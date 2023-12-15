# utils.py

import json
from django.contrib.staticfiles import finders


def id_to_province_name(province_id):

    json_path = finders.find('accounts/argentina/provincias.json')
    if not json_path:
        return None
    
    with open(json_path, 'r', encoding='utf-8') as file:
        provinces_data = json.load(file)['provincias']
        for province in provinces_data:
            if str(province['id']) == str(province_id):
                return province['nombre']  # o 'iso_nombre' si prefieres ese campo
    
    return None