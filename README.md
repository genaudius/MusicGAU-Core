# 🌴 MusicGAU
**The Latin Tropical AI Music Engine. Powered by Gen Audius LLC.**

MusicGAU es un modelo de generación de audio de última generación especializado en géneros tropicales latinos y producción musical multianálisis. Desarrollado por Gen Audius LLC, este motor transforma metadatos contextuales y secuencias MIDI en producciones de audio de alta fidelidad con calidad de estudio.

🚀 Características Principales
- **Tropical Focus**: Entrenamiento optimizado para Bachata, Merengue y Bolero utilizando stems originales y percusiones orgánicas (Timbal, Bongó, Güira).
- **GAU-DNA Pipeline**: Procesamiento de datos único que integra:
    - **Spotify Pedalboard**: Síntesis de VST programática para un sonido no sintético.
    - **Loudness Normalization**: Audio normalizado al 100% mediante `pyloudnorm`.
    - **Multidimensional Metadata**: Integración de APIs de Spotify (Audio Features/Analysis) y Last.fm para un etiquetado contextual profundo (épocas, estilos y energía).
- **ChatGAU Integration**: Un motor de NLP (ChatGAU) que traduce datos JSON complejos en prompts humanos y coherentes para el modelo de audio.
- **Architecture**: Basado en el framework de `stable-audio-tools` de Stability AI, optimizado para la predicción de secciones de 30s y coherencia instrumental.

🛠️ Pipeline de Entrenamiento
- **Source**: `clean_midi` dataset segmentado por instrumentos mediante protocolos de splitting.
- **Analysis**: Extracción de atributos de energía, bailabilidad y estructura (sections) vía Spotify API.
- **Synthesis**: Renderizado de stems mediante Pedalboard para eliminar el rastro "robótico" de los sintetizadores básicos.
- **Natural Language**: Procesamiento de etiquetas históricas y tags humanos vía Last.fm para recrear ambientes específicos (ej: Merengue de los 80).

📄 Licencia y Derechos
Todo el audio generado a través de MusicGAU es **Royalty-Free**. El modelo ha sido entrenado exclusivamente con materiales propiedad de Gen Audius LLC, garantizando una producción libre de infracciones de copyright y percusiones clonadas.

© 2026 Gen Audius LLC | Georgia, USA.
*Empowering Latin Music through Artificial Intelligence.*
