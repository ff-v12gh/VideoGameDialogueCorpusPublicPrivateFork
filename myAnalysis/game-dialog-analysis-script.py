import json
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
import os
from textblob import TextBlob

# Erstellen des results-Ordners, falls er nicht existiert
if not os.path.exists('results'):
    os.makedirs('results')

# Dateipfade zu den JSON-Dateien
json_files = {
    'FF1': 'Data/FinalFantasy/FFI/data.json',
    'FF2': 'Data/FinalFantasy/FFII/data.json',
    'FF6': 'Data/FinalFantasy/FFVI/data.json'
}

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def create_character_network(data):
    G = nx.Graph()
    prev_character = None
    for item in data['text']:
        if isinstance(item, dict):
            for character, dialogue in item.items():
                if character not in ['ACTION', 'COMMENT', 'LOCATION', 'SYSTEM']:
                    G.add_node(character)
                    if prev_character and prev_character != character:
                        if G.has_edge(prev_character, character):
                            G[prev_character][character]['weight'] += 1
                        else:
                            G.add_edge(prev_character, character, weight=1)
                    prev_character = character
    return G

def analyze_sentiment(data):
    sentiments = {}
    for item in data['text']:
        if isinstance(item, dict):
            for character, dialogue in item.items():
                if character not in ['ACTION', 'COMMENT', 'LOCATION', 'SYSTEM']:
                    blob = TextBlob(dialogue)
                    sentiment = blob.sentiment.polarity
                    if character in sentiments:
                        sentiments[character].append(sentiment)
                    else:
                        sentiments[character] = [sentiment]
    return {char: sum(vals)/len(vals) for char, vals in sentiments.items()}

def plot_character_network(G, title, output_file):
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, node_color='lightblue', 
            node_size=1000, font_size=8, font_weight='bold')
    edge_weights = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_weights)
    plt.title(title)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

def plot_sentiment_analysis(sentiments, title, output_file):
    plt.figure(figsize=(12, 8))
    characters = list(sentiments.keys())
    sentiment_values = list(sentiments.values())
    plt.bar(characters, sentiment_values)
    plt.title(title)
    plt.xlabel('Characters')
    plt.ylabel('Average Sentiment')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_file)
    plt.close()

# Hauptanalyse
for game, file_path in json_files.items():
    data = load_json(file_path)
    
    # Charakternetzwerk
    G = create_character_network(data)
    plot_character_network(G, f'Character Interaction Network - {game}', f'results/character_network_{game}.png')
    
    # Sentiment-Analyse
    sentiments = analyze_sentiment(data)
    plot_sentiment_analysis(sentiments, f'Character Sentiment Analysis - {game}', f'results/sentiment_analysis_{game}.png')
    
    # Zusätzliche Statistiken
    character_dialogue_count = Counter(character for item in data['text'] if isinstance(item, dict) 
                                       for character in item.keys() if character not in ['ACTION', 'COMMENT', 'LOCATION', 'SYSTEM'])
    
    with open(f'results/statistics_{game}.txt', 'w') as f:
        f.write(f"Statistics for {game}:\n")
        f.write(f"Total number of dialogues: {len(data['text'])}\n")
        f.write(f"Number of unique characters: {len(character_dialogue_count)}\n")
        f.write("Top 10 characters by dialogue count:\n")
        for char, count in character_dialogue_count.most_common(10):
            f.write(f"{char}: {count}\n")

print("Analysis complete. Results saved in the 'results' folder.")
