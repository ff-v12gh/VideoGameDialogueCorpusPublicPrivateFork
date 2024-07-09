import json
import matplotlib.pyplot as plt
from collections import defaultdict
from textwrap import wrap
import os
import sys

# Get the directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Change the working directory to the script directory
os.chdir(script_dir)
# Add the parent directory to sys.path
sys.path.append(os.path.dirname(script_dir))

def load_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        print(f"Current working directory: {os.getcwd()}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file: {file_path}")
        sys.exit(1)

def normalize_character_name(name, aliases):
    for main_name, alias_list in aliases.items():
        if isinstance(alias_list, list) and name in alias_list:
            return main_name
        elif isinstance(alias_list, dict):
            for sub_name, sub_alias_list in alias_list.items():
                if name in sub_alias_list:
                    return sub_name
    return name

def analyze_story_structure(data, aliases):
    scenes = []
    current_scene = {"location": "", "characters": set(), "content": [], "summary": ""}
    
    for item in data['text']:
        if 'LOCATION' in item:
            if current_scene['content']:
                current_scene['summary'] = summarize_scene(current_scene)
                scenes.append(current_scene)
            current_scene = {"location": item['LOCATION'], "characters": set(), "content": [item], "summary": ""}
        else:
            current_scene['content'].append(item)
            if any(char in item for char in item.keys() if char not in ['ACTION', 'COMMENT']):
                character = list(item.keys())[0]
                normalized_character = normalize_character_name(character, aliases)
                current_scene['characters'].add(normalized_character)

    if current_scene['content']:
        current_scene['summary'] = summarize_scene(current_scene)
        scenes.append(current_scene)

    return scenes

def analyze_character_constellations(data, aliases, inactivity_threshold=50):
    scenes = []
    current_scene = {"characters": set(), "content": [], "summary": ""}
    character_last_seen = defaultdict(int)
    dialogue_count = 0

    for item in data['text']:
        current_scene['content'].append(item)
        if any(char in item for char in item.keys() if char not in ['ACTION', 'COMMENT', 'LOCATION']):
            character = list(item.keys())[0]
            normalized_character = normalize_character_name(character, aliases)
            current_scene['characters'].add(normalized_character)
            character_last_seen[normalized_character] = dialogue_count

            # Check for inactive characters
            inactive_characters = {char for char, last_seen in character_last_seen.items() 
                                   if dialogue_count - last_seen > inactivity_threshold}
            current_scene['characters'] -= inactive_characters

            # Start a new scene if character constellation changes significantly
            if len(current_scene['characters']) > 3 and len(inactive_characters) > 1:
                current_scene['summary'] = summarize_scene(current_scene)
                scenes.append(current_scene)
                current_scene = {"characters": set([normalized_character]), "content": [item], "summary": ""}

            dialogue_count += 1

    if current_scene['content']:
        current_scene['summary'] = summarize_scene(current_scene)
        scenes.append(current_scene)

    return scenes

def summarize_scene(scene):
    characters = ", ".join(scene['characters'])
    content = scene['content']
    first_dialogue = next((item for item in content if any(char in item for char in item.keys() if char not in ['ACTION', 'COMMENT', 'LOCATION'])), None)
    last_dialogue = next((item for item in reversed(content) if any(char in item for char in item.keys() if char not in ['ACTION', 'COMMENT', 'LOCATION'])), None)
    
    summary = f"Characters: {characters}. "
    if 'location' in scene:
        summary += f"Location: {scene['location']}. "
    if first_dialogue:
        summary += f"Starts with: {list(first_dialogue.values())[0]}... "
    if last_dialogue:
        summary += f"Ends with: {list(last_dialogue.values())[0]}"
    return summary

def save_results(scenes, file_name):
    def set_default(obj):
        if isinstance(obj, set):
            return list(obj)
        raise TypeError

    with open(file_name, 'w') as file:
        json.dump(scenes, file, indent=2, default=set_default)

def plot_scene_structure(scenes, title, output_file):
    fig, ax = plt.subplots(figsize=(20, len(scenes) * 0.5))  # Adjust figure height based on number of scenes
    
    y_positions = range(len(scenes))
    labels = [f"Scene {i+1}" for i in range(len(scenes))]
    
    ax.barh(y_positions, [len(scene['content']) for scene in scenes])
    ax.set_yticks(y_positions)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel('Number of Dialogue Lines')
    ax.set_title(title)
    
    for i, scene in enumerate(scenes):
        summary = '\n'.join(wrap(scene['summary'], 60))
        ax.text(len(scene['content'])+1, i, summary, va='center')
    
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()


def analyze_combined(data, aliases, char_threshold=3, location_threshold=50):
    scenes = []
    current_scene = {"location": "", "characters": set(), "content": [], "summary": ""}
    character_last_seen = defaultdict(int)
    dialogue_count = 0
    last_location_change = 0

    for item in data['text']:
        current_scene['content'].append(item)
        
        if 'LOCATION' in item:
            current_scene['location'] = item['LOCATION']
            last_location_change = dialogue_count
        
        if any(char in item for char in item.keys() if char not in ['ACTION', 'COMMENT', 'LOCATION']):
            character = list(item.keys())[0]
            normalized_character = normalize_character_name(character, aliases)
            current_scene['characters'].add(normalized_character)
            character_last_seen[normalized_character] = dialogue_count

            # Check for inactive characters
            inactive_characters = {char for char, last_seen in character_last_seen.items() 
                                   if dialogue_count - last_seen > location_threshold}
            current_scene['characters'] -= inactive_characters

            # Start a new scene if:
            # 1. Character constellation changes significantly OR
            # 2. Character constellation changes moderately AND there's a recent location change
            if (len(current_scene['characters']) > char_threshold and len(inactive_characters) > char_threshold - 1) or \
               (len(current_scene['characters']) > char_threshold - 1 and len(inactive_characters) > 0 and 
                dialogue_count - last_location_change < location_threshold):
                current_scene['summary'] = summarize_scene(current_scene)
                scenes.append(current_scene)
                current_scene = {"location": item['LOCATION'] if 'LOCATION' in item else current_scene['location'], 
                                 "characters": set([normalized_character]), 
                                 "content": [item], 
                                 "summary": ""}

            dialogue_count += 1

    if current_scene['content']:
        current_scene['summary'] = summarize_scene(current_scene)
        scenes.append(current_scene)

    return scenes


# Main execution
try:
    data = load_data('FinalFantasy/FFVI/data-ff6.json')
    meta_data = load_data('FinalFantasy/FFVI/meta-ff6.json')
except Exception as e:
    print(f"An error occurred while loading data: {str(e)}")
    sys.exit(1)

aliases = meta_data['aliases']

# Create results directory if it doesn't exist
os.makedirs('results', exist_ok=True)

story_scenes = analyze_story_structure(data, aliases)
save_results(story_scenes, 'results/FFVI_story_scenes.json')
plot_scene_structure(story_scenes, 'Final Fantasy VI Story Structure', 'results/FFVI_story_structure.png')

character_scenes_short = analyze_character_constellations(data, aliases, inactivity_threshold=25)
save_results(character_scenes_short, 'results/FFVI_character_scenes_short.json')
plot_scene_structure(character_scenes_short, 'Final Fantasy VI Character Scenes (Short)', 'results/FFVI_character_scenes_short.png')

character_scenes_medium = analyze_character_constellations(data, aliases, inactivity_threshold=50)
save_results(character_scenes_medium, 'results/FFVI_character_scenes_medium.json')
plot_scene_structure(character_scenes_medium, 'Final Fantasy VI Character Scenes (Medium)', 'results/FFVI_character_scenes_medium.png')

character_scenes_long = analyze_character_constellations(data, aliases, inactivity_threshold=100)
save_results(character_scenes_long, 'results/FFVI_character_scenes_long.json')
plot_scene_structure(character_scenes_long, 'Final Fantasy VI Character Scenes (Long)', 'results/FFVI_character_scenes_long.png')

combined_scenes = analyze_combined(data, aliases, char_threshold=3, location_threshold=50)
save_results(combined_scenes, 'results/FFVI_combined_scenes.json')
plot_scene_structure(combined_scenes, 'Final Fantasy VI Combined Scene Analysis', 'results/FFVI_combined_scenes.png')

print(f"Number of story-based scenes: {len(story_scenes)}")
print(f"Number of character-based scenes (short): {len(character_scenes_short)}")
print(f"Number of character-based scenes (medium): {len(character_scenes_medium)}")
print(f"Number of character-based scenes (long): {len(character_scenes_long)}")
print(f"Number of combined analysis scenes: {len(combined_scenes)}")

print("Analysis completed successfully. Results saved in the 'results' directory.")