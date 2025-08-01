#!/usr/bin/env python3
"""
키오스크 클라이언트 자동 설치 스크립트
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from typing import List, Dict, Any


class ClientInstaller:
    """클라이언트 설치 관리자"""
    
    def __init__(self):
        self.package_dir = Path(__file__).parent
        self.python_executable = sys.executable
        self.requirements_file = self.package_dir / "requirements.txt"
        self.config_file = self.package_dir / "config.json"
        
    def check_python_version(self) -> bool:
        """Python 버전 확인"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print("❌ Python 3.8 이상이 필요합니다.")
            print(f"현재 버전: {version.major}.{version.minor}.{version.micro}")
            return False
        
        print(f"✅ Python 버전 확인: {version.major}.{version.minor}.{version.micro}")
        return True
    
    def check_pip(self) -> bool:
        """pip 설치 확인"""
        try:
            import pip
            print(f"✅ pip 확인: {pip.__version__}")
            return True
        except ImportError:
            print("❌ pip가 설치되어 있지 않습니다.")
            return False
    
    def install_dependencies(self) -> bool:
        """의존성 설치"""
        if not self.requirements_file.exists():
            print("❌ requirements.txt 파일을 찾을 수 없습니다.")
            return False
        
        print("📦 의존성 설치 중...")
        try:
            cmd = [
                self.python_executable, "-m", "pip", "install", 
                "-r", str(self.requirements_file),
                "--upgrade"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=self.package_dir
            )
            
            if result.returncode == 0:
                print("✅ 의존성 설치 완료")
                return True
            else:
                print(f"❌ 의존성 설치 실패:")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ 의존성 설치 중 오류 발생: {e}")
            return False
    
    def setup_directories(self) -> bool:
        """필요한 디렉토리 생성"""
        directories = [
            "temp_audio",
            "logs",
            "examples/test_audio"
        ]
        
        print("📁 디렉토리 설정 중...")
        try:
            for dir_name in directories:
                dir_path = self.package_dir / dir_name
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"   ✅ {dir_name}")
            
            return True
        except Exception as e:
            print(f"❌ 디렉토리 생성 실패: {e}")
            return False
    
    def validate_config(self) -> bool:
        """설정 파일 검증"""
        if not self.config_file.exists():
            print("❌ config.json 파일을 찾을 수 없습니다.")
            return False
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 필수 설정 확인
            required_keys = ['server', 'audio', 'ui', 'logging']
            for key in required_keys:
                if key not in config:
                    print(f"❌ 설정 파일에 '{key}' 섹션이 없습니다.")
                    return False
            
            print("✅ 설정 파일 검증 완료")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ 설정 파일 JSON 형식 오류: {e}")
            return False
        except Exception as e:
            print(f"❌ 설정 파일 검증 실패: {e}")
            return False
    
    def test_installation(self) -> bool:
        """설치 테스트"""
        print("🧪 설치 테스트 중...")
        
        try:
            # 주요 모듈 import 테스트
            test_imports = [
                "requests",
                "soundfile", 
                "dataclasses",
                "pathlib",
                "json"
            ]
            
            for module_name in test_imports:
                try:
                    __import__(module_name)
                    print(f"   ✅ {module_name}")
                except ImportError as e:
                    print(f"   ❌ {module_name}: {e}")
                    return False
            
            # 클라이언트 모듈 테스트
            sys.path.insert(0, str(self.package_dir))
            try:
                from client.config_manager import ConfigManager
                config = ConfigManager.load_config(str(self.config_file))
                print("   ✅ 클라이언트 모듈 로드")
            except Exception as e:
                print(f"   ❌ 클라이언트 모듈 로드 실패: {e}")
                return False
            
            print("✅ 설치 테스트 완료")
            return True
            
        except Exception as e:
            print(f"❌ 설치 테스트 실패: {e}")
            return False
    
    def create_shortcuts(self) -> bool:
        """실행 단축키 생성"""
        print("🔗 실행 스크립트 설정 중...")
        
        try:
            # 실행 스크립트가 실행 가능하도록 설정
            run_script = self.package_dir / "run_client.py"
            if run_script.exists():
                os.chmod(run_script, 0o755)
                print("   ✅ run_client.py 실행 권한 설정")
            
            # 배치 파일 생성 (Windows)
            if sys.platform == "win32":
                batch_content = f"""@echo off
cd /d "{self.package_dir}"
"{self.python_executable}" run_client.py %*
pause
"""
                batch_file = self.package_dir / "run_client.bat"
                with open(batch_file, 'w', encoding='utf-8') as f:
                    f.write(batch_content)
                print("   ✅ run_client.bat 생성")
            
            # 셸 스크립트 생성 (Unix/Linux)
            else:
                shell_content = f"""#!/bin/bash
cd "{self.package_dir}"
"{self.python_executable}" run_client.py "$@"
"""
                shell_file = self.package_dir / "run_client.sh"
                with open(shell_file, 'w', encoding='utf-8') as f:
                    f.write(shell_content)
                os.chmod(shell_file, 0o755)
                print("   ✅ run_client.sh 생성")
            
            return True
            
        except Exception as e:
            print(f"❌ 실행 스크립트 설정 실패: {e}")
            return False
    
    def show_installation_summary(self):
        """설치 완료 요약"""
        print("\n" + "="*60)
        print("🎉 키오스크 클라이언트 설치 완료!")
        print("="*60)
        
        print("\n📋 설치된 구성 요소:")
        print("   ✅ Python 의존성 패키지")
        print("   ✅ 클라이언트 소스 코드")
        print("   ✅ 설정 파일 (config.json)")
        print("   ✅ 실행 스크립트")
        print("   ✅ 예제 코드")
        
        print("\n🚀 실행 방법:")
        print("   # 기본 데모 실행")
        print("   python run_client.py --demo")
        print("")
        print("   # 특정 음성 파일 전송")
        print("   python run_client.py --audio-file test.wav")
        print("")
        print("   # 서버 상태 확인")
        print("   python run_client.py --check-health")
        
        if sys.platform == "win32":
            print("\n   # Windows 배치 파일 사용")
            print("   run_client.bat --demo")
        else:
            print("\n   # Unix/Linux 셸 스크립트 사용")
            print("   ./run_client.sh --demo")
        
        print("\n⚙️  설정 파일:")
        print(f"   {self.config_file}")
        print("   (서버 URL 등을 필요에 따라 수정하세요)")
        
        print("\n📖 자세한 사용법:")
        print("   README.md 파일을 참조하세요")
        
        print("\n" + "="*60)
    
    def install(self) -> bool:
        """전체 설치 프로세스 실행"""
        print("🔧 키오스크 클라이언트 설치를 시작합니다...")
        print("="*60)
        
        # 1. 시스템 요구사항 확인
        if not self.check_python_version():
            return False
        
        if not self.check_pip():
            return False
        
        # 2. 의존성 설치
        if not self.install_dependencies():
            return False
        
        # 3. 디렉토리 설정
        if not self.setup_directories():
            return False
        
        # 4. 설정 파일 검증
        if not self.validate_config():
            return False
        
        # 5. 설치 테스트
        if not self.test_installation():
            return False
        
        # 6. 실행 스크립트 설정
        if not self.create_shortcuts():
            return False
        
        # 7. 설치 완료 요약
        self.show_installation_summary()
        
        return True


def main():
    """메인 함수"""
    installer = ClientInstaller()
    
    try:
        success = installer.install()
        if success:
            print("\n✅ 설치가 성공적으로 완료되었습니다!")
            sys.exit(0)
        else:
            print("\n❌ 설치 중 오류가 발생했습니다.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  설치가 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()