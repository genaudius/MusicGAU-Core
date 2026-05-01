import os
import subprocess
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de Cloudflare R2
R2_ACCOUNT_ID = os.getenv('R2_ACCOUNT_ID')
R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY')
R2_SECRET_KEY = os.getenv('R2_SECRET_KEY')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME')

# Rutas de origen
WORKSPACE_DIR = "/workspace/GenAudius_V1"
MODEL_PATH = "/workspace/GenAudius_V1/checkpoints/MODELO_FINAL_MASTER.th"

# Rutas de destino locales
WORKSPACE_ARCHIVE_NAME = "/workspace/GenAudius_V1_Backup.tar.gz"

# Nombres de objetos en R2
R2_WORKSPACE_OBJECT = "GenAudius_V1_Backup.tar.gz"
R2_MODEL_OBJECT = "MODELO_FINAL_MASTER.th"

def get_s3_client():
    if not all([R2_ACCOUNT_ID, R2_ACCESS_KEY, R2_SECRET_KEY, R2_BUCKET_NAME]):
        raise ValueError("Faltan credenciales de R2 en el archivo .env. Por favor, créalo y configúralo.")

    endpoint_url = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    
    # Boto3 maneja multipart uploads automáticamente, excelente para archivos grandes
    return boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name='auto'
    )

def create_tar_gz(source_dir, output_filename):
    print(f"Empaquetando {source_dir} en {output_filename}... (Esto puede tomar un largo rato por los audios)")
    # Usamos subprocess con tar del sistema porque es mucho más rápido que la librería de Python
    try:
        subprocess.run(["tar", "-czf", output_filename, source_dir], check=True)
        print("Empaquetado completado exitosamente.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error al comprimir el workspace: {e}")
        return False

def upload_to_r2(file_path, bucket_name, object_name):
    s3 = get_s3_client()
    try:
        file_size_gb = os.path.getsize(file_path) / (1024**3)
        print(f"Iniciando subida de {object_name} ({file_size_gb:.2f} GB) a R2...")
        
        # Configuramos boto3 para optimizar subida de archivos gigantes
        config = boto3.s3.transfer.TransferConfig(
            multipart_threshold=1024 * 25,     # 25MB
            max_concurrency=10,
            multipart_chunksize=1024 * 25,     # 25MB
            use_threads=True
        )
        
        s3.upload_file(file_path, bucket_name, object_name, Config=config)
        print(f"✅ Subida exitosa: {object_name}")
    except FileNotFoundError:
        print(f"❌ El archivo {file_path} no fue encontrado.")
    except NoCredentialsError:
        print("❌ Credenciales incorrectas o no encontradas en R2.")
    except ClientError as e:
        print(f"❌ Error en la subida a R2: {e}")

if __name__ == "__main__":
    print("--- INICIANDO SISTEMA DE RESPALDO HACIA CLOUDFLARE R2 ---")
    
    # 1. Comprimir Workspace Completo (incluyendo audios)
    if not os.path.exists(WORKSPACE_ARCHIVE_NAME):
        success = create_tar_gz(WORKSPACE_DIR, WORKSPACE_ARCHIVE_NAME)
    else:
        print(f"El archivo {WORKSPACE_ARCHIVE_NAME} ya existe, omitiendo compresión.")
        success = True
    
    # 2. Subir Workspace Comprimido
    if success:
        upload_to_r2(WORKSPACE_ARCHIVE_NAME, R2_BUCKET_NAME, R2_WORKSPACE_OBJECT)
    
    # 3. Subir Modelo Maestro (Asegurar los pesos)
    if os.path.exists(MODEL_PATH):
        upload_to_r2(MODEL_PATH, R2_BUCKET_NAME, R2_MODEL_OBJECT)
    else:
        print(f"\n⚠️ ADVERTENCIA: No se encontró el modelo en {MODEL_PATH}.")
        print("Esto es normal si el entrenamiento AÚN NO HA TERMINADO.")
        print("El Guardián moverá el modelo a esa ruta cuando termine.")
        
    print("\n--- PROCESO FINALIZADO ---")
