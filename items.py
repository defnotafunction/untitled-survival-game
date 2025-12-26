import sqlite3
import os
import json

class PlantDB:    
    def __init__(self):
        self.conn = sqlite3.connect(os.path.join('gamedata', 'plants.db'))
        self.cursor = self.conn.cursor()

        self.cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS items  (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                seed_color TEXT,
                image_file TEXT,
                rarity TEXT
            )
        '''
                            )
    
    def get_all_plants(self) -> list[tuple]:
        return self.cursor.execute('SELECT * FROM items').fetchall()
    
    def get_plant(self, plant_id: int) -> list[tuple]:
        return self.cursor.execute(f'SELECT * FROM ITEMS WHERE id = {plant_id}').fetchone()
    
    def add_new_plants(self, values: list[tuple]) -> None:
        """
        Add new plants into the Plant Database
        values must be (id, name, seed_color, image_file, rarity)
        """
        self.cursor.executemany(f'INSERT INTO items VALUES (?,?,?,?,?)', values)
        self.conn.commit()

    def close(self):
        self.conn.close()
        
def get_tiering_system():
    with open(os.path.join('gamedata', 'tiering_system.json')) as tiering_system:
        return json.load(tiering_system)
    
class BaseWateringTool:
    def __init__(self, power: float, watering_range: int) -> None:
        self.power = power
        self.watering_range = watering_range
        self.placed = False

    def place_tool(self, pos: tuple[int, int]):
        self.pos = pos
        self.placed = True
    
