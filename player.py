import pygame
import items
import json
import os
from dataclasses import dataclass, asdict, field
from plants import NonFruitingPlant, Seed
import pygame


@dataclass
class PlayerData:
    health: float = 100
    hunger: float = 100
    illnesses: list[str] = field(default_factory=list)
    inventory: dict[str, object] = field(
        default_factory=lambda: {f"item{i}": None for i in range(8)}
        )
    coins: int = 0

    def __post_init__(self):
        self.HEALTH_BAR_PATH = os.path.join('assets', 'images', 'healthbars')

    def get_health_bar_image(self):
        for i in range(10, 0, -1):
            if (i-1)*10 < self.health <= i*10:
                reverse_i = 10 - i
                if reverse_i < 10:
                    return os.path.join(self.HEALTH_BAR_PATH, f'health0{reverse_i}.png')
                return os.path.join(self.HEALTH_BAR_PATH, f'health{reverse_i}.png')


class Player:
    def __init__(self, pos: tuple) -> None:
        self.height = 120
        self.width = 75
        self.rect = pygame.Rect(pos[0], pos[1], self.width, self.height)
        self.hitbox = pygame.Rect(pos[0], self.rect.bottom, self.width, self.height/2)
        self.speed = 2.5
        self.sprint_button = pygame.K_LSHIFT
        self.sprint_multiplier = 1.8
        self.pos = pygame.math.Vector2(pos[0], pos[1])
        self.past_screen_size, self.screen_size = (1200, 700), (1200,700)
        self.INVENTORY_RECT_SIZE = 64
        self.inventory_rects = [
            pygame.Rect(
                (1200 - (8*64 + 7*20)) // 2 + i * (64 + 20),
                700 - 128 - 40,
                self.INVENTORY_RECT_SIZE,
                self.INVENTORY_RECT_SIZE
                ) 
                for i in range(8)]
        self.player_data_path = os.path.join('gamedata', 'playerdata', 'player_data.json')
        self.data = self.get_player_data()

    def get_player_data(self):
        if os.path.exists(self.player_data_path) and os.path.getsize(self.player_data_path) > 0:  # if path exists and actually has content in it
            with open(self.player_data_path, 'r') as ply_data:
                    return PlayerData(**json.load(ply_data))  # function ends here if data successfully retrieved
        
        with open(self.player_data_path, 'w') as ply_data:
            player_data = PlayerData()
            json.dump(asdict(player_data), ply_data, indent=4)

        return player_data
    
    def save_player_data(self):
        with open(self.player_data_path, 'w') as f:
            json.dump(asdict(self.data), f, indent=4)

    def update_inventory(self, screen):  
        # make sure inventory slots positions are proportional to screen size
        for idx, rect in enumerate(self.inventory_rects):
            rect.left = (screen.get_width() - (8*64 + 7*20)) // 2 + idx * (64 + 20)
            rect.top = screen.get_height() - 128 - 40
    
    def get_sprinting(self):
        return pygame.key.get_pressed()[self.sprint_button]

    def draw_inventory(self, screen: pygame.Surface) -> None:
        self.update_inventory(screen)
        for idx, rect in enumerate(self.inventory_rects):
            pygame.draw.rect(screen, 'black', rect)

    def get_if_in_water(self, tile_map) -> bool:
        liquid_tiles = ['W']
        return tile_map.get_tile_at(self.hitbox.center[0], self.hitbox.center[1]) in liquid_tiles
    
    def get_if_in_mud(self, tile_map):
        mud_tile = 'M'
        return tile_map.get_tile_at(self.hitbox.center[0], self.hitbox.center[1]) == mud_tile

    def get_speed_reducer(self, tile_map):
        if self.get_if_in_water(tile_map):
            return 0.3
        elif self.get_if_in_mud(tile_map):
            return 0.6
        
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
        
        if self.get_sprinting():
            velocity *= self.sprint_multiplier

        self.pos += velocity

    def draw_health_bar(self, screen, camera):
        # subtract 20 from x to display hp on player's left
        health_bar_pos = (-7, -57)  
        health_bar_image_path = self.data.get_health_bar_image()
        health_bar_image = pygame.transform.rotate(
            pygame.transform.scale(
                pygame.image.load(health_bar_image_path)
            , (200, 300)
            )
        , 90)

        screen.blit(health_bar_image, health_bar_pos)
    
    def display_data(self):
        pass

    def draw(self, screen: pygame.Surface, camera) -> None:
        screen_pos = (self.rect.x - camera.offset.x,
                      self.rect.y - camera.offset.y)
        pygame.draw.rect(screen, 'black', (*screen_pos, self.rect.w, self.rect.h))
        pygame.draw.rect(screen, 'white', (*(self.hitbox.x - camera.offset.x,
                      self.hitbox.y - camera.offset.y), self.hitbox.w, self.hitbox.h))
        self.draw_health_bar(screen, camera)

    def update(self, tile_map) -> None:
        self.rect.center = self.pos
        self.hitbox.bottomleft = self.rect.bottomleft
        self.move(tile_map)
        self.save_player_data()