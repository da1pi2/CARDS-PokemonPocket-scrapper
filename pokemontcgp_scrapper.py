import requests
from bs4 import BeautifulSoup
import json
import re

# URL del sito delle carte
url = 'https://pocket.limitlesstcg.com/cards/A1?display=compact'

# Realizziamo la richiesta HTTP per ottenere il contenuto della pagina
response = requests.get(url)
html_content = response.text

# Analizziamo l'HTML con BeautifulSoup
soup = BeautifulSoup(html_content, 'html.parser')

# Troviamo tutte le carte nella pagina
cards = soup.find_all('div', class_='card-classic')

# Lista per memorizzare i dati delle carte
card_data = []

# Dizionario di mappatura per le lettere e le tipologie
type_mapping = {
    'G': 'Grass',
    'R': 'Fire',
    'W': 'Water',
    'L': 'Lightning',
    'P': 'Psychic',
    'F': 'Fighting',
    'D': 'Darkness',
    'M': 'Metal',
    'Y': 'Fairy',
    'C': 'Colorless'
}

# Funzione per mappare i simboli al tipo, con separazione per le stringhe più lunghe
def map_attack_cost(cost_elements):
    cost_counts = {}
    
    for cost in cost_elements:
        cost_symbol = cost.text.strip()  # Simbolo grezzo
        
        # Se il simbolo è una stringa lunga, la dividiamo in singole lettere
        if len(cost_symbol) > 1:
            for letter in cost_symbol:
                cost_type = type_mapping.get(letter, 'Unknown')
                if cost_type == 'Unknown':
                    print(f"Attenzione: simbolo non riconosciuto '{letter}'.")
                cost_counts[cost_type] = cost_counts.get(cost_type, 0) + 1
        else:
            # Caso in cui il simbolo è una singola lettera
            cost_type = type_mapping.get(cost_symbol, 'Unknown')
            if cost_type == 'Unknown':
                print(f"Attenzione: simbolo non riconosciuto '{cost_symbol}'.")
            cost_counts[cost_type] = cost_counts.get(cost_type, 0) + 1

    # Creazione del formato per il costo
    attack_cost = '-'.join(f"{count}x{ctype}" for ctype, count in cost_counts.items())
    return attack_cost if attack_cost else 'No Cost'


# Estrarre i dettagli di ogni carta
for card in cards:
    card_info = {}

    # Nome della carta
    name_section = card.find('span', class_='card-text-name')
    card_info['name'] = name_section.text.strip() if name_section else 'Unknown'

    # Tipo e HP della carta
    type_hp_section = card.find('p', class_='card-text-title')
    if type_hp_section:
        content = type_hp_section.text.replace(card_info['name'], '').strip()
        parts = [part.strip() for part in content.split('-') if part.strip()]
        card_info['type'] = parts[0] if len(parts) >= 2 else 'N/A'
        card_info['hp'] = parts[1] if len(parts) >= 2 else 'N/A'

    # Tipo di carta
    card_type_section = card.find('p', class_='card-text-type')
    stages = ['Basic', 'Stage 1', 'Stage 2']
    card_info['card_type'] = next((stage for stage in stages if stage in card_type_section.text), 'Unknown') if card_type_section else 'Unknown'

    # Attacchi della carta
    attack_section = card.find_all('div', class_='card-text-attack')
    attacks = []
    for attack in attack_section:
        attack_info_section = attack.find('p', class_='card-text-attack-info')
        attack_effect_section = attack.find('p', class_='card-text-attack-effect')

        if attack_info_section:
            cost_elements = attack_info_section.find_all('span', class_='ptcg-symbol')
            attack_cost = map_attack_cost(cost_elements)  # Usa la funzione migliorata

            attack_text = attack_info_section.text.strip()
            for cost_element in cost_elements:
                attack_text = attack_text.replace(cost_element.text, '').strip()

            attack_parts = attack_text.rsplit(' ', 1)
            attack_name = attack_parts[0].strip() if len(attack_parts) > 1 else 'Unknown'
            attack_damage = attack_parts[1].strip() if len(attack_parts) > 1 else '0'

            attack_effect = attack_effect_section.text.strip() if attack_effect_section else 'No effect'

            attacks.append({
                'cost': attack_cost,
                'name': attack_name,
                'damage': attack_damage,
                'effect': attack_effect
            })
    card_info['attacks'] = attacks

    # Abilità della carta
    ability_section = card.find('div', class_='card-text-ability')
    if ability_section:
        ability_name_section = ability_section.find('p', class_='card-text-ability-info')
        ability_effect_section = ability_section.find('p', class_='card-text-ability-effect')
        ability_name = ability_name_section.text.replace('Ability:', '').strip() if ability_name_section else 'Unknown'
        ability_effect = ability_effect_section.text if ability_effect_section else 'No effect'
        ability_effect_cleaned = re.sub(r'\[.*?\]', '', ability_effect).strip()

        card_info['ability'] = {
            'name': ability_name,
            'effect': ability_effect_cleaned
        }
    else:
        card_info['ability'] = {'name': 'No ability', 'effect': 'N/A'}

    # Debolezza e costo di ritirata
    weakness_retreat_section = card.find('p', class_='card-text-wrr')
    if weakness_retreat_section:
        text = weakness_retreat_section.text.strip().split('\n')
        card_info['weakness'] = text[0].split(': ')[1] if len(text) > 0 and ': ' in text[0] else 'N/A'
        card_info['retreat'] = text[1].split(': ')[1] if len(text) > 1 and ': ' in text[1] else 'N/A'

    # URL dell'immagine
    image_section = card.find('img', class_='card shadow max-xs')
    card_info['image_url'] = image_section.attrs['src'] if image_section and 'src' in image_section.attrs else 'N/A'

    # Aggiungere i dati estratti alla lista
    card_data.append(card_info)

# Salvare i risultati in formato JSON
json_filename = 'pokemon_cards.json'
with open(json_filename, mode='w', encoding='utf-8') as jsonfile:
    json.dump(card_data, jsonfile, indent=4, ensure_ascii=False)

# Output per conferma
print(json.dumps(card_data, indent=4, ensure_ascii=False))


# Mostrare i risultati sulla console
for card in card_data:
    print(f"Name: {card['name']}")
    print(f"Type: {card.get('type', 'N/A')}")
    print(f"HP: {card.get('hp', 'N/A')}")
    print(f"Card Type: {card.get('card_type', 'N/A')}")
    #print(f"Image URL: {card.get('image_url', 'N/A')}")
    print(f"Weakness: {card.get('weakness', 'N/A')}")
    print(f"Retreat Cost: {card.get('retreat', 'N/A')}")
    
    # Controlliamo se la carta ha attacchi prima di tentare di stamparli
    if card['attacks']:
        #print(f"costo attacco: {attack_cost}")
        print(f"Attacks: {card['attacks']}")
    else:
        print("Attacks: N/A")
    
    print('-' * 40)
