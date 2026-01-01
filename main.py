import pygame
import player
from plants import Seed, BasePlant, PlantRunner, NonFruitingPlant, give_seed
from items import *
from audio import MusicPlayer
from world import TileMap, Camera
from npc import BaseNPC, NPCRunner, TradingNPC
#ALL SPRITES / IMAGES MADE BY NKOLA AIDEN KATAMBWA (ME)

pygame.init()

music_player = MusicPlayer()
clock = pygame.time.Clock()
ply1 = player.Player((650, 1300))
s1 = give_seed(ply1, 1, 7)
tr1 = TradingNPC('Tader', ply1.pos.copy(), None, (100,100), 200, 1)
tr2 = TradingNPC('Radvier', ply1.pos.copy() + (200, 0), None, (100,100), 200, 0.5)
tr3 = TradingNPC('Rake snake', ply1.pos.copy() + (400, 0), None, (100,100), 200, 0.1)

class Game:  # easier to organize
    def __init__(self, *all_sprites, player):
        WIDTH, HEIGHT = 1200, 700
        self.all_sprites = list(all_sprites)
        self.running = True
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.WORLD_SIZE = 1_000_000, 1_000_000
        self.camera = Camera(WIDTH, HEIGHT, self.WORLD_SIZE[0], self.WORLD_SIZE[1])
        self.screen_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        self.player = player

    def load_player_inventory(self):
        for idx, (slot, item) in enumerate(self.player.data.inventory.items()):
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
        
        all_plant_items = [sprite for sprite in self.all_sprites if isinstance(sprite, Seed) or isinstance(sprite, BasePlant)]
        self.plant_runner = PlantRunner(all_plant_items)
        
        all_npc = [sprite for sprite in self.all_sprites if isinstance(sprite, BaseNPC)]
        self.npc_runner = NPCRunner(all_npc)

        self.tile_map = TileMap(self.camera)
        #self.tile_map.drop_player(self.player, self.WORLD_SIZE)

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
            
            # ORDER DICTATES SCREEN PLACEMENT ORDER

            self.screen.fill('white')
            self.tile_map.draw(self.screen, self.camera)
            self.camera.follow(ply1)

            self.npc_runner.draw(self.screen, self.camera)
            self.npc_runner.update(self.player, self.camera)
            
            self.player.draw(self.screen, self.camera)
            self.player.update(self.tile_map)
            self.player.draw_inventory(self.screen)

            self.plant_runner.draw(self.screen, self.camera)
            self.plant_runner.update(self.camera, self.tile_map)
            
            music_player.run()
           
            pygame.display.update()

            clock.tick(60)

game = Game(tr1, tr2, tr3, player=ply1)
game.set_up()
game.main() 