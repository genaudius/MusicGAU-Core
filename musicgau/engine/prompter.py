import random
import json
from pathlib import Path
from typing import Optional

class BachataPrompter:
    def __init__(self, styles_json_path: Optional[str] = None):
        if styles_json_path and Path(styles_json_path).exists():
            with open(styles_json_path, "r", encoding="utf-8") as f:
                self.styles = json.load(f)
        else:
            # Diccionario robusto predeterminado
            self.styles = {
                "Aventura": {
                    "tags": ["Estilo Urbano", "Requinto con Chorus", "Bajo Dominante", "R&B Fusion"],
                    "moods": ["Amargue", "Romántico", "Agresivo"],
                    "instrumentation": ["Ensamble completo", "Solo bajo y güira"],
                    "panning": ["Bongo panorámico", "Güira al centro"]
                },
                "Romeo Santos": {
                    "tags": ["Producción High-Tech", "Stems Cristalinos", "Ensamble Sofisticado", "Pop Influence"],
                    "moods": ["Romántico", "Elegante", "Smooth"],
                    "instrumentation": ["Ensamble con cuerdas", "Producción pulida"],
                    "panning": ["Mezcla limpia", "Separación estéreo amplia"]
                },
                "Juan Luis Guerra": {
                    "tags": ["Instrumentación en Vivo", "Acústico", "Percusión Compleja", "4:40 Swing"],
                    "moods": ["Alegre", "Festivo", "Poético"],
                    "instrumentation": ["Metales", "Percusión real", "Coros"],
                    "panning": ["Sonido de orquesta", "Espacialidad natural"]
                },
                "Antony Santos": {
                    "tags": ["Requinto Agresivo", "Alta Energía", "Derecho marcado", "Estilo de Guardia"],
                    "moods": ["Amargue", "Bailable", "Calle"],
                    "instrumentation": ["Requinto líder", "Güira rápida"],
                    "panning": ["Percusión centrada", "Pegada fuerte"]
                }
            }
        
        self.bpms = [115, 120, 125, 128, 132]
        self.keys = ["Do mayor", "Sol mayor", "Re mayor", "La menor", "Mi menor"]

    def generate_random_prompt(self, base_style: Optional[str] = None) -> str:
        """
        Genera un prompt robusto y aleatorio siguiendo el ADN de la bachata.
        """
        style_name = base_style if base_style in self.styles else random.choice(list(self.styles.keys()))
        style_data = self.styles[style_name]
        
        selected_tags = random.sample(style_data["tags"], k=random.randint(2, len(style_data["tags"])))
        mood = random.choice(style_data["moods"])
        inst = random.choice(style_data["instrumentation"])
        pan = random.choice(style_data["panning"])
        bpm = random.choice(self.bpms)
        key = random.choice(self.keys)
        
        # Estructura robusta
        prompt_parts = [
            f"Bachata estilo {style_name}",
            ", ".join(selected_tags),
            f"Sentimiento {mood}",
            inst,
            pan,
            f"{bpm} BPM",
            f"en tono {key}",
            "calidad de estudio, masterización profesional"
        ]
        
        return ", ".join(prompt_parts)

    def predict_best_prompt(self, desired_vibe: str) -> str:
        """
        Simulación de algoritmo de predicción basado en vibras.
        """
        # Aquí podríamos usar Spotify para buscar tracks con ese vibe y extraer tags.
        # Por ahora, mapeamos palabras clave a estilos.
        vibe = desired_vibe.lower()
        if "calle" in vibe or "guardia" in vibe:
            return self.generate_random_prompt("Antony Santos")
        if "moderno" in vibe or "pop" in vibe:
            return self.generate_random_prompt("Romeo Santos")
        if "triste" in vibe or "amargue" in vibe:
            return self.generate_random_prompt("Aventura")
        
        return self.generate_random_prompt()

# Singleton para uso rápido
prompter = BachataPrompter()
