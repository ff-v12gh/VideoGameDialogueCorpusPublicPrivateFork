import json
import os
import nltk
from collections import Counter
import matplotlib.pyplot as plt
import networkx as nx

# Ensure necessary NLTK data is downloaded
nltk.download('punkt', quiet=True)

# Definieren Sie hier die Pfade
base_path = "/Users/martinschlenk/Desktop/Videogame-Dialogue-Corpus/VDC04/VideoGameDialogueCorpusPublicPrivateFork"
data_paths = {
    "FFI": f"{base_path}/data/FinalFantasy/FFI/data.json",
    "FFII": f"{base_path}/data/FinalFantasy/FFII/data.json",
    "FFVI": f"{base_path}/data/FinalFantasy/FFVI/data.json"
}
results_path = f"{base_path}/myAnalysis/results"

# Stellen Sie sicher, dass der results_path existiert
os.makedirs(results_path, exist_ok=True)

def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def extract_dialogues(data):
    dialogues = []
    for item in data['text']:
        if isinstance(item, dict):
            for key, value in item.items():
                if key not in ['ACTION', 'LOCATION', 'SYSTEM', 'COMMENT']:
                    if isinstance(value, str):
                        dialogues.append((key, value))
                    elif isinstance(value, list):
                        dialogues.extend((key, v) for v in value if isinstance(v, str))
    return dialogues

def analyze_character_presence(dialogues):
    return Counter(character for character, _ in dialogues)

def analyze_dialogue_length(dialogues):
    return {character: sum(len(nltk.word_tokenize(dialogue)) for _, dialogue in dialogues if _ == character)
            for character in set(character for character, _ in dialogues)}

def analyze_word_frequency(dialogues):
    all_words = [word.lower() for _, dialogue in dialogues 
                 for word in nltk.word_tokenize(dialogue) if isinstance(dialogue, str)]
    return Counter(all_words)

def create_character_network(dialogues, top_characters):
    G = nx.Graph()
    previous_character = None
    for character, _ in dialogues:
        if character in top_characters and previous_character in top_characters:
            if G.has_edge(previous_character, character):
                G[previous_character][character]['weight'] += 1
            else:
                G.add_edge(previous_character, character, weight=1)
        previous_character = character
    return G

def analyze_centrality(G):
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    eigenvector_centrality = nx.eigenvector_centrality(G, max_iter=1000)
    return {
        'degree': degree_centrality,
        'betweenness': betweenness_centrality,
        'eigenvector': eigenvector_centrality
    }

def plot_character_presence(presence, game):
    plt.figure(figsize=(12, 6))
    characters, counts = zip(*presence.most_common(10))
    plt.bar(characters, counts)
    plt.title(f'Top 10 Characters by Dialogue Count in {game}')
    plt.xlabel('Characters')
    plt.ylabel('Dialogue Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f"{results_path}/{game}_character_presence.png")
    plt.close()

def plot_character_network(G, game, centrality_measures):
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)
    
    node_sizes = [centrality_measures['degree'][node] * 3000 for node in G.nodes()]
    node_colors = [centrality_measures['betweenness'][node] for node in G.nodes()]
    
    nodes = nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, cmap=plt.cm.viridis)
    nx.draw_networkx_edges(G, pos)
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
    
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    nx.draw_networkx_edge_labels(G, pos, 
                                 edge_labels={(u,v): G[u][v]['weight'] for u,v in G.edges()})
    
    plt.title(f'Top 10 Character Interaction Network in {game}')
    plt.colorbar(nodes, label='Betweenness Centrality')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(f"{results_path}/{game}_top10_character_network.png")
    plt.close()

def save_results(results, game):
    with open(f"{results_path}/{game}_results.json", 'w') as f:
        json.dump(results, f, indent=2)

def main():
    for game, path in data_paths.items():
        print(f"Analyzing {game}...")
        data = load_data(path)
        dialogues = extract_dialogues(data)
        
        character_presence = analyze_character_presence(dialogues)
        top_10_characters = [char for char, _ in character_presence.most_common(10)]
        
        G = create_character_network(dialogues, top_10_characters)
        centrality_measures = analyze_centrality(G)
        
        results = {
            "character_presence": dict(character_presence),
            "dialogue_length": analyze_dialogue_length(dialogues),
            "word_frequency": analyze_word_frequency(dialogues),
            "centrality_measures": {
                measure: {char: value for char, value in measure_values.items() if char in top_10_characters}
                for measure, measure_values in centrality_measures.items()
            }
        }
        
        save_results(results, game)
        plot_character_presence(character_presence, game)
        plot_character_network(G, game, centrality_measures)
        
        print(f"Analysis for {game} complete. Results saved in {results_path}")

if __name__ == "__main__":
    main()