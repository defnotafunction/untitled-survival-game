import pygame
import ptext
import random
import os
import numpy as np
from items import get_tiering_system, PlantDB

def screen_to_world(pos, camera):
    return (pos[0] + camera.offset.x,
            pos[1] + camera.offset.y)

plant_database = PlantDB()
#plant_database.add_new_plants([(1, 'Carrot', 'orange', 'carrot.png', 'plain')])
print(plant_database.get_all_plants())
plant_database.close()

class Seed:
    def __init__(self, name: str, player, inventory_slot: int, color: str, plant_state = None):
        self.name = name
        self.inventory_slot = inventory_slot  # slot numbered from 0-7
        self.color = color
        self.player = player
        self._click_state = False
        self.inventory_rect_pos = self.player.inventory_rects[inventory_slot].center
        self.rect = pygame.Rect(self.inventory_rect_pos[0], self.inventory_rect_pos[1], 20, 20)
        self.placed = False
        self.dragged = False  
        self.just_dragged = False

        if plant_state:
            self.plant_state = plant_state  # once seed is planted it'll go into plant state
        else:
            self.plant_state = BasePlant(name=self.name[:-5], pos=(0,0), color=self.color,
                                     size=(10,10), growing_time=0, growing_increments=(3,3),
                                     player=player)
        
        player.data.inventory[f'item{inventory_slot}'] = self.get_dict()  # import itself to player inventory data    
    
    def get_mouse_hover(self):
        return self.player.inventory_rects[self.inventory_slot].collidepoint(pygame.mouse.get_pos()) # in inventory slot it doesn't move so doesn't need camera adjustments
    
    def get_dict(self):
        return {
            'name': self.name,
            'type': 'Seed',
            'color': self.color,
            'id': self.plant_state.id
        }

    def just_clicked(self):
        pressed = pygame.mouse.get_pressed()[0]

        if pressed and not self._click_state:
            self._click_state = True
            return True  # only True on the first frame of click
        if not pressed:
            self._click_state = False
        return False
    
    def display_info(self):
        info_to_display = f'''{self.name.upper()}'''
        ptext.draw(
            info_to_display,
            pos=(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]-20),
            fontsize=20,
            width=200,
            background='black',
            fontname=os.path.join('assets', 'fonts', 'WorkSans-Regular.ttf'),
            color=self.color
        )

    def get_clicked_on(self) -> bool:  # seed version will not need to use screen -> world because it detects dragging from STATIONARY slot
        return self.rect.collidepoint(pygame.mouse.get_pos()) and self.just_clicked()
    
    def get_dragged(self) -> bool:
        return self.dragged and pygame.mouse.get_pressed()[0]
    
    def get_can_be_placed(self, tile_map, camera):
        if self.get_dragged() or not self.just_dragged:
            return False
        # make sure seed is not in inventory area
        if any(self.rect.colliderect(r) for r in self.player.inventory_rects):
            return False
        
        world_pos = screen_to_world(self.rect.center, camera)
        if tile_map.get_tile_at(world_pos[0], world_pos[1]) == 'S':
            return True

        return False
    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

    def update(self, tile_map, camera):
        if self.just_dragged and not self.dragged:
            self.just_dragged = False
        # follow cursor as long as player clicked on you and hasn't released since
        if self.get_clicked_on():
            self.dragged = True
            self.just_dragged = True
            
        elif not pygame.mouse.get_pressed()[0]:
            self.dragged = False

        # display info if player is hovering cursor
        if self.get_mouse_hover():
            self.display_info()
        # dragging mechanics, be placed else stay in slot
        if self.get_dragged():
            self.rect.center = pygame.mouse.get_pos()
        elif self.get_can_be_placed(tile_map, camera):
            self.player.data.inventory[f'item{self.inventory_slot}'] = None
            self.placed = True

        if not self.dragged and not self.placed:
            slot_center = self.player.inventory_rects[self.inventory_slot].center
            self.rect.center = slot_center

class BasePlant: 
    def __init__(self, name: str, pos: tuple[int, int], color: str, size: tuple[int,int], 
                 growing_time: float, growing_increments: tuple[float, float], player, 
                 max_size: tuple[int, int] = None, rarity: str = 'ordinary'):
        self.name = name
        self.rect = pygame.Rect(pos[0], pos[1], size[0], size[1])
        self.pos = pos
        self.color = color
        self.player = player
        self.rarity = rarity
        self.rarity_value = self.get_random_rarity_num()
        self.size = np.array(size, dtype=float)
        self.growing_time = self.get_growing_time()  # how much time passes before it grows
        self.growing_increments = growing_increments  # how much it'll grow by
        self.growing_clock = pygame.time.get_ticks() / 1000  # keeps track of time
        self.max_size = self.get_max_size()
        self.picked_up = False 
        self.inventory_rect = None
        self.times_grown = -1

    def get_max_size(self):
        minimum_value = self.rarity_value * 1.2
        rarity_weight = self.rarity_value/5
        original_max_size_weight = random.uniform(1, random.uniform(2, 5))
        return self.size * max(minimum_value,  original_max_size_weight * rarity_weight)

    def get_growing_time(self):
        added_rarity_weight = self.rarity_value / 5
        original_growing_time = random.uniform(0.5, random.uniform(1, 5))
        return original_growing_time * added_rarity_weight

    def get_mouse_hover(self, camera):
        return self.rect.collidepoint(screen_to_world(pygame.mouse.get_pos(), camera)) if not self.picked_up else self.inventory_rect.collidepoint(pygame.mouse.get_pos())
    
    def get_random_rarity_num(self):
        start = None
        for rarity, val in get_tiering_system().items():
            if start is not None:
                stop = val
                break
            if rarity == self.rarity:
                start = val
        return random.uniform(start, stop) if self.rarity != 'intangible' else random.uniform(95, 100)
    
    def get_growing_time_passed(self) -> None:
        return self.growing_time <= pygame.time.get_ticks()/1000 - self.growing_clock
    
    def get_clicked_on(self, camera):
        return self.rect.collidepoint(screen_to_world(pygame.mouse.get_pos(), camera)) and pygame.mouse.get_pressed()[0]
    
    def grow(self) -> None:
        if self.get_growing_time_passed() and not isinstance(self.growing_increments, int):
            self.growing_clock = pygame.time.get_ticks()/1000  # resets clock
            if self.times_grown >= 1:
                self.size[0] = self.size[0] + self.growing_increments[0] if self.size[0] < self.max_size[0] else self.size[0]
                self.size[1] = self.size[1] + self.growing_increments[1] if self.size[1] < self.max_size[1] else self.size[1]
            self.times_grown += 1
            print(self.name)
            print(self.times_grown)
            print(self.rarity_value)
            print(self.times_grown/(self.rarity_value*5))
            print('*********************')
        if (np.sum(self.size) + np.sum(self.growing_increments)) > np.sum(self.max_size): # do not grow if you'll go over the max size
            self.growing_increments = 0

    def just_clicked(self):
        pressed = pygame.mouse.get_pressed()[0]

        if pressed and not self._click_state:
            self._click_state = True
            return True  # only True on the first frame of click
        if not pressed:
            self._click_state = False
        return False
    
    def calculate_price(self) -> int:
        return max(1, np.sum(self.size)) * (self.rarity_value/4)
    
    def get_ready_for_picking(self):
        return (self.times_grown / (self.rarity_value*5)) >= 1 or self.growing_increments == 0

    def handle_pick_up(self, camera) -> None:
        if (self.just_clicked() and self.get_clicked_on(camera) 
            and not self.picked_up and self.get_ready_for_picking()): 
            for inventory_slot, value in self.player.inventory.items():
                if value is None:  # if slot is empty / is holding no value
                    self.player.inventory[inventory_slot] = self
                    self.inventory_rect = self.player.inventory_rects[int(inventory_slot[-1])]
                    self.rect.center = self.player.inventory_rects[int(inventory_slot[-1])].center
                    self.picked_up = True
                    return
                
    def display_info(self):
        if self.picked_up:
            info_to_display = f'''
                            {self.name.upper()}
                                Size - {round(np.sum(self.size)//1.2)} cm²
                                Price - {self.calculate_price():.0f} {'coins' if self.calculate_price() > 1 else 'coin'}
                            '''
            display_pos = (pygame.mouse.get_pos()[0]-50, pygame.mouse.get_pos()[1]-100)
        else:
            info_to_display = f'''
                            {self.name.upper()}
                                Size - {round(np.sum(self.size)/1.2)} cm²
                                Growing Rate - {(np.sum(self.growing_increments)/1.2)/self.growing_time:.2f}cm/s
                                Status - {'Ready for picking!' if self.get_ready_for_picking() else 'Needs more time'}
                            '''
            display_pos = pygame.mouse.get_pos()
        ptext.draw(
            info_to_display,
            pos=display_pos,
            fontsize=20,
            width=200,
            background='black',
            fontname=os.path.join('assets', 'fonts', 'WorkSans-Regular.ttf'),
            color=self.color
        )
        
    def draw(self, screen, camera) -> None:
        if not self.picked_up:  # if not in stationary inventory slot
            screen_pos = (self.rect.x - camera.offset.x,
                          self.rect.y - camera.offset.y)
            pygame.draw.rect(screen, self.color,
                            (*screen_pos, self.rect.w, self.rect.h))
        else:
            rect_x = self.inventory_rect.x + (self.inventory_rect.w - self.rect.w) // 2
            rect_y = self.inventory_rect.y + (self.inventory_rect.h - self.rect.h) // 2
            pygame.draw.rect(screen, self.color, (rect_x, rect_y, self.rect.w, self.rect.h))
            
        if self.get_mouse_hover(camera):
            self.display_info()

    def update(self, camera) -> None:
        if not self.picked_up: 
            self.grow()
            center = self.rect.center
            self.rect.size = self.size[0], self.size[1]
            self.rect.center = center
        else:
            self.inventory_rect_pos = self.inventory_rect.center
            self.rect.center = self.inventory_rect_pos
        
        self.handle_pick_up(camera)

class NonFruitingPlant(BasePlant):
    def __init__(self, id, player, max_size = None):
        self.id = id
        plant_database = PlantDB()
        self.plant_data = plant_database.get_plant(self.id)
        plant_database.close()
        self.image = pygame.transform.scale(pygame.image.load(os.path.join('assets', 'images', 'plants', self.plant_data[3])), (10,10))
        super().__init__(self.plant_data[1], (0,0), self.plant_data[2], (16,16), 0, (1,1), player, max_size, self.plant_data[-1])
    

    def draw_plant_seed(self, screen, camera):
        screen_pos = (self.rect.x - camera.offset.x,
                        self.rect.y - camera.offset.y)
        pygame.draw.rect(screen, self.color,
                        (*screen_pos, self.rect.w, self.rect.h))

    def draw(self, screen, camera) -> None:
        if not self.picked_up and self.times_grown > 1:  # if not in stationary inventory slot
            screen_pos = (self.rect.x - camera.offset.x,
                          self.rect.y - camera.offset.y)
            screen.blit(self.image, screen_pos)
        elif self.picked_up:
            img_rect = self.image.get_rect(center=self.inventory_rect.center)
            screen.blit(self.image, img_rect)
        elif self.times_grown <= 1:
            self.draw_plant_seed(screen, camera) 

        if self.get_mouse_hover(camera):
            self.display_info()    

    def handle_pick_up(self, camera) -> None:
        if self.just_clicked() and self.get_clicked_on(camera) and not self.picked_up and self.get_ready_for_picking(): 
            for inventory_slot, value in self.player.data.inventory.items():
                if value is None:  # if slot is empty / is holding no value
                    self.player.data.inventory[inventory_slot] = self.get_dict_picked_up()
                    self.inventory_rect = self.player.inventory_rects[int(inventory_slot[-1])]
                    self.rect.center = self.player.inventory_rects[int(inventory_slot[-1])].center
                    self.picked_up = True
                    return
                
    def get_dict_picked_up(self):
        #all important stats
        return {
            'id': self.id,
            'size': list(self.size),
            'rarity_value': self.rarity_value,
            'type': 'Plant'
        }

    def update(self, camera):
        self.image = pygame.transform.scale(pygame.image.load(os.path.join('assets', 'images', 'plants', self.plant_data[3])), self.size)
        return super().update(camera)
    
class PlantRunner:
    def __init__(self, seeds_and_plants: list) -> None:
        self.all_seeds_and_plants = seeds_and_plants
        self.dragged_seed = None

    def draw(self, screen, camera) -> None:
        for obj in self.all_seeds_and_plants:
            if isinstance(obj, BasePlant):
                obj.draw(screen, camera)
            else:
                obj.draw(screen)
    
    def update(self, camera, tile_map) -> None:
        for obj in self.all_seeds_and_plants:
            if isinstance(obj, Seed):
                obj.update(tile_map, camera)
                if obj.placed:
                    new_pos = (pygame.mouse.get_pos()[0] + camera.offset.x,
                               pygame.mouse.get_pos()[1] + camera.offset.y)
                    obj.plant_state.rect.center = new_pos
                    self.all_seeds_and_plants.append(obj.plant_state)
                    self.all_seeds_and_plants.remove(obj)
                    break
                # ensures there can only be one dragged seed at a time
                if obj.dragged and (obj == self.dragged_seed or not self.dragged_seed): # can only be dragged seed if variable is available
                    self.dragged_seed = obj
                else:
                    self.dragged_seed = None
                obj.dragged = self.dragged_seed == obj

            else:
                obj.update(camera)

def give_seed(player, plant_id, slot=None):
    # find empty slot if none provided
    if slot is None:
        for i in range(8):
            if player.data.inventory[f'item{i}'] is None:
                slot = i
                break
        else:
            return None  # inventory full

    plant = NonFruitingPlant(plant_id, player)

    seed = Seed(
        name=f"{plant.name} Seed",
        player=player,
        inventory_slot=slot,
        color=plant.color,
        plant_state=plant
    )

    player.data.inventory[f'item{slot}'] = seed.get_dict()
    return seed
 