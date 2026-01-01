import pygame
from extras import AnimationRunner
from os import path
import json
from random import choice
import ptext
import numpy as np
from plants import screen_to_world

DIALOGUE_PATHS = [
    path.join('gamedata', 'npc-dialogue', 'trading_npc.json')
]

all_dialogue = []

for dialogue_path in DIALOGUE_PATHS:
    with open(dialogue_path) as dialogue:
        all_dialogue.append(json.load(dialogue))

class DialogueBox:
    def __init__(self, text, letter_interval: float):
        self.letter_interval = letter_interval
        self._ticks = pygame.time.get_ticks() / 1000
        self.text = text
        self.text_to_display = ""
        self.current_index = 0

    def get_timer(self):
        return pygame.time.get_ticks() / 1000 - self._ticks >= self.letter_interval

    def update(self):
        if self.get_timer() and self.current_index <= len(self.text) - 1: 
            self.text_to_display += self.text[self.current_index]
            self.current_index += 1
            self._ticks = pygame.time.get_ticks() / 1000
            
    def run(self, pos):
        self.update()
        ptext.draw(
            self.text_to_display,
            pos,
            anchor=(0.5, 1.0)
        )

class BaseEnemy:
    """
    Basic player following and attacking physics
    """
    def __init__(self):
        pass
    
    def go_to_point(self, pos):
        pass

class TradingMenu:
    def __init__(self):
        pass

class BaseNPC:
    def __init__(self, name, pos, image, size, interact_area_radius, bias=0.5):
        self.name = name
        self.image = image
        self.pos = pygame.Vector2(pos)
        self.size = size
        self.rect = pygame.Rect(*pos, *size)
        self.interact_area_radius = interact_area_radius
        self.interact_rect = pygame.Rect(*pos, interact_area_radius, interact_area_radius)
        self.activate_button = pygame.K_x
        self.bias = bias
        self.dialogue_box = DialogueBox("None", None)

    def get_activated(self, player_pos):
        return (self.get_in_interact_area(player_pos) 
                and pygame.key.get_just_pressed()[self.activate_button])

    def get_in_interact_area(self, other_pos):
        return self.interact_rect.collidepoint(other_pos)

    def draw(self, screen, camera):
        screen_pos = (self.rect.x - camera.offset.x,
                      self.rect.y - camera.offset.y)
        rect_to_draw = self.rect.copy()
        rect_to_draw.topleft = screen_pos
        pygame.draw.rect(screen, 'gray', rect_to_draw)


    def update(self):
        self.interact_rect.center = self.pos

class TradingNPC(BaseNPC):
    def __init__(self, name, pos, image, size, interact_area_radius, bias=0.5):
        super().__init__(name, pos, image, size, interact_area_radius, bias)
        self.dialogue_options = [d for d in all_dialogue if d['name'] == 'TRADINGNPC'][0]
        self.accept_button = pygame.K_y
        self.activated = False
        self.current_dialogue = None
        self.clicked_item = None


    def get_dialogue_options(self, bias):
        if bias <= 0.3:
            return self.dialogue_options['unhappy']  # low prices
        elif 0.3 < bias <= 0.6:
            return self.dialogue_options['neutral']  
        else:
            return self.dialogue_options['happy']  # higher prices

    def calculate_plant_price(self, plant_dict):
        total_size = sum(x for x in plant_dict['size']) 
        rarity_factor = plant_dict['rarity_value'] / 4
        return total_size * rarity_factor
    
    def set_up_dialogue_box(self):
        self.dialogue_box.__init__(self.current_dialogue, (1-self.bias)/6)

    def inspect_item(self, item_dict: dict):
        if item_dict:
            if item_dict['type'] == 'Plant':
                self.favored_price = max(1, int(
                    self.calculate_plant_price(item_dict) * self.bias
                    ))
            else:
                if self.current_dialogue is None:
                    self.current_dialogue = choice(self.dialogue_options['denial'])
                    self.set_up_dialogue_box()
                #ptext.draw(self.current_dialogue, (corrected_pos[0], corrected_pos[1]))
                return
        
        dialogue_options = self.get_dialogue_options(self.bias)
        if self.current_dialogue is None:  # dialogue resetting process
            self.current_dialogue = f"{choice(dialogue_options)} ({self.favored_price} {'coin' if self.favored_price == 1 else 'coins'})"
            self.set_up_dialogue_box()
        #ptext.draw(self.current_dialogue, (corrected_pos[0], corrected_pos[1]))
        
    def get_player_clicked_item(self, player):
        for idx, rect in enumerate(player.inventory_rects):
            if rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_just_pressed()[0]:
                return player.data.inventory[f'item{idx}']
    
    def write_text(self, text, pos):
        ptext.draw(text, 
                    pos,
                    anchor=(0.5, 1.0))
        
    def handle_activation(self, player, camera):
        corrected_pos = (self.pos[0] - camera.offset.x, self.pos[1] - camera.offset.y-100)
        if self.activated == False:
            self.clicked_item = None

        if (self.clicked_item != self.get_player_clicked_item(player) 
            and self.get_player_clicked_item(player) is not None):  # if there is a new item clicked
            self.current_dialogue = None  # reset the dialogue
            self.clicked_item = self.get_player_clicked_item(player)  # replace item with new item

        # if player presses activate button again, disable npc
        if self.activated and pygame.key.get_just_pressed()[self.activate_button]:
            self.activated = False
            return
        
        if self.get_activated(player.pos) or self.activated:
            self.activated = True  # once activated, always activated unless changed
            if self.clicked_item:  # if clicked item is not None
                self.inspect_item(self.clicked_item)
            else:    
                self.write_text('Click on an item to trade', corrected_pos)
        
        if not self.get_in_interact_area(player.pos):  # once player leaves interact area
            self.activated = False
            self.inspected_item = False 

        if self.get_in_interact_area(player.pos) and not self.activated:
            self.write_text('X to interact', corrected_pos)
        
        if not self.activated:
            self.current_dialogue = None

    def update(self, player, camera):
        corrected_pos = (self.pos[0] - camera.offset.x, self.pos[1] - camera.offset.y-100)
        if self.current_dialogue:
            self.dialogue_box.run(corrected_pos)
        else:
            self.dialogue_box
        
        self.rect.center = self.pos
        self.interact_rect.center = self.pos
        self.handle_activation(player, camera)
       

class NPCRunner:
    def __init__(self, characters: list[BaseNPC]):
        self.characters = characters
    
    def draw(self, screen, camera):
        for c in self.characters:
            c.draw(screen, camera)
    
    def update(self, player, camera):
        for c in self.characters:
            c.update(player, camera)