"""
안전한 입력 처리 유틸리티
"""

import sys
from typing import Optional


def safe_input(prompt: str, default: str = "") -> Optional[str]:
    """
    안전한 입력 처리 (EOF, KeyboardInterrupt 처리)
    
    Args:
        prompt: 입력 프롬프트
        default: 기본값
        
    Returns:
        입력된 문자열 또는 None (중단된 경우)
    """
    try:
        result = input(prompt).strip()
        return result if result else default
    except EOFError:
        print("\n입력이 종료되었습니다.")
        return None
    except KeyboardInterrupt:
        print("\n사용자가 취소했습니다.")
        return None


def safe_choice(prompt: str, valid_choices: list, default: str = "") -> Optional[str]:
    """
    안전한 선택 입력 처리
    
    Args:
        prompt: 입력 프롬프트
        valid_choices: 유효한 선택지 리스트
        default: 기본값
        
    Returns:
        선택된 값 또는 None (중단된 경우)
    """
    while True:
        choice = safe_input(prompt, default)
        
        if choice is None:  # EOF 또는 KeyboardInterrupt
            return None
        
        if choice in valid_choices:
            return choice
        
        print(f"❌ 잘못된 선택입니다. 다음 중에서 선택하세요: {', '.join(valid_choices)}")


def confirm_action(prompt: str, default: bool = False) -> Optional[bool]:
    """
    확인 액션 처리
    
    Args:
        prompt: 확인 프롬프트
        default: 기본값
        
    Returns:
        True/False 또는 None (중단된 경우)
    """
    default_text = "Y/n" if default else "y/N"
    full_prompt = f"{prompt} ({default_text}): "
    
    choice = safe_input(full_prompt)
    
    if choice is None:
        return None
    
    if not choice:  # 빈 입력
        return default
    
    return choice.lower() in ['y', 'yes', '예', 'true', '1']


def get_menu_choice(menu_items: dict, prompt: str = "선택하세요") -> Optional[str]:
    """
    메뉴 선택 처리
    
    Args:
        menu_items: {키: 설명} 형태의 메뉴 딕셔너리
        prompt: 선택 프롬프트
        
    Returns:
        선택된 키 또는 None (중단된 경우)
    """
    print("\n메뉴:")
    for key, description in menu_items.items():
        print(f"  {key}. {description}")
    
    valid_choices = list(menu_items.keys())
    return safe_choice(f"{prompt} ({'/'.join(valid_choices)}): ", valid_choices)


def pause_for_continue(message: str = "계속하려면 Enter를 누르세요") -> bool:
    """
    계속 진행을 위한 일시정지
    
    Args:
        message: 표시할 메시지
        
    Returns:
        True (계속), False (중단)
    """
    result = safe_input(f"\n{message}...")
    return result is not None  # None이면 중단됨