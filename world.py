import pygame
import os
import random
import json

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

class TileMap:
    CHUNK_WIDTH = 30
    CHUNK_HEIGHT = 20
    TILE_SIZE = 100

    def __init__(self, camera: Camera, seed=None):
        self.WORLD_DATA_PATH = os.path.join('gamedata', 'world_data.json')
        self.camera = camera
        self.loaded_chunks = {}
        self.color_key = {
            'W': pygame.Color("#67c0d6"),  # WATER
            'SW': pygame.Color("#3e4431"), #SWAMP WATER
            'DG': pygame.Color('#013b01'),  # DARK GRASS
            'LG': pygame.Color('#2aaa3b'),  # LIGHT GRASS
            'S': pygame.Color('#96702b')  # SOIL
        }
        self.seed = self.get_world_rng(seed)

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
        likiness = 1
        
        for neighbor in neighbors:
            if neighbor in terrain_key[terrain_wanted]:
                likiness += 1

        return likiness * self.seed.random()
    
    def blend_map(self, tile_map: list[list]) -> list[list]:
        new_tile_map = tile_map[:]
        for row_index, row in enumerate(new_tile_map):
            for col_index, col in enumerate(row):
                col_neighbors = self.get_tile_neighbors(new_tile_map, row_index, col_index)
                if col not in col_neighbors: #  if tile is different from neighbors
                    new_tile_map[row_index][col_index] = random.choice(col_neighbors)

        return new_tile_map

    def get_world_rng(self, chosen_seed):
        if chosen_seed:
            return random.Random(chosen_seed)
        else:
            seed = random.randint(0, 4_294_967_295) #seed range, over 4 billion seeds, 32-bit range
            return random.Random(seed)

    def save_world_data(self) -> None:
        with open(self.WORLD_DATA_PATH, 'w') as world_f:
            pass

    def drop_player(self, player):
        selected_position = None

    def generate_chunk(self, chunk_x, chunk_y):
        print('GENERATING NEW CHUNK')
        tile_chunk = [[None for _ in range(self.CHUNK_WIDTH)]
                    for _ in range(self.CHUNK_HEIGHT)]

        base_terrain_chances = {
            'W': self.seed.uniform(0.2, 0.5),
            'SW': self.seed.uniform(0.1, 0.3),
            'LG': self.seed.uniform(1, 1.5),
            'DG': self.seed.uniform(0.4, 0.8),
            'S': self.seed.uniform(0.05, 0.1)
        }

        connect_terrain_chances = {
            'W': 0.9,
            'SW': 0.3,
            'LG': 1.5,
            'DG': 0.8,
            'S': 0.2
        }


        for row_index, row in enumerate(tile_chunk):
            for col_index, col in enumerate(row):
                tile_neighbors = self.get_tile_neighbors(tile_chunk, row_index, col_index)
                random_chance = self.seed.random()
                for neighbor in tile_neighbors:

                    if neighbor is None:
                        continue

                    likiness = self.get_terrain_likiness(neighbor, tile_neighbors)
                    if connect_terrain_chances[neighbor] >= random_chance and likiness >= 1:
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
