"""
기본 클라이언트 사용 예제
"""

import sys
from pathlib import Path

# 패키지 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from client import VoiceClient, ConfigManager, KioskUIManager
from utils.logger import setup_logging, get_logger


def basic_client_example():
    """기본 클라이언트 사용 예제"""
    print("🎤 기본 클라이언트 예제")
    print("=" * 50)
    
    # 1. 설정 로드
    config_path = Path(__file__).parent.parent / "config.json"
    config = ConfigManager.load_config(str(config_path))
    
    # 2. 로깅 설정
    setup_logging(
        log_level=config.logging.level,
        log_file=config.logging.file
    )
    
    logger = get_logger(__name__)
    logger.info("기본 클라이언트 예제 시작")
    
    # 3. 클라이언트 생성
    client = VoiceClient(config)
    ui_manager = KioskUIManager(client)
    
    try:
        # 4. 서버 상태 확인
        print("\n1. 서버 상태 확인...")
        if not client.check_server_health():
            print("❌ 서버에 연결할 수 없습니다.")
            return
        print("✅ 서버 연결 정상")
        
        # 5. 테스트 음성 파일 찾기
        test_files = find_test_audio_files()
        if not test_files:
            print("❌ 테스트용 음성 파일을 찾을 수 없습니다.")
            print("💡 프로젝트 루트에 .wav 파일을 추가해주세요.")
            return
        
        print(f"\n2. 테스트 파일 발견: {test_files[0]}")
        
        # 6. 음성 파일 전송
        print("\n3. 음성 파일 전송...")
        response = client.send_audio_file(test_files[0])
        
        # 7. 응답 처리
        print("\n4. 응답 처리...")
        ui_manager.handle_response(response)
        
        # 8. 결과 확인
        print("\n5. 처리 결과:")
        if response.success:
            print("✅ 성공적으로 처리되었습니다.")
            
            # 현재 상태 표시
            ui_manager.show_status()
        else:
            print("❌ 처리 중 오류가 발생했습니다.")
        
    except Exception as e:
        logger.error(f"예제 실행 중 오류: {e}")
        print(f"❌ 오류 발생: {e}")
    
    finally:
        # 9. 정리
        client.close()
        print("\n🎉 예제 완료!")


def find_test_audio_files():
    """테스트용 음성 파일 찾기"""
    test_files = []
    
    # 프로젝트 루트에서 .wav 파일 찾기
    project_root = Path(__file__).parent.parent.parent
    
    # 루트 디렉토리의 .wav 파일들
    for wav_file in project_root.glob("*.wav"):
        test_files.append(str(wav_file))
    
    # examples/test_audio 디렉토리
    test_audio_dir = Path(__file__).parent / "test_audio"
    if test_audio_dir.exists():
        for wav_file in test_audio_dir.glob("*.wav"):
            test_files.append(str(wav_file))
    
    return sorted(test_files)[:1]  # 첫 번째 파일만


if __name__ == "__main__":
    basic_client_example()