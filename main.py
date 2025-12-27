import pygame
import player
from plants import Seed, BasePlant, PlantRunner, NonFruitingPlant, give_seed
from items import *
from audio import MusicPlayer
import random
import os
#ALL SPRITES / IMAGES MADE BY NKOLA AIDEN KATAMBWA (ME)

pygame.init()

music_player = MusicPlayer()
clock = pygame.time.Clock()
ply1 = player.Player((650, 1300))

class TileMap:
    CHUNK_WIDTH = 30
    CHUNK_HEIGHT = 20
    TILE_SIZE = 100


    def __init__(self, camera):
        self.tile_map_path = os.path.join('gamedata', 'tilemap.txt')
        self.camera = camera
        self.loaded_chunks = {}
        self.color_key = {
            'W': pygame.Color("#67c0d6"),  # WATER
            'SW': pygame.Color("#3e4431"), #SWAMP WATER
            'DG': pygame.Color('#013b01'),  # DARK GRASS
            'LG': pygame.Color('#2aaa3b'),  # LIGHT GRASS
            'S': pygame.Color('#96702b')  # SOIL
        }
        if os.path.exists(self.tile_map_path):
            with open(self.tile_map_path, 'r') as f:
                self.tile_map = f.read().split()
            self.tile_rects = []
        else:
            pass

    def get_tile_neighbors(self, tile_map: list[list], row_index: int, col_index: int) -> list:
        neighbors = []
        rows = len(tile_map)
        cols = len(tile_map[0])

        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            r, c = row_index + dr, col_index + dc
            if 0 <= r < rows and 0 <= c < cols:
                neighbors.append(tile_map[r][c])
        return neighbors
    
    def get_chunk_coords(self, world_x, world_y):
        return world_x // (self.CHUNK_WIDTH * self.TILE_SIZE), world_y // (self.CHUNK_HEIGHT * self.TILE_SIZE)

    def get_terrain_likiness(self, terrain_wanted, neighbors) -> float:
        terrain_key = {
            'W': ['LG', 'S'],
            'SW': ['DG'],
            'LG': ['W', 'S'],
            'DG': ['SW'],
            'S': ['LG', 'W']
        }
        likiness = 0
        
        for neighbor in neighbors:
            if neighbor in terrain_key[terrain_wanted]:
                likiness += 1

        return likiness / 4
    
    def blend_map(self, tile_map: list[list]) -> list[list]:
        new_tile_map = tile_map[:]
        for row_index, row in enumerate(new_tile_map):
            for col_index, col in enumerate(row):
                col_neighbors = self.get_tile_neighbors(new_tile_map, row_index, col_index)
                if col not in col_neighbors: #  if tile is different from neighbors
                    new_tile_map[row_index][col_index] = random.choice(col_neighbors)

        return new_tile_map

    def get_rects_to_draw(self) -> None:
        pass

    def generate_chunk(self, chunk_x, chunk_y):
        print('GENERATING NEW CHUNK')
        tile_chunk = [[None for _ in range(self.CHUNK_WIDTH)]
                    for _ in range(self.CHUNK_HEIGHT)]

        base_terrain_chances = {
            'W': 0.4,
            'SW': 0.2,
            'LG': 1,
            'DG': 0.4,
            'S': 0.1
        }

        connect_terrain_chances = {
            'W': 1,
            'SW': 0.3,
            'LG': 1,
            'DG': 0.8,
            'S': 0.2
        }

        random.seed(chunk_x * 100000 + chunk_y)

        for row_index, row in enumerate(tile_chunk):
            for col_index, col in enumerate(row):
                tile_neighbors = self.get_tile_neighbors(tile_chunk, row_index, col_index)
                random_chance = random.random()
                for neighbor in tile_neighbors:

                    if neighbor is None:
                        continue

                    likiness = self.get_terrain_likiness(neighbor, tile_neighbors)
                    if connect_terrain_chances[neighbor] >= random_chance and likiness >= 0.7:
                        tile_chunk[row_index][col_index] = neighbor
                        break

                for tile_type, chance in sorted(base_terrain_chances.items(), key=lambda x: x[1]):
                    
                    if chance >= random_chance:
                        tile_chunk[row_index][col_index] = tile_type
                        break

        tile_chunk = self.blend_map(tile_chunk)

        self.loaded_chunks[(chunk_x, chunk_y)] = tile_chunk
            
        return tile_chunk


    def get_tile_at(self, world_x, world_y):
        chunk_x = world_x // (self.CHUNK_WIDTH * self.TILE_SIZE)
        chunk_y = world_y // (self.CHUNK_HEIGHT * self.TILE_SIZE)
        local_x = (world_x % (self.CHUNK_WIDTH * self.TILE_SIZE)) // self.TILE_SIZE
        local_y = (world_y % (self.CHUNK_HEIGHT * self.TILE_SIZE)) // self.TILE_SIZE

        if (chunk_x, chunk_y) not in self.loaded_chunks:
            self.generate_chunk(chunk_x, chunk_y)

        tile_key = self.loaded_chunks[(chunk_x, chunk_y)][int(local_y)][int(local_x)]
        return tile_key
    
    def draw(self, screen, camera):
        start_chunk_x = int(camera.offset.x // (self.CHUNK_WIDTH * self.TILE_SIZE))
        start_chunk_y = int(camera.offset.y // (self.CHUNK_HEIGHT * self.TILE_SIZE))
        end_chunk_x = int((camera.offset.x + camera.w) // (self.CHUNK_WIDTH * self.TILE_SIZE)) + 1
        end_chunk_y = int((camera.offset.y + camera.h) // (self.CHUNK_HEIGHT * self.TILE_SIZE)) + 1

        for chunk_x in range(start_chunk_x, end_chunk_x):
            for chunk_y in range(start_chunk_y, end_chunk_y):
                if (chunk_x, chunk_y) not in self.loaded_chunks:
                    self.generate_chunk(chunk_x, chunk_y)
                chunk = self.loaded_chunks[(chunk_x, chunk_y)]

                for row_idx, row in enumerate(chunk):
                    for col_idx, tile in enumerate(row):
                        
                        tile_rect = pygame.Rect(
                            chunk_x * self.CHUNK_WIDTH * self.TILE_SIZE + col_idx * self.TILE_SIZE - camera.offset.x,
                            chunk_y * self.CHUNK_HEIGHT * self.TILE_SIZE + row_idx * self.TILE_SIZE - camera.offset.y,
                            self.TILE_SIZE,
                            self.TILE_SIZE
                        )
                        pygame.draw.rect(screen, self.color_key[tile], tile_rect)


class Camera:
    def __init__(self, w, h, world_w, world_h):
        self.offset = pygame.Vector2()
        self.w = w
        self.h = h
        self.world_w = world_w
        self.world_h = world_h

    def follow(self, target) -> None:
        # center camera on player
        self.offset.x = target.rect.centerx - self.w // 2
        self.offset.y = target.rect.centery - self.h // 2
        # clamp so camera doesn’t go outside world
        self.offset.x = max(0, min(self.offset.x, self.world_w - self.w))
        self.offset.y = max(0, min(self.offset.y, self.world_h - self.h))


class Game:  # easier to organize
    def __init__(self, *all_sprites):
        WIDTH, HEIGHT = 1200, 700
        self.all_sprites = list(all_sprites)
        self.running = True
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.WORLD_SIZE = 100000, 100000
        self.camera = Camera(WIDTH, HEIGHT, self.WORLD_SIZE[0], self.WORLD_SIZE[1])
        self.screen_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        

    def load_player_inventory(self):
        for idx, (slot, item) in enumerate(ply1.data.inventory.items()):
            if item:
                if item['type'] == 'Seed':
                    self.all_sprites.append(Seed(name=item['name'],
                                                 player=ply1,
                                                 inventory_slot=idx,
                                                 color=item['color'],
                                                 plant_state=NonFruitingPlant(item['id'], ply1)))
                
                if item['type'] == 'Plant':
                    plant_to_implement = NonFruitingPlant(item['id'], ply1)
                    plant_to_implement.inventory_rect = ply1.inventory_rects[idx]
                    plant_to_implement.rect.center = ply1.inventory_rects[idx].center
                    plant_to_implement.picked_up = True
                    plant_to_implement.size = item['size']
                    plant_to_implement.rarity_value = item['rarity_value']
                    self.all_sprites.append(plant_to_implement)

    def set_up(self) -> None:
        self.load_player_inventory()
        all_plant_items = [sprite for sprite in self.all_sprites if isinstance(sprite, Seed) or isinstance(sprite, BasePlant)] # all base plants are children of the seed class
        self.plant_runner = PlantRunner(all_plant_items)
        self.tile_map = TileMap(self.camera)


    def main(self) -> None:
        pygame.display.set_caption('Grow a Garden')
        music_player.play_song('morning')
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.VIDEORESIZE:
                    # update screen and camera sizes
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.camera.w = event.w
                    self.camera.h = event.h
            
            self.screen.fill('white')
            self.tile_map.draw(self.screen, self.camera)
            self.camera.follow(ply1)

            ply1.draw(self.screen, self.camera)
            ply1.update(self.tile_map)
            ply1.draw_inventory(self.screen)

            self.plant_runner.draw(self.screen, self.camera)
            self.plant_runner.update(self.camera, self.tile_map)

            music_player.run()
           
            pygame.display.update()

            clock.tick(60)

game = Game(ply1)
game.set_up()
game.main() 