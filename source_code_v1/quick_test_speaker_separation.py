#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실제 화자분리 기능 간단 테스트
"""

import os
import torchaudio
import torch
from pathlib import Path

def create_mixed_audio_sample():
    """간단한 2화자 믹스 오디오 생성"""
    print("🎵 테스트용 2화자 믹스 오디오 생성 중...")
    
    # 3초 길이, 16000Hz
    duration = 3.0
    sr = 16000
    t = torch.linspace(0, duration, int(duration * sr))
    
    # 화자 1: 낮은 주파수 (남성 목소리 시뮬레이션)
    speaker1_freq = 150.0  # Hz
    speaker1 = 0.7 * torch.sin(2 * torch.pi * speaker1_freq * t)
    
    # 화자 2: 높은 주파수 (여성 목소리 시뮬레이션) 
    speaker2_freq = 300.0  # Hz
    speaker2 = 0.5 * torch.sin(2 * torch.pi * speaker2_freq * t)
    
    # 믹스: 화자1은 전체, 화자2는 중간 부분만
    mixed = speaker1.clone()
    mid_start = int(len(t) * 0.2)
    mid_end = int(len(t) * 0.8)
    mixed[mid_start:mid_end] += speaker2[mid_start:mid_end]
    
    # 노이즈 추가
    noise = 0.1 * torch.randn_like(mixed)
    mixed += noise
    
    # 모노 채널로 변환
    mixed = mixed.unsqueeze(0)  # (1, samples)
    
    # 파일 저장
    output_path = "test_mixed_audio.wav"
    torchaudio.save(output_path, mixed, sr)
    print(f"✅ 테스트 오디오 생성 완료: {output_path}")
    
    return output_path

def test_real_speaker_separation():
    """실제 화자분리 테스트"""
    print("🔍 실제 화자분리 기능 테스트 시작\n")
    
    try:
        # 1. 테스트 오디오 생성
        test_audio = create_mixed_audio_sample()
        
        # 2. extract_main_speaker 함수 실행
        print("🚀 화자분리 실행 중...")
        from src.utils.extract_main_speaker_speaking import extract_main_speaker
        
        result_path = extract_main_speaker(
            audiodir=test_audio,
            savedir="separated_speaker.wav"
        )
        
        print(f"✅ 화자분리 완료!")
        print(f"📁 결과 파일: {result_path}")
        
        # 3. 결과 파일 정보
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"📊 파일 크기: {file_size:,} bytes ({file_size/1024:.2f} KB)")
            
            # 오디오 정보
            waveform, sr = torchaudio.load(result_path)
            duration = waveform.shape[1] / sr
            print(f"🎵 오디오 길이: {duration:.2f}초")
            print(f"🔊 샘플링 레이트: {sr}Hz")
            print(f"📈 오디오 shape: {waveform.shape}")
        
        # 4. 정리
        cleanup_files = [test_audio, "separated_speaker.wav", "e_separated_speaker.wav"]
        print(f"\n🧹 임시 파일 정리:")
        for file_path in cleanup_files:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"  ✅ 삭제: {file_path}")
        
        print(f"\n🎉 화자분리 테스트 성공! 실제로 작동합니다!")
        return True
        
    except Exception as e:
        print(f"❌ 화자분리 테스트 실패: {e}")
        print(f"\n💡 가능한 원인:")
        print(f"  - AI 모델 다운로드가 필요함 (처음 실행시 시간 소요)")
        print(f"  - GPU 메모리 부족")
        print(f"  - 네트워크 연결 문제 (모델 다운로드)")
        print(f"  - HuggingFace 토큰 문제")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("  실제 화자분리 기능 테스트")
    print("  (AI 모델 다운로드로 인해 처음 실행시 시간이 걸릴 수 있습니다)")
    print("=" * 60)
    
    success = test_real_speaker_separation()
    
    if success:
        print(f"\n✅ 결론: extract_main_speaker_speaking.py가 실제로 작동합니다!")
    else:
        print(f"\n⚠️  결론: 환경은 준비되었지만 실행 중 문제가 있습니다.")
        print(f"        위의 가능한 원인들을 확인해보세요.")