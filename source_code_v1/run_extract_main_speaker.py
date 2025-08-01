#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_main_speaker_speaking.py 실행 스크립트

사용법:
    python run_extract_main_speaker.py input_audio.wav output_audio.wav
    python run_extract_main_speaker.py input_audio.wav  # output은 자동으로 e_sample.wav
    python run_extract_main_speaker.py  # 기본 설정으로 실행
"""

import sys
import os
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="음성 파일에서 주요 화자 추출",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    %(prog)s input.wav output.wav          # 입력과 출력 파일 지정
    %(prog)s input.wav                     # 출력은 e_sample.wav로 자동 설정
    %(prog)s                              # 기본 설정으로 실행
    
참고:
    - 입력 파일은 16000Hz 모노 채널 WAV 파일이어야 합니다
    - GPU와 CUDA가 필요합니다
    - HuggingFace 토큰이 필요합니다 (환경변수 또는 소스 코드에 설정)
        """
    )
    
    parser.add_argument(
        'input_audio', 
        nargs='?',
        default='mixed_audio/2person_enhancedmix/wav/S00000332_0.84_S00190179_0.16_mixed_2.3.wav',
        help='입력 오디오 파일 경로 (기본값: mixed_audio/...)'
    )
    
    parser.add_argument(
        'output_audio',
        nargs='?', 
        default='sample.wav',
        help='출력 오디오 파일 경로 (기본값: sample.wav)'
    )
    
    parser.add_argument(
        '--token',
        help='HuggingFace 토큰 (환경변수가 우선)'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='테스트 모드: 시스템 확인만 수행'
    )
    
    args = parser.parse_args()
    
    # 테스트 모드
    if args.test:
        print("🔍 테스트 모드: 시스템 환경 확인")
        import test_extract_main_speaker
        tester = test_extract_main_speaker.ExtractMainSpeakerTester()
        tester.run_all_tests()
        return
    
    # 입력 파일 존재 확인
    input_path = Path(args.input_audio)
    if not input_path.exists():
        print(f"❌ 입력 파일이 존재하지 않습니다: {input_path}")
        print(f"📁 현재 디렉토리: {os.getcwd()}")
        return 1
    
    # 출력 디렉토리 생성
    output_path = Path(args.output_audio)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # extract_main_speaker 함수 임포트
        from src.utils.extract_main_speaker_speaking import extract_main_speaker
        
        print(f"🎵 입력 파일: {input_path}")
        print(f"💾 출력 파일: {output_path}")
        print("🚀 주요 화자 추출 시작...")
        
        # 함수 실행
        result_path = extract_main_speaker(
            audiodir=str(input_path),
            savedir=str(output_path),
            huggingface_token=args.token
        )
        
        print(f"✅ 처리 완료!")
        print(f"📄 결과 파일: {result_path}")
        
        # 결과 파일 정보
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            print(f"📊 파일 크기: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
        
        return 0
        
    except ImportError as e:
        print(f"❌ 모듈 임포트 실패: {e}")
        print("💡 src/utils/extract_main_speaker_speaking.py 파일이 존재하는지 확인하세요")
        return 1
        
    except Exception as e:
        print(f"❌ 처리 중 오류 발생: {e}")
        print("💡 다음을 확인해보세요:")
        print("  - GPU/CUDA 환경이 설정되었는지")
        print("  - HuggingFace 토큰이 올바른지")
        print("  - 입력 파일이 올바른 형식인지 (16000Hz 모노 WAV)")
        print("  - 필요한 라이브러리가 모두 설치되었는지")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)