import json
import matplotlib.pyplot as plt
from collections import defaultdict
from textwrap import wrap
import os
import sys
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

def analyze_combined(data, aliases, char_threshold=3, location_threshold=50):
    scenes = []
    current_scene = {"locations": set(), "characters": set(), "content": [], "summary": ""}
    character_last_seen = defaultdict(int)
    dialogue_count = 0
    last_location_change = 0

    for item in data['text']:
        current_scene['content'].append(item)
        
        if 'LOCATION' in item:
            current_scene['locations'].add(item['LOCATION'])
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
                current_scene = {"locations": set(current_scene['locations']), 
                                 "characters": set([normalized_character]), 
                                 "content": [item], 
                                 "summary": ""}

            dialogue_count += 1

    if current_scene['content']:
        current_scene['summary'] = summarize_scene(current_scene)
        scenes.append(current_scene)

    return scenes

def summarize_scene(scene):
    characters = ", ".join(scene['characters'])
    locations = ", ".join(scene['locations'])
    content = scene['content']
    first_dialogue = next((item for item in content if any(char in item for char in item.keys() if char not in ['ACTION', 'COMMENT', 'LOCATION'])), None)
    last_dialogue = next((item for item in reversed(content) if any(char in item for char in item.keys() if char not in ['ACTION', 'COMMENT', 'LOCATION'])), None)
    
    summary = f"Locations: {locations}. Characters: {characters}. "
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

def plot_scene_structure(scenes, title):
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
    return fig

def divide_into_acts(scenes, act_threshold):
    acts = []
    current_act = []
    act_dialogue_count = 0

    for scene in scenes:
        current_act.append(scene)
        act_dialogue_count += len(scene['content'])

        if act_dialogue_count >= act_threshold:
            acts.append(current_act)
            current_act = []
            act_dialogue_count = 0

    if current_act:
        acts.append(current_act)

    return acts

class FF6AnalysisGUI:
    def __init__(self, master):
        self.master = master
        master.title("Final Fantasy VI Script Analysis")

        self.data = load_data('FinalFantasy/FFVI/data-ff6.json')
        self.meta_data = load_data('FinalFantasy/FFVI/meta-ff6.json')
        self.aliases = self.meta_data['aliases']

        # Create and pack widgets
        ttk.Label(master, text="Character Threshold:").grid(row=0, column=0, sticky="w")
        self.char_threshold = ttk.Scale(master, from_=1, to=10, orient=tk.HORIZONTAL)
        self.char_threshold.set(3)
        self.char_threshold.grid(row=0, column=1)
        self.char_threshold_value = ttk.Label(master, text="3")
        self.char_threshold_value.grid(row=0, column=2)

        ttk.Label(master, text="Location Threshold:").grid(row=1, column=0, sticky="w")
        self.location_threshold = ttk.Scale(master, from_=10, to=200, orient=tk.HORIZONTAL)
        self.location_threshold.set(50)
        self.location_threshold.grid(row=1, column=1)
        self.location_threshold_value = ttk.Label(master, text="50")
        self.location_threshold_value.grid(row=1, column=2)

        ttk.Label(master, text="Act Threshold:").grid(row=2, column=0, sticky="w")
        self.act_threshold = ttk.Scale(master, from_=1000, to=10000, orient=tk.HORIZONTAL)
        self.act_threshold.set(5000)
        self.act_threshold.grid(row=2, column=1)
        self.act_threshold_value = ttk.Label(master, text="5000")
        self.act_threshold_value.grid(row=2, column=2)

        self.analyze_button = ttk.Button(master, text="Analyze", command=self.analyze)
        self.analyze_button.grid(row=3, column=1)

        self.result_text = tk.Text(master, height=10, width=50)
        self.result_text.grid(row=4, column=0, columnspan=3)

        self.fig = None
        self.canvas = None

        # Bind the scale widgets to update functions
        self.char_threshold.bind("<Motion>", self.update_char_threshold)
        self.location_threshold.bind("<Motion>", self.update_location_threshold)
        self.act_threshold.bind("<Motion>", self.update_act_threshold)

    def update_char_threshold(self, event):
        value = int(self.char_threshold.get())
        self.char_threshold_value.config(text=str(value))

    def update_location_threshold(self, event):
        value = int(self.location_threshold.get())
        self.location_threshold_value.config(text=str(value))

    def update_act_threshold(self, event):
        value = int(self.act_threshold.get())
        self.act_threshold_value.config(text=str(value))

    def analyze(self):
        char_threshold = int(self.char_threshold.get())
        location_threshold = int(self.location_threshold.get())
        act_threshold = int(self.act_threshold.get())

        scenes = analyze_combined(self.data, self.aliases, char_threshold, location_threshold)
        acts = divide_into_acts(scenes, act_threshold)

        result = f"Number of scenes: {len(scenes)}\n"
        result += f"Number of acts: {len(acts)}\n"
        for i, act in enumerate(acts, 1):
            result += f"Act {i}: {len(act)} scenes, {sum(len(scene['content']) for scene in act)} dialogues\n"

        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, result)

        if self.fig:
            plt.close(self.fig)
        self.fig = plot_scene_structure(scenes, "Final Fantasy VI Scene Structure")
        
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=5, column=0, columnspan=3)

        # Save results
        save_results(scenes, 'results/FFVI_combined_scenes.json')
        save_results(acts, 'results/FFVI_acts.json')

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    gui = FF6AnalysisGUI(root)
    root.mainloop()