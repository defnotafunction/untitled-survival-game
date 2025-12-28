import pygame
class AnimationRunner:
    def __init__(self, frames: list, frame_switch_interval: float, ping_pong: bool):
        """
        The Animation Runner class - returns what frame to put as your image, used for animations
        :param frames : list - list of image paths
        :param frame_switch_interval : float - amount of time itll take to switch from one frame to another
        :param ping_pong : bool - if False will loop through frames 1 -> 2 -> 3 -> 1 if True will reverse after reaching last frame 1 -> 2 -> 3 -> 2 -> 1
        """
        self.animation_index = 0
        self.frames = frames
        self.frame_switch_interval = frame_switch_interval
        self.start_time = pygame.time.get_ticks() / 1000
        
        self.ping_pong = ping_pong
        self.reverse = False

    def get_next_frame(self):
        if pygame.time.get_ticks()/1000 - self.start_time >= self.frame_switch_interval:
            self.start_time = pygame.time.get_ticks()/1000
            last_frame_index = len(self.frames) - 1

            if self.reverse:
                self.animation_index -= 1
                if self.animation_index <= 0:
                    self.animation_index = 0
                    self.reverse = False
            else:
                self.animation_index += 1
                if self.animation_index > last_frame_index:
                    if self.ping_pong:
                        self.reverse = True
                        self.animation_index = last_frame_index - 1
                    else:
                        self.animation_index = 0

        return self.frames[self.animation_index]
            