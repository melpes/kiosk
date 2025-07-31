"""
설정 관리 시스템 데모
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import ConfigManager
from src.utils.config_utils import (
    setup_initial_config,
    validate_api_key,
    get_config_file_info,
    validate_json_file
)


def demo_config_management():
    """설정 관리 시스템 데모"""
    print("=== 설정 관리 시스템 데모 ===\n")
    
    # 1. 초기 설정 수행
    print("1. 초기 설정 수행")
    setup_initial_config()
    print("✓ 초기 설정 완료\n")
    
    # 2. ConfigManager 초기화
    print("2. ConfigManager 초기화")
    config_manager = ConfigManager()
    print("✓ ConfigManager 초기화 완료\n")
    
    # 3. 설정 파일 정보 확인
    print("3. 설정 파일 정보 확인")
    env_file_info = get_config_file_info(".env")
    menu_file_info = get_config_file_info("config/menu_config.json")
    
    print(f"환경 변수 파일 (.env):")
    print(f"  - 존재: {env_file_info['exists']}")
    print(f"  - 크기: {env_file_info.get('size', 0)} bytes")
    print(f"  - 읽기 가능: {env_file_info.get('readable', False)}")
    print(f"  - 쓰기 가능: {env_file_info.get('writable', False)}")
    
    print(f"메뉴 설정 파일:")
    print(f"  - 존재: {menu_file_info['exists']}")
    print(f"  - 크기: {menu_file_info.get('size', 0)} bytes")
    print(f"  - 읽기 가능: {menu_file_info.get('readable', False)}")
    print(f"  - 쓰기 가능: {menu_file_info.get('writable', False)}")
    print()
    
    # 4. JSON 파일 유효성 검증
    print("4. JSON 파일 유효성 검증")
    menu_validation = validate_json_file("config/menu_config.json")
    
    print(f"메뉴 설정 파일 유효성: {menu_validation['valid']}")
    if not menu_validation['valid']:
        print(f"  오류: {menu_validation.get('error')}")
    print()
    
    # 5. 설정 로드 및 표시
    print("5. 설정 로드 및 표시")
    try:
        # API 설정 로드
        api_config = config_manager.load_api_config()
        print(f"API 설정:")
        print(f"  - 모델: {api_config.model}")
        print(f"  - 최대 토큰: {api_config.max_tokens}")
        print(f"  - 온도: {api_config.temperature}")
        print(f"  - API 키 설정됨: {validate_api_key(api_config.api_key)}")
        
        # 메뉴 설정 로드
        menu_config = config_manager.load_menu_config()
        print(f"메뉴 설정:")
        print(f"  - 식당명: {menu_config.restaurant_info.get('name', 'Unknown')}")
        print(f"  - 식당 타입: {menu_config.restaurant_info.get('type', 'Unknown')}")
        print(f"  - 카테고리 수: {len(menu_config.categories)}")
        print(f"  - 메뉴 아이템 수: {len(menu_config.menu_items)}")
        
        # 음성 설정 로드
        audio_config = config_manager.get_audio_config()
        print(f"음성 설정:")
        print(f"  - 샘플레이트: {audio_config.sample_rate}Hz")
        print(f"  - 청크 크기: {audio_config.chunk_size}")
        print(f"  - 노이즈 감소 레벨: {audio_config.noise_reduction_level}")
        
        # 시스템 설정 로드
        system_config = config_manager.get_system_config()
        print(f"시스템 설정:")
        print(f"  - 로그 레벨: {system_config.log_level}")
        print(f"  - 언어: {system_config.language}")
        print(f"  - 식당명: {system_config.restaurant_name}")
        
        # TTS 설정 로드
        tts_config = config_manager.get_tts_config()
        print(f"TTS 설정:")
        print(f"  - 서비스: {tts_config.service}")
        print(f"  - 음성: {tts_config.voice}")
        print(f"  - 속도: {tts_config.speed}")
        print()
        
    except Exception as e:
        print(f"설정 로드 중 오류: {e}\n")
    
    # 6. 설정 유효성 검증
    print("6. 설정 유효성 검증")
    validation_results = config_manager.validate_config()
    
    for config_type, is_valid in validation_results.items():
        status = "✓" if is_valid else "✗"
        print(f"  {status} {config_type}: {'유효' if is_valid else '유효하지 않음'}")
    
    all_valid = all(validation_results.values())
    print(f"\n전체 설정 상태: {'✓ 모든 설정이 유효합니다' if all_valid else '✗ 일부 설정에 문제가 있습니다'}")
    print()
    
    # 7. 설정 요약 정보
    print("7. 설정 요약 정보")
    summary = config_manager.get_config_summary()
    
    if summary:
        print("설정 요약:")
        for category, info in summary.items():
            print(f"  {category.upper()}:")
            for key, value in info.items():
                print(f"    - {key}: {value}")
    else:
        print("설정 요약 정보를 가져올 수 없습니다.")
    print()
    
    # 8. 환경 변수 확인
    print("8. 환경 변수 확인")
    env_vars = [
        'OPENAI_API_KEY', 'OPENAI_MODEL', 'LOG_LEVEL', 
        'AUDIO_SAMPLE_RATE', 'RESTAURANT_NAME'
    ]
    
    print("주요 환경 변수:")
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'API_KEY' in var:
                display_value = f"{value[:10]}..." if len(value) > 10 else value
            else:
                display_value = value
            print(f"  - {var}: {display_value}")
        else:
            print(f"  - {var}: 설정되지 않음")
    print()
    
    # 9. 권장사항 표시
    print("9. 권장사항")
    recommendations = []
    
    if not validate_api_key(api_config.api_key):
        recommendations.append("OpenAI API 키를 .env 파일의 OPENAI_API_KEY에 설정하세요")
    
    if not all_valid:
        recommendations.append("유효하지 않은 설정을 수정하세요")
    
    if not recommendations:
        recommendations.append("모든 설정이 올바르게 구성되었습니다!")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")
    
    print("\n=== 설정 관리 시스템 데모 완료 ===")


def demo_dynamic_config_loading():
    """동적 설정 로딩 데모"""
    print("\n=== 동적 설정 로딩 데모 ===")
    
    config_manager = ConfigManager()
    
    # 초기 메뉴 설정 로드
    print("1. 초기 메뉴 설정 로드")
    menu_config = config_manager.load_menu_config()
    print(f"메뉴 아이템 수: {len(menu_config.menu_items)}")
    print(f"마지막 수정 시간: {menu_config.last_modified}")
    
    # 사용자에게 메뉴 파일 수정 요청
    print("\n2. 메뉴 파일 수정 테스트")
    print("config/menu_config.json 파일을 수정한 후 Enter를 누르세요...")
    print("(예: 새로운 메뉴 아이템 추가)")
    input("계속하려면 Enter를 누르세요...")
    
    # 동적 로딩 확인
    print("\n3. 동적 로딩 확인")
    updated_menu_config = config_manager.load_menu_config()
    print(f"업데이트된 메뉴 아이템 수: {len(updated_menu_config.menu_items)}")
    print(f"새로운 수정 시간: {updated_menu_config.last_modified}")
    
    if updated_menu_config.last_modified != menu_config.last_modified:
        print("✓ 동적 로딩이 정상적으로 작동했습니다!")
    else:
        print("파일이 수정되지 않았거나 동적 로딩에 문제가 있습니다.")
    
    print("=== 동적 설정 로딩 데모 완료 ===")


if __name__ == "__main__":
    demo_config_management()
    
    # 동적 로딩 데모는 선택사항
    print("\n동적 설정 로딩 데모를 실행하시겠습니까? (y/n): ", end="")
    if input().lower() == 'y':
        demo_dynamic_config_loading()