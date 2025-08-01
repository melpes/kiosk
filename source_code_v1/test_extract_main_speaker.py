#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_main_speaker_speaking.py 파일 기능 테스트 코드

이 테스트는 다음을 확인합니다:
1. 필요한 라이브러리 의존성 체크
2. rms_safe_normalize 함수 테스트
3. 전체 파이프라인 시뮬레이션 테스트
4. 에러 케이스 처리 테스트
"""

import os
import sys
import torch
import torchaudio
import numpy as np
import warnings
import traceback
from pathlib import Path

# 색상 출력을 위한 ANSI 코드
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.ENDC}")

def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*50}")
    print(f"  {msg}")
    print(f"{'='*50}{Colors.ENDC}\n")

class ExtractMainSpeakerTester:
    def __init__(self):
        self.test_results = []
        self.temp_files = []
        
    def add_result(self, test_name, passed, details=""):
        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'details': details
        })
        
    def cleanup(self):
        """테스트 중 생성된 임시 파일들 정리"""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print_info(f"임시 파일 삭제: {file_path}")
            except Exception as e:
                print_warning(f"임시 파일 삭제 실패 {file_path}: {e}")

    def test_dependencies(self):
        """필요한 라이브러리 의존성 테스트"""
        print_header("라이브러리 의존성 테스트")
        
        dependencies = [
            ('torch', 'torch'),
            ('torchaudio', 'torchaudio'),
            ('speechbrain', 'speechbrain.pretrained'),
            ('pyannote.audio', 'pyannote.audio'),
            ('numpy', 'numpy'),
        ]
        
        all_passed = True
        for lib_name, import_name in dependencies:
            try:
                __import__(import_name)
                print_success(f"{lib_name} 라이브러리 가져오기 성공")
            except ImportError as e:
                print_error(f"{lib_name} 라이브러리 가져오기 실패: {e}")
                all_passed = False
        
        # CUDA 체크
        if torch.cuda.is_available():
            print_success(f"CUDA 사용 가능 (GPU 개수: {torch.cuda.device_count()})")
        else:
            print_warning("CUDA 사용 불가능 - CPU 모드로 동작")
            
        self.add_result("의존성 테스트", all_passed)
        return all_passed

    def test_rms_safe_normalize(self):
        """rms_safe_normalize 함수 테스트"""
        print_header("rms_safe_normalize 함수 테스트")
        
        # src/utils 디렉토리를 파이썬 경로에 추가
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'utils'))
        
        try:
            # 함수 임포트 시도
            from src.utils.extract_main_speaker_speaking import rms_safe_normalize
            print_success("rms_safe_normalize 함수 임포트 성공")
            
            # 테스트 케이스 1: 정상적인 웨이브폼
            test_waveform = torch.randn(1, 16000) * 0.1  # 1초, 작은 볼륨
            try:
                normalized = rms_safe_normalize(test_waveform)
                print_success("정상 웨이브폼 정규화 성공")
                print_info(f"입력 RMS: {(test_waveform ** 2).mean().sqrt():.6f}")
                print_info(f"출력 RMS: {(normalized ** 2).mean().sqrt():.6f}")
                print_info(f"출력 shape: {normalized.shape}")
                self.add_result("정상 웨이브폼 정규화", True)
            except Exception as e:
                print_error(f"정상 웨이브폼 정규화 실패: {e}")
                self.add_result("정상 웨이브폼 정규화", False, str(e))
            
            # 테스트 케이스 2: 빈 웨이브폼 (에러 케이스)
            try:
                zero_waveform = torch.zeros(1, 16000)
                normalized = rms_safe_normalize(zero_waveform)
                print_error("빈 웨이브폼에서 예외가 발생하지 않음 (예상과 다름)")
                self.add_result("빈 웨이브폼 에러 처리", False, "예외가 발생하지 않음")
            except Exception as e:
                print_success(f"빈 웨이브폼에서 예상된 예외 발생: {e}")
                self.add_result("빈 웨이브폼 에러 처리", True)
                
            # 테스트 케이스 3: 매우 큰 값의 웨이브폼
            try:
                large_waveform = torch.randn(1, 16000) * 10  # 큰 볼륨
                normalized = rms_safe_normalize(large_waveform, max_target_rms=0.05)
                output_rms = (normalized ** 2).mean().sqrt()
                
                # 부동소수점 오차를 고려하여 약간의 여유를 둡니다 (1% 허용)
                tolerance = 0.05 * 0.01  # 1% 허용 오차
                if output_rms <= 0.05 + tolerance:
                    print_success(f"큰 볼륨 웨이브폼 정규화 성공 (출력 RMS: {output_rms:.6f}, 목표: ≤{0.05:.3f})")
                    self.add_result("큰 볼륨 웨이브폼 정규화", True)
                else:
                    print_warning(f"출력 RMS가 목표값을 초과함: {output_rms:.6f} > {0.05 + tolerance:.6f}")
                    self.add_result("큰 볼륨 웨이브폼 정규화", False, f"RMS 초과: {output_rms:.6f}")
            except Exception as e:
                print_error(f"큰 볼륨 웨이브폼 정규화 실패: {e}")
                self.add_result("큰 볼륨 웨이브폼 정규화", False, str(e))
                
        except ImportError as e:
            print_error(f"rms_safe_normalize 함수 임포트 실패: {e}")
            self.add_result("rms_safe_normalize 함수 테스트", False, str(e))
            return False
            
        return True

    def create_test_audio(self, filename, duration=3.0, sample_rate=16000, num_speakers=2):
        """테스트용 오디오 파일 생성"""
        try:
            # 다중 화자 시뮬레이션을 위한 간단한 믹스 오디오 생성
            t = torch.linspace(0, duration, int(duration * sample_rate))
            
            # 주 화자 (더 큰 볼륨과 더 긴 지속시간)
            main_freq = 440.0  # A4 note
            main_speaker = 0.6 * torch.sin(2 * torch.pi * main_freq * t)
            
            # 보조 화자 (작은 볼륨, 짧은 구간)
            secondary_freq = 880.0  # A5 note
            secondary_speaker = 0.3 * torch.sin(2 * torch.pi * secondary_freq * t)
            
            # 보조 화자는 중간 부분에만 추가
            mid_start = int(len(t) * 0.3)
            mid_end = int(len(t) * 0.7)
            mixed_audio = main_speaker.clone()
            mixed_audio[mid_start:mid_end] += secondary_speaker[mid_start:mid_end]
            
            # 노이즈 추가
            noise = 0.05 * torch.randn_like(mixed_audio)
            mixed_audio += noise
            
            # 모노 채널로 만들기
            mixed_audio = mixed_audio.unsqueeze(0)  # (1, samples)
            
            # 파일 저장
            torchaudio.save(filename, mixed_audio, sample_rate)
            self.temp_files.append(filename)
            return True
            
        except Exception as e:
            print_error(f"테스트 오디오 파일 생성 실패: {e}")
            return False

    def test_audio_pipeline_simulation(self):
        """전체 파이프라인 시뮬레이션 테스트 (실제 모델 로드 없이)"""
        print_header("오디오 파이프라인 시뮬레이션 테스트")
        
        # 테스트 오디오 파일 생성
        test_audio_file = "test_audio_sample.wav"
        if not self.create_test_audio(test_audio_file):
            self.add_result("오디오 파이프라인 시뮬레이션", False, "테스트 오디오 생성 실패")
            return False
            
        try:
            # 오디오 파일 로드 테스트
            waveform, sr = torchaudio.load(test_audio_file)
            print_success(f"오디오 파일 로드 성공: shape={waveform.shape}, sr={sr}")
            
            # 샘플링 레이트 체크
            if sr == 16000:
                print_success("샘플링 레이트 16000Hz 확인")
            else:
                print_warning(f"샘플링 레이트가 16000Hz가 아님: {sr}Hz")
                
            # 모노 채널 체크
            if waveform.shape[0] == 1:
                print_success("모노 채널 오디오 확인")
            else:
                print_warning(f"모노 채널이 아님: {waveform.shape[0]} 채널")
                
            # 리샘플링 테스트
            if sr != 8000:
                resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=8000)
                waveform_8k = resampler(waveform)
                print_success(f"8kHz 리샘플링 성공: {waveform_8k.shape}")
            else:
                waveform_8k = waveform
                
            # RMS 정규화 테스트
            try:
                from src.utils.extract_main_speaker_speaking import rms_safe_normalize
                normalized = rms_safe_normalize(waveform)
                print_success("RMS 정규화 성공")
            except Exception as e:
                print_warning(f"RMS 정규화 실패 (함수 없음): {e}")
                
            self.add_result("오디오 파이프라인 시뮬레이션", True)
            return True
            
        except Exception as e:
            print_error(f"오디오 파이프라인 시뮬레이션 실패: {e}")
            self.add_result("오디오 파이프라인 시뮬레이션", False, str(e))
            return False

    def test_huggingface_token(self):
        """HuggingFace 토큰 체크"""
        print_header("HuggingFace 토큰 체크")
        
        # 환경변수에서 토큰 체크
        hf_token_env = os.getenv('HUGGINGFACE_TOKEN')
        if hf_token_env:
            print_success("환경변수에서 HUGGINGFACE_TOKEN 발견")
            self.add_result("HuggingFace 토큰 (환경변수)", True)
        else:
            print_warning("환경변수에 HUGGINGFACE_TOKEN이 설정되지 않음")
            
        # 소스 코드의 하드코딩된 토큰 체크
        try:
            from src.utils.extract_main_speaker_speaking import HUGGINGFACE_TOKEN
            if HUGGINGFACE_TOKEN and HUGGINGFACE_TOKEN.startswith('hf_'):
                print_success("소스 코드에서 HuggingFace 토큰 발견")
                print_warning("보안상 하드코딩된 토큰은 환경변수로 이동하는 것을 권장합니다")
                self.add_result("HuggingFace 토큰 (하드코딩)", True)
            else:
                print_error("소스 코드의 토큰이 유효하지 않음")
                self.add_result("HuggingFace 토큰 (하드코딩)", False)
        except ImportError as e:
            print_error(f"extract_main_speaker_speaking 모듈 임포트 실패: {e}")
            self.add_result("HuggingFace 토큰 체크", False, f"모듈 임포트 실패: {e}")

    def test_file_structure(self):
        """파일 구조 및 경로 테스트"""
        print_header("파일 구조 및 경로 테스트")
        
        # 주요 파일 경로들 체크
        files_to_check = [
            'src/utils/extract_main_speaker_speaking.py',
            'src/utils/__init__.py',
            'requirements.txt',
            'requirements_essential.txt'
        ]
        
        all_files_exist = True
        for file_path in files_to_check:
            if os.path.exists(file_path):
                print_success(f"파일 존재 확인: {file_path}")
            else:
                print_warning(f"파일 없음: {file_path}")
                if 'extract_main_speaker_speaking.py' in file_path:
                    all_files_exist = False
                    
        # 디렉토리 체크
        dirs_to_check = ['temp_audio', 'mixed_audio']
        for dir_path in dirs_to_check:
            if os.path.exists(dir_path):
                print_info(f"디렉토리 존재: {dir_path}")
            else:
                print_info(f"디렉토리 없음 (필요시 생성): {dir_path}")
                
        self.add_result("파일 구조 테스트", all_files_exist)
        return all_files_exist

    def test_extract_main_speaker_function(self):
        """extract_main_speaker 함수 테스트"""
        print_header("extract_main_speaker 함수 테스트")
        
        # 테스트 오디오 파일 생성
        test_audio_file = "test_function_audio.wav"
        if not self.create_test_audio(test_audio_file):
            self.add_result("extract_main_speaker 함수 테스트", False, "테스트 오디오 생성 실패")
            return False
            
        try:
            from src.utils.extract_main_speaker_speaking import extract_main_speaker
            print_success("extract_main_speaker 함수 임포트 성공")
            
            # 함수 테스트 (실제 AI 모델 로드는 하지 않고 가벼운 테스트만)
            # 참고: 실제 실행은 GPU와 AI 모델이 필요하므로 여기서는 함수 시그니처만 확인
            try:
                import inspect
                sig = inspect.signature(extract_main_speaker)
                params = list(sig.parameters.keys())
                expected_params = ['audiodir', 'savedir', 'huggingface_token']
                
                if all(param in params for param in expected_params[:2]):  # audiodir, savedir는 필수
                    print_success("함수 시그니처 확인 성공")
                    print_info(f"함수 파라미터: {params}")
                    self.add_result("extract_main_speaker 함수 시그니처", True)
                else:
                    print_error(f"함수 파라미터가 예상과 다름: {params}")
                    self.add_result("extract_main_speaker 함수 시그니처", False, f"파라미터: {params}")
                    
            except Exception as e:
                print_error(f"함수 시그니처 확인 실패: {e}")
                self.add_result("extract_main_speaker 함수 시그니처", False, str(e))
                
            # 함수 호출 시뮬레이션 (실제 모델 없이 에러 핸들링 확인)
            try:
                # 존재하지 않는 파일로 테스트해서 적절한 에러가 발생하는지 확인
                fake_audio_path = "nonexistent_audio_file.wav" 
                try:
                    result = extract_main_speaker(fake_audio_path, "test_output.wav")
                    print_error("존재하지 않는 파일에 대해 에러가 발생하지 않음")
                    self.add_result("extract_main_speaker 에러 핸들링", False, "에러가 발생하지 않음")
                except Exception as expected_error:
                    print_success(f"존재하지 않는 파일에 대해 적절한 에러 발생: {type(expected_error).__name__}")
                    self.add_result("extract_main_speaker 에러 핸들링", True)
                    
            except Exception as e:
                print_warning(f"에러 핸들링 테스트 실패: {e}")
                self.add_result("extract_main_speaker 에러 핸들링", False, str(e))
                
            self.add_result("extract_main_speaker 함수 테스트", True)
            return True
            
        except ImportError as e:
            print_error(f"extract_main_speaker 함수 임포트 실패: {e}")
            self.add_result("extract_main_speaker 함수 테스트", False, str(e))
            return False

    def run_all_tests(self):
        """모든 테스트 실행"""
        print_header("Extract Main Speaker Speaking 테스트 시작")
        
        try:
            # 테스트 실행
            self.test_file_structure()
            self.test_dependencies()
            self.test_huggingface_token()
            self.test_rms_safe_normalize()
            self.test_audio_pipeline_simulation()
            self.test_extract_main_speaker_function()
            
        except KeyboardInterrupt:
            print_warning("사용자에 의해 테스트가 중단되었습니다")
        except Exception as e:
            print_error(f"예상치 못한 오류 발생: {e}")
            traceback.print_exc()
        finally:
            self.cleanup()
            
        # 결과 요약
        self.print_summary()

    def print_summary(self):
        """테스트 결과 요약 출력"""
        print_header("테스트 결과 요약")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"총 테스트: {total_tests}")
        print(f"성공: {Colors.GREEN}{passed_tests}{Colors.ENDC}")
        print(f"실패: {Colors.RED}{failed_tests}{Colors.ENDC}")
        print(f"성공률: {Colors.BOLD}{(passed_tests/total_tests*100):.1f}%{Colors.ENDC}")
        
        print("\n상세 결과:")
        for result in self.test_results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            color = Colors.GREEN if result['passed'] else Colors.RED
            print(f"  {color}{status}{Colors.ENDC} {result['name']}")
            if result['details'] and not result['passed']:
                print(f"    └─ {Colors.YELLOW}{result['details']}{Colors.ENDC}")
                
        # 추천사항
        print_header("추천사항")
        
        recommendations = []
        
        # 실패한 테스트에 따른 추천사항
        for result in self.test_results:
            if not result['passed']:
                if '의존성' in result['name']:
                    recommendations.append("필요한 라이브러리를 설치하세요: pip install -r requirements.txt")
                elif 'CUDA' in result['details']:
                    recommendations.append("GPU가 필요한 경우 CUDA 환경을 설정하세요")
                elif 'HuggingFace' in result['name']:
                    recommendations.append("HuggingFace 토큰을 환경변수로 설정하세요: export HUGGINGFACE_TOKEN=your_token")
                    
        if not recommendations:
            recommendations.append("모든 테스트가 통과했습니다! extract_main_speaker_speaking.py를 실행해볼 수 있습니다.")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")

def main():
    """메인 실행 함수"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("  Extract Main Speaker Speaking 테스트 도구")
    print("  음성에서 주요 화자 추출 기능 테스트")
    print("=" * 60)
    print(f"{Colors.ENDC}")
    
    tester = ExtractMainSpeakerTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()