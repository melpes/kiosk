"""
TTS 기능 CLI 테스트 스크립트
실제 OpenAI TTS API를 사용하여 음성 파일 생성 테스트
"""

import os
import sys
import argparse
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.audio.tts_manager import TTSManager
from src.audio.tts_providers.base_tts import TTSError
from src.api.response_builder import ResponseBuilder
from src.logger import get_logger


def test_openai_tts_direct():
    """OpenAI TTS 직접 테스트"""
    print("=== OpenAI TTS 직접 테스트 ===")
    
    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        return False
    
    try:
        # TTS 관리자 생성
        manager = TTSManager(
            provider_name='openai',
            provider_config={
                'api_key': api_key,
                'model': 'tts-1',
                'voice': 'alloy',
                'speed': 1.0
            }
        )
        
        # 테스트 텍스트
        test_text = "안녕하세요! 음성 키오스크 시스템입니다. 주문을 도와드리겠습니다."
        
        print(f"📝 변환할 텍스트: {test_text}")
        print(f"💰 예상 비용: ${manager.estimate_cost(test_text):.6f}")
        
        # TTS 변환
        print("🔄 TTS 변환 중...")
        file_id = manager.text_to_speech(test_text)
        
        # 결과 확인
        file_path = manager.get_file_path(file_id)
        if file_path and Path(file_path).exists():
            file_size = Path(file_path).stat().st_size
            print(f"✅ TTS 변환 성공!")
            print(f"   파일 ID: {file_id}")
            print(f"   파일 경로: {file_path}")
            print(f"   파일 크기: {file_size:,} bytes")
            
            # 제공자 정보 출력
            provider_info = manager.get_provider_info()
            print(f"   제공자: {provider_info['provider']}")
            print(f"   모델: {provider_info.get('current_model', 'N/A')}")
            print(f"   음성: {provider_info.get('current_voice', 'N/A')}")
            
            return True
        else:
            print("❌ TTS 파일이 생성되지 않았습니다.")
            return False
            
    except TTSError as e:
        print(f"❌ TTS 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False


def test_response_builder_tts():
    """ResponseBuilder TTS 통합 테스트"""
    print("\n=== ResponseBuilder TTS 통합 테스트 ===")
    
    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        return False
    
    try:
        # ResponseBuilder 생성
        builder = ResponseBuilder(
            tts_provider='openai',
            tts_config={
                'api_key': api_key,
                'model': 'tts-1',
                'voice': 'nova',  # 다른 음성 사용
                'speed': 1.2
            }
        )
        
        # 테스트 메시지
        test_message = "주문이 완료되었습니다. 총 금액은 15,000원입니다. 결제를 진행해주세요."
        
        print(f"📝 응답 메시지: {test_message}")
        
        # 성공 응답 생성
        print("🔄 서버 응답 생성 중...")
        response = builder.build_success_response(
            message=test_message,
            session_id="test_session_123"
        )
        
        # 결과 확인
        if response.success and response.tts_audio_url:
            print(f"✅ 서버 응답 생성 성공!")
            print(f"   성공 여부: {response.success}")
            print(f"   메시지: {response.message}")
            print(f"   TTS URL: {response.tts_audio_url}")
            print(f"   세션 ID: {response.session_id}")
            
            # TTS 파일 확인
            file_id = response.tts_audio_url.split('/')[-1]
            file_path = builder.get_tts_file_path(file_id)
            if file_path and Path(file_path).exists():
                file_size = Path(file_path).stat().st_size
                print(f"   TTS 파일 크기: {file_size:,} bytes")
            
            # 제공자 정보 출력
            provider_info = builder.get_tts_provider_info()
            print(f"   TTS 제공자: {provider_info.get('provider', 'N/A')}")
            
            return True
        else:
            print("❌ 서버 응답 생성 실패")
            return False
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False


def test_tts_provider_switch():
    """TTS 제공자 교체 테스트"""
    print("\n=== TTS 제공자 교체 테스트 ===")
    
    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        return False
    
    try:
        # 초기 ResponseBuilder (폴백 모드)
        builder = ResponseBuilder(
            tts_provider='invalid_provider'  # 의도적으로 잘못된 제공자
        )
        
        print("📋 초기 제공자 정보:")
        initial_info = builder.get_tts_provider_info()
        print(f"   제공자: {initial_info.get('provider', 'N/A')}")
        
        # OpenAI로 교체
        print("🔄 OpenAI TTS로 제공자 교체 중...")
        builder.switch_tts_provider('openai', {
            'api_key': api_key,
            'model': 'tts-1',
            'voice': 'shimmer',
            'speed': 0.9
        })
        
        print("📋 교체 후 제공자 정보:")
        new_info = builder.get_tts_provider_info()
        print(f"   제공자: {new_info.get('provider', 'N/A')}")
        print(f"   모델: {new_info.get('current_model', 'N/A')}")
        print(f"   음성: {new_info.get('current_voice', 'N/A')}")
        
        # 교체된 제공자로 TTS 테스트
        test_message = "제공자가 성공적으로 교체되었습니다."
        response = builder.build_success_response(test_message)
        
        if response.success and response.tts_audio_url:
            print("✅ 제공자 교체 및 TTS 생성 성공!")
            return True
        else:
            print("❌ 교체된 제공자로 TTS 생성 실패")
            return False
            
    except Exception as e:
        print(f"❌ 제공자 교체 실패: {e}")
        return False


def test_multiple_voices():
    """다양한 음성으로 TTS 테스트"""
    print("\n=== 다양한 음성 TTS 테스트 ===")
    
    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        return False
    
    voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
    test_text = "각기 다른 음성으로 테스트합니다."
    
    success_count = 0
    
    for voice in voices:
        try:
            print(f"🎤 {voice} 음성으로 TTS 생성 중...")
            
            manager = TTSManager(
                provider_name='openai',
                provider_config={
                    'api_key': api_key,
                    'voice': voice
                }
            )
            
            file_id = manager.text_to_speech(test_text)
            file_path = manager.get_file_path(file_id)
            
            if file_path and Path(file_path).exists():
                file_size = Path(file_path).stat().st_size
                print(f"   ✅ {voice}: {file_size:,} bytes")
                success_count += 1
            else:
                print(f"   ❌ {voice}: 파일 생성 실패")
                
        except Exception as e:
            print(f"   ❌ {voice}: {e}")
    
    print(f"\n📊 결과: {success_count}/{len(voices)} 음성 성공")
    return success_count == len(voices)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="TTS 기능 CLI 테스트")
    parser.add_argument('--test', choices=['direct', 'builder', 'switch', 'voices', 'all'], 
                       default='all', help='실행할 테스트 선택')
    parser.add_argument('--verbose', action='store_true', help='상세 로그 출력')
    
    args = parser.parse_args()
    
    if args.verbose:
        # 로깅 레벨 설정
        import logging
        logging.basicConfig(level=logging.INFO)
    
    print("🎵 TTS 기능 CLI 테스트 시작")
    print("=" * 50)
    
    results = []
    
    if args.test in ['direct', 'all']:
        results.append(('OpenAI TTS 직접 테스트', test_openai_tts_direct()))
    
    if args.test in ['builder', 'all']:
        results.append(('ResponseBuilder TTS 테스트', test_response_builder_tts()))
    
    if args.test in ['switch', 'all']:
        results.append(('TTS 제공자 교체 테스트', test_tts_provider_switch()))
    
    if args.test in ['voices', 'all']:
        results.append(('다양한 음성 테스트', test_multiple_voices()))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    
    success_count = 0
    for test_name, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{test_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n전체 결과: {success_count}/{len(results)} 테스트 성공")
    
    if success_count == len(results):
        print("🎉 모든 테스트가 성공했습니다!")
        return 0
    else:
        print("⚠️  일부 테스트가 실패했습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(main())