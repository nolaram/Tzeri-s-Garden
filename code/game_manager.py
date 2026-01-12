import json
import os
from settings import *

SAVE_PATH = 'saves/'

class SaveManager:
    @staticmethod
    def ensure_folder():
        if not os.path.exists(SAVE_PATH):
            os.makedirs(SAVE_PATH)

    @staticmethod
    def get_save_files():
        SaveManager.ensure_folder()
        return [f.replace('.json', '') for f in os.listdir(SAVE_PATH) if f.endswith('.json')]

    @staticmethod
    def save(slot_name, data):
        SaveManager.ensure_folder()
        with open(f'{SAVE_PATH}{slot_name}.json', 'w') as f:
            json.dump(data, f, indent=4)

    @staticmethod
    def load(slot_name):
        try:
            with open(f'{SAVE_PATH}{slot_name}.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {slot_name}: {e}")
            return None