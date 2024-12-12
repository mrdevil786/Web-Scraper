import json
import os
import logging

def load_config(filename='config.json'):
    if not os.path.exists(filename):
        logging.error(f"Configuration file {filename} not found.")
        return {}
    try:
        with open(filename, 'r') as jsonfile:
            return json.load(jsonfile)
    except json.JSONDecodeError as e:
        logging.error(f"Error reading JSON from {filename}: {e}")
        return {}

def save_to_json(data, filename):
    try:
        with open(filename, 'w') as jsonfile:
            json.dump(data, jsonfile)
        logging.info(f"Successfully saved data to {filename}.")
    except IOError as e:
        logging.error(f"Error writing to {filename}: {e}")
