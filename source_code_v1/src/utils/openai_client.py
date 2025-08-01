"""
OpenAI API 클라이언트 (requests 기반)
OpenAI 라이브러리의 클라이언트 초기화 문제를 우회하기 위한 대안
"""

import requests
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ChatMessage:
    """채팅 메시지"""
    role: str
    content: str


@dataclass
class ChatChoice:
    """채팅 응답 선택지"""
    message: ChatMessage
    finish_reason: str
    index: int


@dataclass
class ChatCompletion:
    """채팅 완료 응답"""
    choices: List[ChatChoice]
    model: str
    usage: Dict[str, int]


class OpenAIClient:
    """OpenAI API 클라이언트 (requests 기반)"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        """
        클라이언트 초기화
        
        Args:
            api_key: OpenAI API 키
            base_url: API 기본 URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def chat_completions_create(
        self,
        model: str = "gpt-4o",
        messages: List[Dict[str, str]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None
    ) -> ChatCompletion:
        """
        채팅 완료 API 호출
        
        Args:
            model: 사용할 모델
            messages: 메시지 리스트
            max_tokens: 최대 토큰 수
            temperature: 온도 설정
            tools: 도구 목록 (tool calling용)
            tool_choice: 도구 선택 방식
            
        Returns:
            ChatCompletion 객체
        """
        if messages is None:
            messages = []
        
        data = {
            'model': model,
            'messages': messages,
            'max_tokens': max_tokens,
            'temperature': temperature
        }
        
        # Tool calling 지원
        if tools:
            data['tools'] = tools
        if tool_choice:
            data['tool_choice'] = tool_choice
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"API 호출 실패: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # 응답을 ChatCompletion 객체로 변환
            choices = []
            for choice_data in result.get('choices', []):
                message = ChatMessage(
                    role=choice_data['message']['role'],
                    content=choice_data['message']['content']
                )
                choice = ChatChoice(
                    message=message,
                    finish_reason=choice_data.get('finish_reason', ''),
                    index=choice_data.get('index', 0)
                )
                choices.append(choice)
            
            return ChatCompletion(
                choices=choices,
                model=result.get('model', model),
                usage=result.get('usage', {})
            )
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"네트워크 오류: {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"응답 파싱 오류: {e}")
        except Exception as e:
            raise Exception(f"API 호출 오류: {e}")


def create_openai_client(api_key: str) -> OpenAIClient:
    """
    OpenAI 클라이언트 생성
    
    Args:
        api_key: OpenAI API 키
        
    Returns:
        OpenAIClient 인스턴스
    """
    return OpenAIClient(api_key)