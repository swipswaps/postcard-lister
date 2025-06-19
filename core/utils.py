import os
import re
import json
from pathlib import Path

def is_image_file(filename: str) -> bool:
    return filename.lower().endswith((".jpg", ".jpeg", ".png"))

def get_image_pairs(folder: str) -> list[tuple[str, str]]:
    # Get only raw JPGs that are not AI-generated output
    files = [f for f in os.listdir(folder)
             if f.lower().endswith(".jpg")
             and not f.startswith("vision_")
             and not f.startswith("final_")]

    files.sort()  # Make sure A, B, A, B order stays consistent
    pairs = []

    # Pair images in order: (0,1), (2,3), etc.
    for i in range(0, len(files), 2):
        front = os.path.join(folder, files[i])
        back = os.path.join(folder, files[i + 1]) if i + 1 < len(files) else None
        if back:
            pairs.append((front, back))

    return pairs

def load_settings(settings_path: str) -> dict:
    if Path(settings_path).exists():
        with open(settings_path, 'r') as f:
            return json.load(f)
    else:
        return {}

def save_settings(settings_path: str, data: dict):
    with open(settings_path, 'w') as f:
        json.dump(data, f, indent=4)

def has_been_processed(output_folder: str, label: str) -> bool:
    return Path(os.path.join(output_folder, f"{label}.csv")).exists()