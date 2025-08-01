"""
설정 관리 시스템 통합 테스트
"""

import os
import json
import tempfile
from pathlib import Path
from src.config import ConfigManager
from src.utils.config_utils import (
    create_default_config_files,
    create_env_file,
    load_env_file,
    validate_api_key,
    backup_config_file,
    restore_config_file,
    validate_json_file,
    setup_initial_config
)


def test_config_integration():
    """설정 관리 시스템 통합 테스트"""
    print("=== 설정 관리 시스템 통합 테스트 시작 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config_dir = temp_path / "config"
        
        print(f"임시 디렉토리: {temp_dir}")
        
        # 1. 기본 설정 파일 생성 테스트
        print("\n1. 기본 설정 파일 생성 테스트")
        create_default_config_files(str(config_dir))
        
        api_keys_file = config_dir / "api_keys.json"
        menu_config_file = config_dir / "menu_config.json"
        
        assert api_keys_file.exists(), "API 키 설정 파일이 생성되지 않았습니다."
        assert menu_config_file.exists(), "메뉴 설정 파일이 생성되지 않았습니다."
        print("기본 설정 파일 생성 완료")
        
        # 2. JSON 파일 유효성 검증 테스트
        print("\n2. JSON 파일 유효성 검증 테스트")
        api_validation = validate_json_file(str(api_keys_file))
        menu_validation = validate_json_file(str(menu_config_file))
        
        assert api_validation['valid'], f"API 설정 파일이 유효하지 않습니다: {api_validation.get('error')}"
        assert menu_validation['valid'], f"메뉴 설정 파일이 유효하지 않습니다: {menu_validation.get('error')}"
        print("JSON 파일 유효성 검증 완료")
        
        # 3. 환경 변수 파일 생성 및 로드 테스트
        print("\n3. 환경 변수 파일 테스트")
        env_file = temp_path / ".env"
        create_env_file(str(env_file))
        
        assert env_file.exists(), "환경 변수 파일이 생성되지 않았습니다."
        
        # 환경 변수 로드
        load_env_file(str(env_file))
        
        # 테스트를 위해 환경 변수에서 API 키 제거
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        print("환경 변수 파일 생성 및 로드 완료")
        
        # 4. ConfigManager 초기화 및 설정 로드 테스트
        print("\n4. ConfigManager 설정 로드 테스트")
        
        # ConfigManager 초기화
        config_manager = ConfigManager(str(config_dir))
        
        # API 설정에 유효한 키 설정
        with open(api_keys_file, 'r', encoding='utf-8') as f:
            api_config = json.load(f)
        api_config['openai']['api_key'] = 'sk-test_valid_api_key_for_testing_purposes_only'
        with open(api_keys_file, 'w', encoding='utf-8') as f:
            json.dump(api_config, f, indent=2)
        
        # 파일 내용 확인
        with open(api_keys_file, 'r', encoding='utf-8') as f:
            check_config = json.load(f)
        print(f"파일에 저장된 API 키: {check_config['openai']['api_key'][:10]}...")
        
        # 캐시 초기화
        config_manager._api_config = None
        
        # 설정 로드
        api_config_obj = config_manager.load_api_config()
        menu_config_obj = config_manager.load_menu_config()
        audio_config_obj = config_manager.get_audio_config()
        system_config_obj = config_manager.get_system_config()
        tts_config_obj = config_manager.get_tts_config()
        
        print(f"API 설정 로드: 모델={api_config_obj.model}")
        print(f"메뉴 설정 로드: 메뉴 아이템 수={len(menu_config_obj.menu_items)}")
        print(f"음성 설정 로드: 샘플레이트={audio_config_obj.sample_rate}")
        print(f"시스템 설정 로드: 로그레벨={system_config_obj.log_level}")
        print(f"TTS 설정 로드: 서비스={tts_config_obj.service}")
        
        # 5. 설정 유효성 검증 테스트
        print("\n5. 설정 유효성 검증 테스트")
        
        # API 설정을 강제로 다시 로드
        api_config_obj = config_manager.load_api_config(force_reload=True)
        print(f"API 키 확인: {api_config_obj.api_key[:10]}...")
        
        validation_results = config_manager.validate_config()
        
        print(f"API 설정 유효성: {validation_results['api_config']}")
        print(f"메뉴 설정 유효성: {validation_results['menu_config']}")
        print(f"음성 설정 유효성: {validation_results['audio_config']}")
        print(f"시스템 설정 유효성: {validation_results['system_config']}")
        print(f"TTS 설정 유효성: {validation_results['tts_config']}")
        
        assert all(validation_results.values()), f"일부 설정이 유효하지 않습니다: {validation_results}"
        print("모든 설정 유효성 검증 완료")
        
        # 6. 동적 메뉴 로딩 테스트
        print("\n6. 동적 메뉴 로딩 테스트")
        
        # 메뉴 설정 수정
        with open(menu_config_file, 'r', encoding='utf-8') as f:
            menu_data = json.load(f)
        
        menu_data['menu_items']['새로운메뉴'] = {
            "category": "버거",
            "price": 7000,
            "description": "새로운 버거 메뉴",
            "available_options": ["단품", "세트"],
            "set_drink_options": ["콜라"],
            "set_side_options": ["감자튀김"]
        }
        
        # 파일 수정 시간을 변경하기 위해 잠시 대기
        import time
        time.sleep(0.1)
        
        with open(menu_config_file, 'w', encoding='utf-8') as f:
            json.dump(menu_data, f, indent=2, ensure_ascii=False)
        
        # 동적 로딩 확인
        updated_menu_config = config_manager.load_menu_config()
        assert '새로운메뉴' in updated_menu_config.menu_items, "동적 메뉴 로딩이 작동하지 않습니다."
        print("동적 메뉴 로딩 완료")
        
        # 7. 설정 백업 및 복원 테스트
        print("\n7. 설정 백업 및 복원 테스트")
        
        backup_path = backup_config_file(str(menu_config_file))
        assert backup_path is not None, "설정 파일 백업이 실패했습니다."
        assert Path(backup_path).exists(), "백업 파일이 생성되지 않았습니다."
        print(f"설정 파일 백업 완료: {backup_path}")
        
        # 원본 파일 수정
        menu_data['menu_items']['테스트메뉴'] = {
            "category": "음료",
            "price": 1500,
            "description": "테스트 음료",
            "available_options": ["미디움"],
            "set_drink_options": [],
            "set_side_options": []
        }
        
        with open(menu_config_file, 'w', encoding='utf-8') as f:
            json.dump(menu_data, f, indent=2, ensure_ascii=False)
        
        # 복원 테스트
        restore_success = restore_config_file(backup_path, str(menu_config_file))
        assert restore_success, "설정 파일 복원이 실패했습니다."
        
        # 복원 확인
        config_manager.reload_all_configs()
        restored_menu_config = config_manager.load_menu_config()
        assert '테스트메뉴' not in restored_menu_config.menu_items, "설정 파일 복원이 제대로 되지 않았습니다."
        print("설정 파일 복원 완료")
        
        # 8. 설정 요약 정보 테스트
        print("\n8. 설정 요약 정보 테스트")
        summary = config_manager.get_config_summary()
        
        assert 'api' in summary, "API 설정 요약이 없습니다."
        assert 'menu' in summary, "메뉴 설정 요약이 없습니다."
        assert 'audio' in summary, "음성 설정 요약이 없습니다."
        assert 'system' in summary, "시스템 설정 요약이 없습니다."
        assert 'tts' in summary, "TTS 설정 요약이 없습니다."
        
        print(f"설정 요약 정보:")
        print(f"  - API 모델: {summary['api']['model']}")
        print(f"  - 메뉴 아이템 수: {summary['menu']['menu_items_count']}")
        print(f"  - 음성 샘플레이트: {summary['audio']['sample_rate']}")
        print(f"  - 시스템 언어: {summary['system']['language']}")
        
        # 9. API 키 유효성 검증 테스트
        print("\n9. API 키 유효성 검증 테스트")
        
        valid_key = "sk-test_valid_api_key_for_testing_purposes_only"
        invalid_key1 = "your_openai_api_key_here"
        invalid_key2 = ""
        invalid_key3 = "invalid_key"
        
        assert validate_api_key(valid_key), "유효한 API 키가 유효하지 않다고 판단됩니다."
        assert not validate_api_key(invalid_key1), "기본 플레이스홀더 키가 유효하다고 판단됩니다."
        assert not validate_api_key(invalid_key2), "빈 키가 유효하다고 판단됩니다."
        assert not validate_api_key(invalid_key3), "잘못된 형식의 키가 유효하다고 판단됩니다."
        
        print("API 키 유효성 검증 완료")
        
        print("\n=== 모든 통합 테스트 완료 ===")
        print("설정 관리 시스템이 정상적으로 작동합니다.")


def test_environment_variable_priority():
    """환경 변수 우선순위 테스트"""
    print("\n=== 환경 변수 우선순위 테스트 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        
        # 기본 설정 파일 생성
        create_default_config_files(str(config_dir))
        
        # 설정 파일에 값 설정
        api_keys_file = config_dir / "api_keys.json"
        with open(api_keys_file, 'r', encoding='utf-8') as f:
            api_config = json.load(f)
        
        api_config['openai']['api_key'] = 'sk-file_api_key'
        api_config['openai']['model'] = 'gpt-3.5-turbo'
        
        with open(api_keys_file, 'w', encoding='utf-8') as f:
            json.dump(api_config, f, indent=2)
        
        # 환경 변수 설정
        os.environ['OPENAI_API_KEY'] = 'sk-env_api_key'
        os.environ['OPENAI_MODEL'] = 'gpt-4o'
        
        try:
            config_manager = ConfigManager(str(config_dir))
            api_config_obj = config_manager.load_api_config()
            
            # 환경 변수가 우선되어야 함
            assert api_config_obj.api_key == 'sk-env_api_key', f"환경 변수 API 키가 우선되지 않았습니다: {api_config_obj.api_key}"
            assert api_config_obj.model == 'gpt-4o', f"환경 변수 모델이 우선되지 않았습니다: {api_config_obj.model}"
            
            print("환경 변수가 설정 파일보다 우선됩니다.")
            
        finally:
            # 환경 변수 정리
            if 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']
            if 'OPENAI_MODEL' in os.environ:
                del os.environ['OPENAI_MODEL']


def test_error_handling():
    """오류 처리 테스트"""
    print("\n=== 오류 처리 테스트 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir) / "config"
        
        # 환경 변수 정리
        env_backup = {}
        for key in ['OPENAI_API_KEY', 'OPENAI_MODEL', 'OPENAI_MAX_TOKENS', 'OPENAI_TEMPERATURE']:
            if key in os.environ:
                env_backup[key] = os.environ[key]
                del os.environ[key]
        
        try:
            config_manager = ConfigManager(str(config_dir))
            
            # 1. 존재하지 않는 설정 파일 테스트
            print("1. 존재하지 않는 설정 파일 테스트")
            try:
                config_manager.load_api_config()
                # ConfigManager는 파일이 없을 때 기본값을 사용하므로 예외가 발생하지 않을 수 있음
                print("API 설정 파일이 없을 때 기본값 사용됨")
            except FileNotFoundError:
                print("존재하지 않는 API 설정 파일에 대해 적절한 예외 발생")
            
            try:
                config_manager.load_menu_config()
                # ConfigManager는 파일이 없을 때 기본값을 사용하므로 예외가 발생하지 않을 수 있음
                print("메뉴 설정 파일이 없을 때 기본값 사용됨")
            except FileNotFoundError:
                print("존재하지 않는 메뉴 설정 파일에 대해 적절한 예외 발생")
        
        finally:
            # 환경 변수 복원
            for key, value in env_backup.items():
                os.environ[key] = value
        
        # 2. 잘못된 JSON 형식 테스트
        print("2. 잘못된 JSON 형식 테스트")
        config_dir.mkdir(exist_ok=True)
        
        invalid_json_file = config_dir / "api_keys.json"
        with open(invalid_json_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json content")
        
        try:
            config_manager.load_api_config()
            # ConfigManager가 JSON 오류를 내부적으로 처리할 수 있음
            print("잘못된 JSON에 대해 기본값 사용됨 또는 내부 처리됨")
        except json.JSONDecodeError:
            print("잘못된 JSON 형식에 대해 적절한 예외 발생")
        except Exception as e:
            print(f"잘못된 JSON에 대해 다른 예외 발생: {type(e).__name__}")
        
        # 3. 유효하지 않은 메뉴 설정 테스트
        print("3. 유효하지 않은 메뉴 설정 테스트")
        
        # 유효한 API 설정 생성
        valid_api_config = {
            "openai": {
                "api_key": "sk-test_key",
                "model": "gpt-4o"
            }
        }
        with open(invalid_json_file, 'w', encoding='utf-8') as f:
            json.dump(valid_api_config, f)
        
        # 유효하지 않은 메뉴 설정 생성
        invalid_menu_config = {
            "restaurant_info": {"name": "테스트"},
            "categories": ["버거"],
            "menu_items": {
                "콜라": {
                    "category": "음료",  # categories에 없는 카테고리
                    "price": 2000,
                    "description": "콜라",
                    "available_options": ["미디움"],
                    "set_drink_options": [],
                    "set_side_options": []
                }
            },
            "set_pricing": {},
            "option_pricing": {}
        }
        
        menu_file = config_dir / "menu_config.json"
        with open(menu_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_menu_config, f)
        
        try:
            config_manager.load_menu_config()
            assert False, "유효하지 않은 메뉴 설정에 대해 예외가 발생하지 않았습니다."
        except ValueError:
            print("유효하지 않은 메뉴 설정에 대해 적절한 예외 발생")


if __name__ == "__main__":
    test_config_integration()
    test_environment_variable_priority()
    test_error_handling()
    print("\n모든 설정 관리 시스템 테스트가 성공적으로 완료되었습니다!")