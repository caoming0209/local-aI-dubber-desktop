#!/usr/bin/env python3
"""Debug script to check TTS internals."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import torch
from src.core.tts_engine import tts_engine
from src.core.voice_config import get_voice_config

def test_debug():
    """Test TTS synthesis with debug info."""
    print("=" * 60)
    print("Testing TTS synthesis with debug info")
    print("=" * 60)
    
    # Test text
    text = "今天天气真好，适合出去散步。"
    voice_id = "voice_male_01"
    
    print(f"\nText: {text}")
    print(f"Voice ID: {voice_id}")
    
    # Get voice config
    config = get_voice_config(voice_id)
    print(f"\nVoice config:")
    print(f"  Name: {config['name']}")
    print(f"  Mode: {config['mode']}")
    print(f"  Prompt WAV: {config['prompt_wav']}")
    print(f"  Prompt text: {config['prompt_text']}")
    
    # Load model
    tts_engine._ensure_model()
    print("\nModel loaded successfully")
    
    # Prepare text
    tts_text = tts_engine._prepare_tts_text(text, min_token_len=300)
    print(f"\nPrepared text: {tts_text[:100]}...")
    
    # Check token length
    _, token_len = tts_engine._model.frontend._extract_text_token(tts_text)
    print(f"Token length: {token_len.item()}")
    
    # Check prompt_wav
    prompt_wav_path = tts_engine._resolve_prompt_path(config["prompt_wav"])
    print(f"\nPrompt WAV path: {prompt_wav_path}")
    
    # Load prompt_wav and check its length
    import torchaudio
    prompt_wav, sample_rate = torchaudio.load(prompt_wav_path)
    print(f"Prompt WAV shape: {prompt_wav.shape}")
    print(f"Prompt WAV duration: {prompt_wav.shape[1] / sample_rate:.2f} seconds")
    print(f"Prompt WAV sample rate: {sample_rate} Hz")
    
    # Check model sample rate
    print(f"\nModel sample rate: {tts_engine._model.sample_rate}")
    
    # Check input_frame_rate
    print(f"Model flow input_frame_rate: {tts_engine._model.model.flow.input_frame_rate}")
    print(f"Model flow token_mel_ratio: {tts_engine._model.model.flow.token_mel_ratio}")
    
    # Calculate expected mel length
    token_count = int(token_len.item())
    input_frame_rate = tts_engine._model.model.flow.input_frame_rate
    sample_rate = tts_engine._model.sample_rate
    
    # mel_len = token_count / input_frame_rate * sample_rate / 256
    expected_mel_len = int(token_count / input_frame_rate * sample_rate / 256)
    print(f"\nExpected mel length: {expected_mel_len} frames")
    print(f"Expected audio duration: {expected_mel_len * 256 / sample_rate:.2f} seconds")
    
    # Check prompt_feat length
    from cosyvoice.cli.frontend import CosyVoiceFrontEnd
    speech_feat, speech_feat_len = tts_engine._model.frontend._extract_speech_feat(prompt_wav_path)
    print(f"\nPrompt speech_feat shape: {speech_feat.shape}")
    print(f"Prompt speech_feat length: {speech_feat_len.item()} frames")
    print(f"Prompt speech_feat duration: {int(speech_feat_len.item()) * 256 / sample_rate:.2f} seconds")
    
    # Check hift upsample_rates
    print(f"\nHift upsample_rates: {tts_engine._model.model.hift.upsample_rates}")
    total_upsample = 1
    for rate in tts_engine._model.model.hift.upsample_rates:
        total_upsample *= rate
    print(f"Total upsample rate: {total_upsample}")
    
    # Check if the issue is with token_mel_ratio
    print(f"\nActual mel length calculation:")
    print(f"  token_len2: {token_count}")
    print(f"  input_frame_rate: {input_frame_rate}")
    print(f"  sample_rate: {sample_rate}")
    print(f"  mel_len2 = token_len2 / input_frame_rate * sample_rate / 256")
    print(f"  mel_len2 = {token_count} / {input_frame_rate} * {sample_rate} / 256")
    print(f"  mel_len2 = {token_count / input_frame_rate} * {sample_rate / 256:.2f}")
    print(f"  mel_len2 = {token_count / input_frame_rate * sample_rate / 256:.2f}")
    print(f"  mel_len2 (int) = {int(token_count / input_frame_rate * sample_rate / 256)}")
    
    # Check if the issue is with prompt_feat
    print(f"\nPrompt feat calculation:")
    print(f"  mel_len1: {int(speech_feat_len.item())}")
    print(f"  mel_len1 + mel_len2: {int(speech_feat_len.item()) + int(token_count / input_frame_rate * 22050 / 256)}")
    print(f"  Expected audio duration: {(int(speech_feat_len.item()) + int(token_count / input_frame_rate * 22050 / 256)) * 256 / sample_rate:.2f} seconds")

if __name__ == "__main__":
    test_debug()
