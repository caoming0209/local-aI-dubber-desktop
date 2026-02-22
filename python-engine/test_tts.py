#!/usr/bin/env python3
"""Test script to reproduce TTS error."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.tts_engine import tts_engine
from src.core.voice_config import get_voice_config

def test_tts():
    """Test TTS synthesis."""
    print("=" * 60)
    print("Testing TTS synthesis")
    print("=" * 60)
    
    # Test text - use different text from prompt_text
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
    
    # Test _prepare_tts_text
    print("\n" + "=" * 60)
    print("Testing _prepare_tts_text")
    print("=" * 60)
    
    try:
        tts_engine._ensure_model()
        print("Model loaded successfully")
        
        # Prepare text
        prepared_text = tts_engine._prepare_tts_text(text, min_token_len=300)
        print(f"\nPrepared text: {prepared_text[:100]}...")
        print(f"Prepared text length: {len(prepared_text)}")
        
        # Check token length
        _, token_len = tts_engine._model.frontend._extract_text_token(prepared_text)
        print(f"Token length: {token_len.item()}")
        
    except Exception as e:
        print(f"Error during text preparation: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test synthesis
    print("\n" + "=" * 60)
    print("Testing synthesis")
    print("=" * 60)
    
    try:
        output_path = tts_engine.synthesize(text, voice_id, min_token_len=300)
        print(f"\nSynthesis successful!")
        print(f"Output path: {output_path}")
        
        # Check output file
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"Output file size: {file_size} bytes")
        else:
            print("Output file not found!")
            
    except Exception as e:
        print(f"\nError during synthesis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tts()
