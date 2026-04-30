import random
import json
from pathlib import Path
from typing import Optional, Dict, Any

class ChatGAU:
    def __init__(self, config_path: str = "tropical_config.json"):
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        else:
            self.config = {}

        self.few_shot_examples = self.config.get("chatgau_logic", {}).get("few_shot_examples", [
            "A high-energy 80s Merengue with sharp brass and fast tambora",
            "A romantic modern Bachata, crystal clear requinto, 130 BPM"
        ])

    def humanize_json(self, metadata_json: Dict[str, Any]) -> str:
        """
        Translates raw API JSON data into a human-like musical prompt.
        ChatGAU Engine logic.
        """
        info = metadata_json.get("info", {})
        features = metadata_json.get("features", {})
        tags = metadata_json.get("tags", [])
        
        genre = info.get("genre", "tropical music")
        energy = features.get("energy", 0.5)
        danceability = features.get("danceability", 0.5)
        tempo = features.get("tempo", 120)
        
        # Determine intensity descriptors
        intensity = "vibrant and energetic" if energy > 0.7 else "smooth and balanced"
        if energy < 0.4: intensity = "mellow and romantic"
        
        # Select random template structure to avoid robotic patterns
        templates = [
            f"A {intensity} {genre} track. It features {', '.join(tags[:3])}. {tempo:.0f} BPM.",
            f"{genre.capitalize()} with a sentiment of {intensity}. Key elements include {random.choice(tags) if tags else 'organic percussion'}. Tempo is {tempo:.0f} BPM.",
            f"Professional studio production of {genre}. Energy level is {energy*100:.0f}%, making it very {intensity}. Includes {', '.join(tags[:2])}.",
        ]
        
        base_prompt = random.choice(templates)
        
        # Add "Patch" logic (Instrumental control)
        instrument_patches = metadata_json.get("patch", {})
        add_instr = instrument_patches.get("add", [])
        rem_instr = instrument_patches.get("remove", [])
        
        if add_instr:
            base_prompt += f" Featuring additional {', '.join(add_instr)}."
        if rem_instr:
            base_prompt += f" Removing {', '.join(rem_instr)} from the standard arrangement."
            
        return base_prompt

    def generate_random_prompt(self, genre: str = "bachata") -> str:
        """
        Generates a prompt based on the tropical_config.json definitions.
        """
        genre_def = self.config.get("genre_definitions", {}).get(genre, {})
        if not genre_def:
            return random.choice(self.few_shot_examples)
            
        stems = genre_def.get("required_stems", [])
        bpm_range = genre_def.get("typical_bpm", [120, 130])
        bpm = random.randint(bpm_range[0], bpm_range[1])
        
        selected_stems = random.sample(stems, k=random.randint(3, len(stems)))
        
        return f"Authentic {genre} with {', '.join(selected_stems)}. {bpm} BPM, high fidelity tropical production."

# Singleton for quick access
chatgau = ChatGAU()

if __name__ == "__main__":
    # Test humanization
    sample_json = {
        "info": {"genre": "80s Merengue"},
        "features": {"energy": 0.9, "tempo": 165},
        "tags": ["brass", "fast tambora", "classic"],
        "patch": {"add": ["piano pad"]}
    }
    print("ChatGAU Output:")
    print(chatgau.humanize_json(sample_json))
