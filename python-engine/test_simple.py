import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.tts_engine import tts_engine

def main():
    print("=" * 60)
    print("Simple TTS Test")
    print("=" * 60)
    
    text = "今天天气真好，适合出去散步。"
    voice_id = "voice_male_01"
    
    try:
        print(f"Text: {text}")
        print(f"Voice ID: {voice_id}")
        
        output_path = tts_engine.synthesize(text, voice_id)
        print(f"\n✓ Success!")
        print(f"Output file: {output_path}")
        
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"File size: {size} bytes")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
