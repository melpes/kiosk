"""
API 서버 테스트 스크립트
"""

import requests
import json
import time
from pathlib import Path
import sys

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_server_health(base_url: str = "http://localhost:8000"):
    """서버 헬스 체크 테스트"""
    try:
        print("🔍 서버 헬스 체크 중...")
        
        # 루트 엔드포인트 테스트
        response = requests.get(f"{base_url}/")
        print(f"✅ 루트 엔드포인트: {response.status_code}")
        print(f"   응답: {response.json()}")
        
        # 헬스 체크 엔드포인트 테스트
        response = requests.get(f"{base_url}/health")
        print(f"✅ 헬스 체크: {response.status_code}")
        print(f"   응답: {response.json()}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        return False
    except Exception as e:
        print(f"❌ 헬스 체크 실패: {e}")
        return False


def test_voice_processing(base_url: str = "http://localhost:8000", audio_file_path: str = None):
    """음성 처리 엔드포인트 테스트"""
    try:
        print("\n🎤 음성 처리 엔드포인트 테스트 중...")
        
        # 테스트용 더미 WAV 파일 생성
        if audio_file_path is None:
            audio_file_path = create_dummy_wav_file()
        
        if not Path(audio_file_path).exists():
            print(f"❌ 오디오 파일을 찾을 수 없습니다: {audio_file_path}")
            return False
        
        # 파일 업로드
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio_file': ('test.wav', audio_file, 'audio/wav')}
            data = {'session_id': 'test_session_123'}
            
            print(f"📤 파일 업로드 중: {audio_file_path}")
            response = requests.post(
                f"{base_url}/api/voice/process",
                files=files,
                data=data,
                timeout=30
            )
        
        print(f"📥 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 음성 처리 성공!")
            print(f"   성공 여부: {result.get('success')}")
            print(f"   메시지: {result.get('message')}")
            print(f"   처리 시간: {result.get('processing_time', 0):.2f}초")
            print(f"   세션 ID: {result.get('session_id')}")
            print(f"   TTS URL: {result.get('tts_audio_url')}")
            
            # UI 액션 정보
            ui_actions = result.get('ui_actions', [])
            if ui_actions:
                print(f"   UI 액션: {len(ui_actions)}개")
                for i, action in enumerate(ui_actions):
                    print(f"     {i+1}. {action.get('action_type')}")
            
            # 주문 데이터 정보
            order_data = result.get('order_data')
            if order_data:
                print(f"   주문 상태: {order_data.get('status')}")
                print(f"   주문 항목: {order_data.get('item_count', 0)}개")
                print(f"   총 금액: {order_data.get('total_amount', 0):,}원")
            
            return True
        else:
            print(f"❌ 음성 처리 실패: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   오류 내용: {error_detail}")
            except:
                print(f"   오류 내용: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 요청 타임아웃 (30초)")
        return False
    except Exception as e:
        print(f"❌ 음성 처리 테스트 실패: {e}")
        return False


def test_tts_download(base_url: str = "http://localhost:8000", file_id: str = None):
    """TTS 파일 다운로드 테스트"""
    try:
        print("\n🔊 TTS 파일 다운로드 테스트 중...")
        
        if file_id is None:
            print("⚠️ TTS 파일 ID가 제공되지 않았습니다. 더미 ID로 테스트합니다.")
            file_id = "dummy_file_id"
        
        response = requests.get(f"{base_url}/api/voice/tts/{file_id}")
        
        print(f"📥 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ TTS 파일 다운로드 성공!")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   파일 크기: {len(response.content)} bytes")
            return True
        elif response.status_code == 404:
            print("⚠️ TTS 파일을 찾을 수 없습니다 (예상된 결과)")
            return True
        else:
            print(f"❌ TTS 파일 다운로드 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ TTS 다운로드 테스트 실패: {e}")
        return False


def create_dummy_wav_file() -> str:
    """테스트용 더미 WAV 파일 생성"""
    import wave
    import struct
    import tempfile
    
    # 임시 파일 생성
    temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_file.close()
    
    # 더미 WAV 파일 생성 (1초간 무음)
    sample_rate = 16000
    duration = 1.0
    num_samples = int(sample_rate * duration)
    
    with wave.open(temp_file.name, 'w') as wav_file:
        wav_file.setnchannels(1)  # 모노
        wav_file.setsampwidth(2)  # 16비트
        wav_file.setframerate(sample_rate)
        
        # 무음 데이터 생성
        for _ in range(num_samples):
            wav_file.writeframes(struct.pack('<h', 0))
    
    print(f"📁 테스트용 더미 WAV 파일 생성: {temp_file.name}")
    return temp_file.name


def main():
    """메인 테스트 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="API 서버 테스트")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="서버 기본 URL (기본값: http://localhost:8000)"
    )
    parser.add_argument(
        "--audio-file",
        help="테스트할 오디오 파일 경로"
    )
    parser.add_argument(
        "--skip-voice",
        action="store_true",
        help="음성 처리 테스트 건너뛰기"
    )
    
    args = parser.parse_args()
    
    print("🧪 API 서버 테스트 시작")
    print(f"🌐 서버 URL: {args.base_url}")
    print("=" * 50)
    
    # 1. 헬스 체크
    if not test_server_health(args.base_url):
        print("\n❌ 서버 헬스 체크 실패. 테스트를 중단합니다.")
        return
    
    # 2. 음성 처리 테스트
    if not args.skip_voice:
        success = test_voice_processing(args.base_url, args.audio_file)
        if not success:
            print("\n⚠️ 음성 처리 테스트 실패")
    
    # 3. TTS 다운로드 테스트
    test_tts_download(args.base_url)
    
    print("\n" + "=" * 50)
    print("✅ API 서버 테스트 완료")
    print("\n💡 서버를 시작하려면:")
    print("   python -m src.api.cli --debug")
    print("\n💡 실제 음성 파일로 테스트하려면:")
    print(f"   python -m src.api.test_server --audio-file your_audio.wav")


if __name__ == "__main__":
    main()