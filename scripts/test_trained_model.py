
import torch
import soundfile as sf
from audiocraft.models import MusicGen
from pathlib import Path

def test_model():
    checkpoint_path = "/workspace/GenAudius_V1/checkpoints/MODELO_FINAL_MASTER.th"
    output_path = "/workspace/GenAudius_V1/outputs/test_bachata_trained.wav"
    
    print(f"Loading base model: facebook/musicgen-medium...")
    model = MusicGen.get_pretrained('facebook/musicgen-medium')
    
    print(f"Loading trained weights from {checkpoint_path}...")
    checkpoint = torch.load(checkpoint_path, map_location='cuda')
    
    # Extract the state dict. Dora saves the LM state in 'best_state'
    if 'best_state' in checkpoint:
        print("Using 'best_state' from checkpoint.")
        state_dict = checkpoint['best_state']
    elif 'model' in checkpoint:
        print("Using 'model' from checkpoint.")
        state_dict = checkpoint['model']
    else:
        state_dict = checkpoint
        
    # Load into the LM
    model.lm.load_state_dict(state_dict)
    model.set_generation_params(duration=30)
    
    prompt = "A romantic modern Bachata, crystal clear requinto, 130 BPM, high fidelity"
    print(f"Generating audio with prompt: {prompt}")
    
    with torch.no_grad():
        output = model.generate([prompt], progress=True)
    
    print(f"Saving output to {output_path}")
    Path("/workspace/GenAudius_V1/outputs").mkdir(parents=True, exist_ok=True)
    wav_np = output[0].detach().cpu().numpy().T
    sf.write(output_path, wav_np, model.sample_rate)
    print("Done!")

if __name__ == "__main__":
    test_model()
