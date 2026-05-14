# 🏆 Memoria del Proyecto: Entrenamiento Maestro GenAudius Tropical

Este documento registra la configuración, el dataset y el estado del entrenamiento de alta fidelidad iniciado el 30 de abril de 2026.

## 📊 Estadísticas del Dataset
Se ha construido uno de los datasets de música tropical más completos para fine-tuning de IA:
- **Total de Canciones:** 1,290 temas originales.
- **Pistas de Entrenamiento:** ~5,160 stems individuales (Guitarras, Bajos, Percusiones, Voces).
- **Géneros Integrados:**
  - **Bachata:** (Danny Garcia - Protegido, Aventura, Zacarias Ferreira, Romeo, Frank Reyes, Luis Vargas, Luis Segura, Leonardo Paniagua).
  - **Salsa:** (Grupo Niche, Victor Manuelle, Rey Ruiz).
  - **Vallenato:** (Los Gigantes, Binomio de Oro, Los Inquietos, Carlos Vives).
  - **Merengue:** (Típico, Mambo, 80s, Navideño, Wilfrido Vargas, Elvis Crespo).
  - **Música Mexicana:** (Banda El Recodo, Los Tigres del Norte, Mariachi).
  - **Pop/Contemporáneo:** (Baladas Románticas y Música en Inglés).

## ⚙️ Configuración Técnica (Blindaje)
Para garantizar la estabilidad en RunPod (RTX 4090), se implementaron las siguientes mejoras:
- **Estabilidad del DataLoader:** `dataset.num_workers=0` para evitar errores de memoria compartida en Docker.
- **Rutas Absolutas:** Manifiestos reconstruidos con rutas completas para evitar errores de `FileNotFound`.
- **Motor Oficial:** Cambio del script personalizado al `official solver` de AudioCraft para máxima calidad de gradientes.
- **Optimización de Memoria:** `batch_size=4` para mantener el uso de VRAM en ~18GB de 24GB.

## 🛡️ Sistema de Vigilancia y Seguridad
Se han desplegado dos sistemas autónomos en el servidor:
1. **El Guardián (`guardian.py`):**
   - Monitorea el progreso cada 30 min.
   - **Límite de Seguridad:** Detendrá el entrenamiento a las **15 horas** exactas.
   - **Salvado Maestro:** Copiará el modelo final a `/workspace/GenAudius_V1/checkpoints/MODELO_FINAL_MASTER.th`.
2. **Separador Dinámico (`separate_all_genres.py`):**
   - Procesa los stems en segundo plano.
   - Integra automáticamente los nuevos géneros al entrenamiento en cuanto termina cada bloque.

## 🚀 Próximos Pasos
Al finalizar las 15 horas de entrenamiento:
1. Descargar el archivo `MODELO_FINAL_MASTER.th`.
2. Ejecutar el script de inferencia para validar el "swing" multi-género.
3. Integrar los pesos finales en el backend de producción de GenAudius.

---
**Estado del Saldo:** ~$11.00 (Suficiente para el ciclo completo).
**Fecha de finalización estimada:** 1 de Mayo de 2026, 09:30 AM.
