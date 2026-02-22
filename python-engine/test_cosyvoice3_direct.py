"""Direct CosyVoice3 test — follows official example.py format exactly.

Usage:
    cd python-engine
    .venv/Scripts/activate
    python test_cosyvoice3_direct.py

This tests CosyVoice3 model directly (without our TTSEngine wrapper) to
isolate whether the issue is in the model or in our calling code.
"""

import os
import sys
import time

# Add CosyVoice to path
cosyvoice_root = os.path.join(os.path.dirname(__file__), "third_party", "CosyVoice")
matcha_path = os.path.join(cosyvoice_root, "third_party", "Matcha-TTS")
for p in [cosyvoice_root, matcha_path]:
    if p not in sys.path:
        sys.path.insert(0, p)

import torch
import torchaudio
from cosyvoice.cli.cosyvoice import CosyVoice3

# --- Config ---
# Adjust this path if your model is stored elsewhere
MODEL_DIR = os.path.join(
    os.path.expanduser("~"), "Documents", "local-aI-dubber-desktop",
    "models", "cosyvoice3", "Fun-CosyVoice3-0.5B-2512"
)

# Use project voices or CosyVoice default prompt
PROJECT_PROMPT_WAV = os.path.join(os.path.dirname(__file__), "voices", "male_haoran", "prompt.wav")
DEFAULT_PROMPT_WAV = os.path.join(cosyvoice_root, "asset", "zero_shot_prompt.wav")

OUTPUT_DIR = os.path.join(os.environ.get("TEMP", "/tmp"), "cosyvoice3_test")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_wav(speech_tensor, sample_rate, filename):
    """Save speech tensor to WAV file (16-bit PCM)."""
    path = os.path.join(OUTPUT_DIR, filename)
    speech_i16 = (speech_tensor * 32767.0).to(torch.int16)
    torchaudio.save(path, speech_i16, sample_rate, encoding="PCM_S", bits_per_sample=16)
    duration = speech_tensor.shape[1] / sample_rate
    print(f"  Saved: {path} ({duration:.1f}s, {os.path.getsize(path)} bytes)")
    return path


def check_prompt_wav(path):
    """Check prompt WAV properties."""
    if not os.path.exists(path):
        print(f"  NOT FOUND: {path}")
        return False
    waveform, sr = torchaudio.load(path)
    duration = waveform.shape[1] / sr
    print(f"  Prompt WAV: {path}")
    print(f"    Sample rate: {sr}, Channels: {waveform.shape[0]}, Duration: {duration:.2f}s")
    print(f"    Min: {waveform.min():.4f}, Max: {waveform.max():.4f}, RMS: {waveform.pow(2).mean().sqrt():.4f}")
    if duration < 0.5:
        print(f"    WARNING: Too short (< 0.5s)")
        return False
    if waveform.pow(2).mean().sqrt() < 0.001:
        print(f"    WARNING: Appears to be silence")
        return False
    return True


def main():
    print("=" * 60)
    print("CosyVoice3 Direct Test")
    print("=" * 60)

    # Check model
    print(f"\nModel dir: {MODEL_DIR}")
    yaml_path = os.path.join(MODEL_DIR, "cosyvoice3.yaml")
    if not os.path.exists(yaml_path):
        print(f"ERROR: cosyvoice3.yaml not found at {yaml_path}")
        return

    # Check prompt WAVs
    print("\n--- Checking prompt WAVs ---")
    has_project_prompt = check_prompt_wav(PROJECT_PROMPT_WAV)
    has_default_prompt = check_prompt_wav(DEFAULT_PROMPT_WAV)

    if not has_project_prompt and not has_default_prompt:
        print("ERROR: No valid prompt WAV found")
        return

    # Load model
    print(f"\n--- Loading CosyVoice3 model ---")
    t0 = time.time()
    fp16 = torch.cuda.is_available()
    cosyvoice = CosyVoice3(MODEL_DIR, fp16=fp16)
    print(f"  Model loaded in {time.time() - t0:.1f}s")
    print(f"  Sample rate: {cosyvoice.sample_rate}")
    print(f"  Available speakers: {cosyvoice.list_available_spks()}")

    tts_text = "收到好友从远方寄来的生日礼物，那份意外的惊喜与深深的祝福让我心中充满了甜蜜的快乐，笑容如花儿般绽放。"

    # ==========================================
    # Test 1: cross_lingual with DEFAULT prompt
    # (Exactly like official example.py)
    # ==========================================
    if has_default_prompt:
        print(f"\n--- Test 1: cross_lingual (default prompt, official format) ---")
        cross_lingual_text = f"You are a helpful assistant.<|endofprompt|>{tts_text}"
        print(f"  Text: {cross_lingual_text[:80]}...")
        t0 = time.time()
        chunks = []
        for i, output in enumerate(cosyvoice.inference_cross_lingual(
            cross_lingual_text,
            DEFAULT_PROMPT_WAV,
            stream=False
        )):
            chunks.append(output["tts_speech"])
            print(f"  Chunk {i}: shape={output['tts_speech'].shape}")
        speech = torch.cat(chunks, dim=1)
        print(f"  Inference time: {time.time() - t0:.1f}s")
        save_wav(speech, cosyvoice.sample_rate, "test1_cross_lingual_default.wav")

    # ==========================================
    # Test 2: zero_shot with DEFAULT prompt
    # (Exactly like official example.py)
    # ==========================================
    if has_default_prompt:
        print(f"\n--- Test 2: zero_shot (default prompt, official format) ---")
        prompt_text = "You are a helpful assistant.<|endofprompt|>希望你以后能够做的比我还好呦。"
        print(f"  TTS text: {tts_text[:60]}...")
        print(f"  Prompt text: {prompt_text}")
        t0 = time.time()
        chunks = []
        for i, output in enumerate(cosyvoice.inference_zero_shot(
            tts_text,
            prompt_text,
            DEFAULT_PROMPT_WAV,
            stream=False
        )):
            chunks.append(output["tts_speech"])
            print(f"  Chunk {i}: shape={output['tts_speech'].shape}")
        speech = torch.cat(chunks, dim=1)
        print(f"  Inference time: {time.time() - t0:.1f}s")
        save_wav(speech, cosyvoice.sample_rate, "test2_zero_shot_default.wav")

    # ==========================================
    # Test 3: cross_lingual with PROJECT prompt
    # ==========================================
    if has_project_prompt:
        print(f"\n--- Test 3: cross_lingual (project prompt: male_haoran) ---")
        cross_lingual_text = f"You are a helpful assistant.<|endofprompt|>{tts_text}"
        t0 = time.time()
        chunks = []
        for i, output in enumerate(cosyvoice.inference_cross_lingual(
            cross_lingual_text,
            PROJECT_PROMPT_WAV,
            stream=False
        )):
            chunks.append(output["tts_speech"])
            print(f"  Chunk {i}: shape={output['tts_speech'].shape}")
        speech = torch.cat(chunks, dim=1)
        print(f"  Inference time: {time.time() - t0:.1f}s")
        save_wav(speech, cosyvoice.sample_rate, "test3_cross_lingual_project.wav")

    # ==========================================
    # Test 4: zero_shot with PROJECT prompt
    # ==========================================
    if has_project_prompt:
        print(f"\n--- Test 4: zero_shot (project prompt: male_haoran) ---")
        prompt_text = "You are a helpful assistant.<|endofprompt|>大家好，我是浩然，很高兴为您服务。"
        print(f"  TTS text: {tts_text[:60]}...")
        print(f"  Prompt text: {prompt_text}")
        t0 = time.time()
        chunks = []
        for i, output in enumerate(cosyvoice.inference_zero_shot(
            tts_text,
            prompt_text,
            PROJECT_PROMPT_WAV,
            stream=False
        )):
            chunks.append(output["tts_speech"])
            print(f"  Chunk {i}: shape={output['tts_speech'].shape}")
        speech = torch.cat(chunks, dim=1)
        print(f"  Inference time: {time.time() - t0:.1f}s")
        save_wav(speech, cosyvoice.sample_rate, "test4_zero_shot_project.wav")

    # ==========================================
    # Test 5: instruct2 with PROJECT prompt
    # ==========================================
    if has_project_prompt:
        print(f"\n--- Test 5: instruct2 (project prompt: male_haoran) ---")
        instruct_text = "You are a helpful assistant. 用标准普通话朗读这段话。<|endofprompt|>"
        print(f"  TTS text: {tts_text[:60]}...")
        print(f"  Instruct text: {instruct_text}")
        t0 = time.time()
        chunks = []
        for i, output in enumerate(cosyvoice.inference_instruct2(
            tts_text,
            instruct_text,
            PROJECT_PROMPT_WAV,
            stream=False
        )):
            chunks.append(output["tts_speech"])
            print(f"  Chunk {i}: shape={output['tts_speech'].shape}")
        speech = torch.cat(chunks, dim=1)
        print(f"  Inference time: {time.time() - t0:.1f}s")
        save_wav(speech, cosyvoice.sample_rate, "test5_instruct2_project.wav")

    print(f"\n{'=' * 60}")
    print(f"All test files saved to: {OUTPUT_DIR}")
    print(f"Please listen to each WAV file and report which ones sound correct.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
