import os
import time
import subprocess
from pathlib import Path

# Configuración
LOG_PATH = "/tmp/audiocraft_root/xps/754b57ad/solver.log.0"
PROGRESS_LOG = "/workspace/log_de_mision.txt"
FINAL_MODEL_DEST = "/workspace/GenAudius_V1/checkpoints/MODELO_FINAL_MASTER.th"
MAX_TIME_SECONDS = 15.0 * 3600  # 15 horas exactas
START_TIME = time.time()

def log_message(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(PROGRESS_LOG, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(msg)

log_message("--- INICIANDO GUARDIÁN DE GENAUDIUS ---")
log_message(f"Objetivo: Monitorear entrenamiento y salvar modelo antes de 16.5 horas.")

while True:
    elapsed = time.time() - START_TIME
    remaining = MAX_TIME_SECONDS - elapsed
    
    # 1. Verificar Progreso
    if os.path.exists(LOG_PATH):
        try:
            last_lines = subprocess.check_output(["tail", "-n", "20", LOG_PATH]).decode()
            if "Epoch" in last_lines:
                stats = [line for line in last_lines.split("\n") if "Epoch" in line][-1]
                log_message(f"PROGRESO ACTUAL: {stats}")
        except:
            log_message("Esperando a que el solver genere nuevos logs...")
    
    # 2. Verificar si hay nuevos géneros para integrar
    # (Este paso se maneja vía disparadores en los otros scripts, 
    # pero el guardián asegura que el entrenamiento siga vivo)
    try:
        pid = subprocess.check_output(["pgrep", "-f", "train"]).decode().strip()
        log_message(f"Entrenamiento activo (PID {pid}). Tiempo restante: {remaining/3600:.2f} horas.")
    except:
        log_message("ALERTA: Entrenamiento detenido. Intentando relanzar...")
        subprocess.run(["bash", "/workspace/launch_official_pod.sh"])

    # 3. Parada de Seguridad
    if elapsed >= MAX_TIME_SECONDS:
        log_message("!!! TIEMPO LÍMITE ALCANZADO !!! Iniciando guardado final...")
        subprocess.run(["pkill", "-TERM", "-f", "train"])
        time.sleep(60) # Esperar a que guarde
        
        src_checkpoint = "/tmp/audiocraft_root/xps/754b57ad/checkpoint.th"
        if os.path.exists(src_checkpoint):
            os.makedirs(os.path.dirname(FINAL_MODEL_DEST), exist_ok=True)
            subprocess.run(["cp", src_checkpoint, FINAL_MODEL_DEST])
            log_message(f"ÉXITO: Modelo salvado en {FINAL_MODEL_DEST}")
        else:
            log_message("ERROR: No se encontró el checkpoint final.")
        
        break

    time.sleep(1800) # Revisar cada 30 min
