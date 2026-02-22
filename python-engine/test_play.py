#!/usr/bin/env python3
"""Test script to play and analyze TTS output."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import torch
import torchaudio

def analyze_audio(path):
    """Analyze audio file."""
    print(f"\nAnalyzing: {path}")
    print("=" * 60)
    
    # Load audio
    waveform, sample_rate = torchaudio.load(path)
    
    print(f"Sample rate: {sample_rate} Hz")
    print(f"Duration: {waveform.shape[1] / sample_rate:.2f} seconds")
    print(f"Channels: {waveform.shape[0]}")
    print(f"Samples: {waveform.shape[1]}")
    print(f"Data type: {waveform.dtype}")
    print(f"Min value: {waveform.min().item():.4f}")
    print(f"Max value: {waveform.max().item():.4f}")
    print(f"Mean value: {waveform.mean().item():.4f}")
    
    # Check if audio is mostly silent
    if waveform.abs().max() < 0.01:
        print("WARNING: Audio is mostly silent!")
    
    # Check if audio has valid content
    if waveform.abs().max() > 1.0:
        print("WARNING: Audio has clipping!")
    
    print("=" * 60)

if __name__ == "__main__":
    # Analyze the latest generated file
    import glob
    import os
    
    temp_dir = os.path.join(os.environ.get("TEMP", "/tmp"), "zhiying_tts")
    wav_files = glob.glob(os.path.join(temp_dir, "tts_*.wav"))
    
    if wav_files:
        # Get the most recent file
        latest_file = max(wav_files, key=os.path.getmtime)
        analyze_audio(latest_file)
    else:
        print("No WAV files found in temp directory")
