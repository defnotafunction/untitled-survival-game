import pygame
import random
from os import path
# JuliusH - "Aurora - Ambient Chill Music"
pygame.mixer.init()

class MusicPlayer:
    def __init__(self):
        self.music_list = [
            'aurora-ambient.mp3',
            'morning-mood.mp3'
        ]
        self.music_path = path.join('assets', 'audio', 'music')
        self.song_to_play = None

    def play_random_song(self):
        """
            Plays a random song
        """
        pygame.mixer.music.load(path.join(self.music_path, random.choice(self.music_list)))
        pygame.mixer.music.play()

    def play_song(self, song_title) -> None:
        for song in self.music_list:
            if song_title in song:
                self.song_to_play = song
                
        if self.song_to_play:
            pygame.mixer.music.load(path.join(self.music_path, self.song_to_play))
            pygame.mixer.music.play()

    def run(self):
        if not pygame.mixer.music.get_busy():
                self.play_random_song()