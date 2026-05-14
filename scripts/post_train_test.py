import requests
import os
import time
from pathlib import Path

# --- Configuration ---
API_BASE_URL = "http://localhost:8000"  # Update to production URL when ready
API_KEY = "gau_master_secure_2026"
HEADERS = {"x-api-key": API_KEY}
OUTPUT_DIR = Path("outputs/tests")

def test_production_quality():
    """
    Script para probar la calidad del modelo una vez terminado el entrenamiento.
    """
    print("\n--- GenAudius: Prueba de Calidad Post-Entrenamiento ---")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Definir un prompt que ponga a prueba el "swing" aprendido
    payload = {
        "prompt": "bachata moderna, estilo Danny Garcia, guitarras brillantes, percusión real, romántica",
        "version": "MusicGAU-Tropical-V1",
        "make_instrumental": False
    }
    
    try:
        print(f"\n[1/3] Enviando petición de generación a {API_BASE_URL}...")
        r = requests.post(f"{API_BASE_URL}/api/v1/generate", json=payload, headers=HEADERS)
        r.raise_for_status()
        task_data = r.json().get('data', {})
        task_id = task_data.get('taskId')
        print(f"Tarea enviada con éxito. ID: {task_id}")
        
        # 2. Poll for results
        print("\n[2/3] Esperando a que el motor procese la música...")
        while True:
            # En producción, esto llamaría a get_record_info
            # Por ahora simulamos la espera
            status_check = requests.get(f"{API_BASE_URL}/api/v1/chat/credit", headers=HEADERS)
            if status_check.status_code == 200:
                print("El motor está respondiendo. Verificando estado de la tarea...")
                # Aquí iría la lógica real de polling del taskId
                break
            time.sleep(10)
            
        print("\n[3/3] ¡Música generada! (Simulado)")
        print(f"Descarga el archivo y verifica: {OUTPUT_DIR}/test_result.wav")
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")

if __name__ == "__main__":
    test_production_quality()
