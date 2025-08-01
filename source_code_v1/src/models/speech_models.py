"""
음성인식 관련 데이터 모델
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RecognitionResult:
    """음성인식 결과"""
    text: str                    # 인식된 텍스트
    confidence: float            # 신뢰도 (0.0 ~ 1.0)
    processing_time: float       # 처리 시간 (초)
    language: str = "ko"         # 언어 코드
    model_version: Optional[str] = None  # 사용된 모델 버전
    
    def __post_init__(self):
        """데이터 검증"""
        if not isinstance(self.text, str):
            raise ValueError("인식된 텍스트는 문자열이어야 합니다")
        
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError("신뢰도는 0.0과 1.0 사이의 값이어야 합니다")
        
        if self.processing_time < 0:
            raise ValueError("처리 시간은 음수일 수 없습니다")
        
        if not self.language:
            raise ValueError("언어 코드는 비어있을 수 없습니다")
    
    @property
    def is_high_confidence(self) -> bool:
        """높은 신뢰도 여부 (0.8 이상)"""
        return self.confidence >= 0.8
    
    @property
    def is_low_confidence(self) -> bool:
        """낮은 신뢰도 여부 (0.5 미만)"""
        return self.confidence < 0.5
    
    def __str__(self) -> str:
        return f"RecognitionResult(text='{self.text}', confidence={self.confidence:.2f})"