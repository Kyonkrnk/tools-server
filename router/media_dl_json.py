import os
import json

def load_json(request_id):
    path = os.path.join("media_info", f"{request_id}.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data

def write_json(request_id, write_data: dict):
    path = os.path.join("media_info", f"{request_id}.json")
    data = load_json(request_id)
    for key in write_data.keys():
        data[key] = write_data[key]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)