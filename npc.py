import pygame
from extras import AnimationRunner

class BaseEnemy:
    """
    Basic player following and attacking physics
    """
    def __init__(self):
        pass
    
    
    def go_to_point(self, player):
        pass

class BaseNPC:
    def __init__(self, pos, image):
        self.image = image
        self.pos = pos