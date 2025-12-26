import pygame
import items
import json
import os

class Player:
    def __init__(self, pos: tuple) -> None:
        self.height = 120
        self.width = 75
        self.rect = pygame.Rect(pos[0], pos[1], self.width, self.height)
        self.hitbox = pygame.Rect(pos[0], self.rect.bottom, self.width, self.height/2)
        self.speed = 4.5
        self.pos = pygame.math.Vector2(pos[0], pos[1])
        self.inventory = {f'item{i}': None for i in range(8)}
        self.past_screen_size, self.screen_size = (1200, 700), (1200,700)
        self.inventory_rects = [
            pygame.Rect(
                (1200 - (8*64 + 7*20)) // 2 + i * (64 + 20),
                700 - 128 - 40,
                64,
                64
                ) 
                for i in range(8)]
        self.player_data_path = os.path.join('gamedata', 'playerdata', 'player_data.json')
        self.player_data = self.get_player_data()

    def get_player_data(self):
        if os.path.exists(self.player_data_path) and os.path.getsize(self.player_data_path) > 0:  # if path exists and actually has content in it
            with open(self.player_data_path, 'r') as ply_data:
                    return json.load(ply_data)  # function ends here if data successfully retrieved
        
        with open(self.player_data_path, 'w') as ply_data:
            player_data = { # create new data
                'coins': 0,
                'inventory': {f'item{i}': None for i in range(8)}
                          }
            json.dump(player_data, ply_data, indent=4)
            return player_data
        
    def save_player_data(self):
        with open(self.player_data_path, 'w') as f:
            json.dump(self.player_data, f, indent=4)

    def update_inventory(self, screen):  # make sure inventory slots positions are proportional to screen size
        for idx, rect in enumerate(self.inventory_rects):
            rect.left = (screen.get_width() - (8*64 + 7*20)) // 2 + idx * (64 + 20)
            rect.top = screen.get_height() - 128 - 40

    def draw_inventory(self, screen: pygame.Surface) -> None:
        self.update_inventory(screen)
        for idx, rect in enumerate(self.inventory_rects):
            pygame.draw.rect(screen, 'black', rect)

    def get_if_in_water(self, tile_map) -> bool:
        liquid_tiles = ['W', 'SW']
        return tile_map.get_tile_at(self.hitbox.center[0], self.hitbox.center[1]) in liquid_tiles
    
    def get_speed_reducer(self, tile_map):
        if self.get_if_in_water(tile_map):
            return 0.3
        return 1

    def move(self, tile_map) -> None:
        keys = pygame.key.get_pressed()
        velocity = pygame.Vector2(0,0)
        speed_reducer = self.get_speed_reducer(tile_map)
        # moving system
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            velocity.x += -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            velocity.x += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            velocity.y += -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            velocity.y += 1

        if velocity.length() > 0:
            velocity = velocity.normalize() * self.speed * speed_reducer
        self.pos += velocity

    def draw(self, screen: pygame.Surface, camera) -> None:
        screen_pos = (self.rect.x - camera.offset.x,
                      self.rect.y - camera.offset.y)
        pygame.draw.rect(screen, 'black', (*screen_pos, self.rect.w, self.rect.h))
        pygame.draw.rect(screen, 'white', (*(self.hitbox.x - camera.offset.x,
                      self.hitbox.y - camera.offset.y), self.hitbox.w, self.hitbox.h))
    def update(self, tile_map) -> None:
        self.rect.center = self.pos
        self.hitbox.bottomleft = self.rect.bottomleft
        self.move(tile_map)
        self.save_player_data()