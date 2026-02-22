#!/usr/bin/env python3
"""Debug script to check flow.inference output."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import torch
from src.core.tts_engine import tts_engine
from src.core.voice_config import get_voice_config

def test_flow_inference():
    """Test flow.inference directly."""
    print("=" * 60)
    print("Testing flow.inference directly")
    print("=" * 60)
    
    # Test text
    text = "今天天气真好，适合出去散步。"
    voice_id = "voice_male_01"
    
    # Get voice config
    config = get_voice_config(voice_id)
    
    # Load model
    tts_engine._ensure_model()
    
    # Prepare text
    tts_text = tts_engine._prepare_tts_text(text, min_token_len=300)
    
    # Extract tokens and features
    tts_text_token, tts_text_token_len = tts_engine._model.frontend._extract_text_token(tts_text)
    prompt_text_token, prompt_text_token_len = tts_engine._model.frontend._extract_text_token(config['prompt_text'])
    prompt_wav_path = tts_engine._resolve_prompt_path(config["prompt_wav"])
    speech_feat, speech_feat_len = tts_engine._model.frontend._extract_speech_feat(prompt_wav_path)
    
    print(f"TTS text token length: {tts_text_token_len.item()}")
    print(f"Prompt text token length: {prompt_text_token_len.item()}")
    print(f"Prompt speech feat length: {speech_feat_len.item()}")
    
    # Get model input using frontend_zero_shot to get proper embedding
    model_input = tts_engine._model.frontend.frontend_zero_shot(
        tts_text, config['prompt_text'], prompt_wav_path, tts_engine._model.sample_rate, ''
    )
    
    # Call flow.inference directly
    with torch.no_grad():
        feat, _ = tts_engine._model.model.flow.inference(
            token=model_input['text'].to(tts_engine._device, dtype=torch.int32),
            token_len=model_input['text_len'].to(tts_engine._device),
            prompt_token=model_input['prompt_text'].to(tts_engine._device, dtype=torch.int32),
            prompt_token_len=model_input['prompt_text_len'].to(tts_engine._device),
            prompt_feat=model_input['prompt_speech_feat'].to(tts_engine._device),
            prompt_feat_len=model_input['prompt_speech_feat_len'].to(tts_engine._device),
            embedding=model_input['flow_embedding'].to(tts_engine._device),
            streaming=False,
            finalize=True
        )
    
    print(f"Flow output feat shape: {feat.shape}")
    print(f"Flow output feat length: {feat.shape[2]} mel frames")
    
    # Calculate expected length
    token_len2 = tts_text_token_len.item()
    input_frame_rate = tts_engine._model.model.flow.input_frame_rate
    sample_rate = tts_engine._model.sample_rate
    expected_len = int(token_len2 / input_frame_rate * sample_rate / 256)
    print(f"Expected TTS mel length: {expected_len} frames")
    
    # Calculate audio length
    audio_samples = feat.shape[2] * 256  # assuming 256 samples per mel frame
    audio_duration = audio_samples / sample_rate
    print(f"Audio samples (from feat): {audio_samples}")
    print(f"Audio duration (from feat): {audio_duration:.2f} seconds")


if __name__ == "__main__":
    test_flow_inference()
