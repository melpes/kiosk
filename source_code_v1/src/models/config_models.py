"""
설정 관련 데이터 모델
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from decimal import Decimal


@dataclass
class MenuItemConfig:
    """메뉴 아이템 설정"""
    name: str                    # 메뉴명
    category: str                # 카테고리
    price: Decimal               # 가격
    available_options: List[str] = field(default_factory=list)  # 사용 가능한 옵션들
    description: str = ""        # 설명
    is_available: bool = True    # 판매 가능 여부
    
    def __hash__(self):
        """해시 함수 (set에서 사용하기 위해)"""
        return hash((self.name, self.category, self.price))
    
    def __post_init__(self):
        """데이터 검증"""
        if not self.name or not self.name.strip():
            raise ValueError("메뉴명은 비어있을 수 없습니다")
        
        if not self.category or not self.category.strip():
            raise ValueError("카테고리는 비어있을 수 없습니다")
        
        if self.price < 0:
            raise ValueError("가격은 음수일 수 없습니다")
        
        # 가격을 Decimal로 변환
        if not isinstance(self.price, Decimal):
            self.price = Decimal(str(self.price))
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'name': self.name,
            'category': self.category,
            'price': float(self.price),
            'available_options': self.available_options,
            'description': self.description,
            'is_available': self.is_available
        }


@dataclass
class MenuConfig:
    """메뉴 설정"""
    restaurant_type: str         # 식당 타입 (예: "fast_food", "korean", "chinese")
    menu_items: Dict[str, MenuItemConfig]  # 메뉴 아이템들 (이름 -> 설정)
    categories: List[str]        # 카테고리 목록
    currency: str = "KRW"        # 통화
    tax_rate: Decimal = Decimal("0.1")  # 세율 (기본 10%)
    service_charge: Decimal = Decimal("0.0")  # 서비스 요금
    
    def __post_init__(self):
        """데이터 검증"""
        if not self.restaurant_type or not self.restaurant_type.strip():
            raise ValueError("식당 타입은 비어있을 수 없습니다")
        
        if not self.menu_items:
            raise ValueError("메뉴 아이템이 최소 하나는 있어야 합니다")
        
        if not self.categories:
            raise ValueError("카테고리가 최소 하나는 있어야 합니다")
        
        # 세율과 서비스 요금을 Decimal로 변환
        if not isinstance(self.tax_rate, Decimal):
            self.tax_rate = Decimal(str(self.tax_rate))
        
        if not isinstance(self.service_charge, Decimal):
            self.service_charge = Decimal(str(self.service_charge))
        
        # 메뉴 아이템의 카테고리가 정의된 카테고리에 포함되는지 확인
        for item_name, item_config in self.menu_items.items():
            if item_config.category not in self.categories:
                raise ValueError(f"메뉴 아이템 '{item_name}'의 카테고리 '{item_config.category}'가 정의된 카테고리에 없습니다")
    
    def get_items_by_category(self, category: str) -> List[MenuItemConfig]:
        """카테고리별 메뉴 아이템 반환"""
        return [item for item in self.menu_items.values() if item.category == category and item.is_available]
    
    def get_item(self, name: str) -> Optional[MenuItemConfig]:
        """메뉴 아이템 반환"""
        return self.menu_items.get(name)
    
    def is_item_available(self, name: str) -> bool:
        """메뉴 아이템 판매 가능 여부 확인"""
        item = self.get_item(name)
        return item is not None and item.is_available


@dataclass
class AudioConfig:
    """음성 처리 설정"""
    sample_rate: int = 16000     # 샘플링 레이트
    chunk_size: int = 1024       # 청크 크기
    channels: int = 1            # 채널 수
    noise_reduction_level: float = 0.5  # 노이즈 제거 레벨 (0.0 ~ 1.0)
    speaker_separation_threshold: float = 0.7  # 화자 분리 임계값
    max_recording_duration: int = 30  # 최대 녹음 시간 (초)
    silence_threshold: float = 0.01   # 무음 임계값
    noise_reduction_enabled: bool = True  # 노이즈 제거 활성화
    speaker_separation_enabled: bool = True  # 화자 분리 활성화
    
    def __post_init__(self):
        """데이터 검증"""
        if self.sample_rate <= 0:
            raise ValueError("샘플링 레이트는 양수여야 합니다")
        
        if self.chunk_size <= 0:
            raise ValueError("청크 크기는 양수여야 합니다")
        
        if self.channels <= 0:
            raise ValueError("채널 수는 양수여야 합니다")
        
        if not (0.0 <= self.noise_reduction_level <= 1.0):
            raise ValueError("노이즈 제거 레벨은 0.0과 1.0 사이여야 합니다")
        
        if not (0.0 <= self.speaker_separation_threshold <= 1.0):
            raise ValueError("화자 분리 임계값은 0.0과 1.0 사이여야 합니다")
        
        if self.max_recording_duration <= 0:
            raise ValueError("최대 녹음 시간은 양수여야 합니다")


@dataclass
class TTSConfig:
    """TTS 설정"""
    engine: str = "default"      # TTS 엔진
    voice: str = "default"       # 음성
    speed: float = 1.0           # 속도 (0.5 ~ 2.0)
    pitch: float = 1.0           # 음높이 (0.5 ~ 2.0)
    volume: float = 1.0          # 볼륨 (0.0 ~ 1.0)
    language: str = "ko"         # 언어
    output_format: str = "wav"   # 출력 포맷
    sample_rate: int = 22050     # 출력 샘플링 레이트
    
    def __post_init__(self):
        """데이터 검증"""
        if not self.engine or not self.engine.strip():
            raise ValueError("TTS 엔진은 비어있을 수 없습니다")
        
        if not (0.5 <= self.speed <= 2.0):
            raise ValueError("속도는 0.5와 2.0 사이여야 합니다")
        
        if not (0.5 <= self.pitch <= 2.0):
            raise ValueError("음높이는 0.5와 2.0 사이여야 합니다")
        
        if not (0.0 <= self.volume <= 1.0):
            raise ValueError("볼륨은 0.0과 1.0 사이여야 합니다")
        
        if not self.language or not self.language.strip():
            raise ValueError("언어는 비어있을 수 없습니다")
        
        if self.sample_rate <= 0:
            raise ValueError("샘플링 레이트는 양수여야 합니다")


@dataclass
class SystemConfig:
    """시스템 전체 설정"""
    menu_config: MenuConfig      # 메뉴 설정
    audio_config: AudioConfig    # 음성 설정
    tts_config: TTSConfig        # TTS 설정
    api_keys: Dict[str, str] = field(default_factory=dict)  # API 키들
    log_level: str = "INFO"      # 로그 레벨
    debug_mode: bool = False     # 디버그 모드
    
    def __post_init__(self):
        """데이터 검증"""
        if not isinstance(self.menu_config, MenuConfig):
            raise ValueError("메뉴 설정은 MenuConfig 객체여야 합니다")
        
        if not isinstance(self.audio_config, AudioConfig):
            raise ValueError("음성 설정은 AudioConfig 객체여야 합니다")
        
        if not isinstance(self.tts_config, TTSConfig):
            raise ValueError("TTS 설정은 TTSConfig 객체여야 합니다")
        
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"로그 레벨은 {valid_log_levels} 중 하나여야 합니다")