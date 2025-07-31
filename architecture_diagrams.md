# 음성 기반 키오스크 AI 주문 시스템 - 아키텍처 시각화

## 1. 전체 시스템 아키텍처

```mermaid
graph TB
    subgraph "사용자 인터페이스"
        A[👤 사용자 음성 입력]
        B[🎤 마이크 입력]
        C[📝 텍스트 입력]
        D[📁 음성 파일 입력]
    end
    
    subgraph "음성 전처리 계층"
        E[🔊 AudioProcessor<br/>다중화자인식/구분]
        F[🎙️ MicrophoneManager<br/>VAD 기반 실시간 처리]
    end
    
    subgraph "음성인식 계층"
        G[🗣️ SpeechRecognizer<br/>Whisper 기반 STT]
    end
    
    subgraph "자연어 처리 계층"
        H[🧠 IntentRecognizer<br/>GPT-4o 기반 의도 파악]
        I[💬 DialogueManager<br/>멀티턴 대화 관리]
    end
    
    subgraph "비즈니스 로직 계층"
        J[🍔 MenuManager<br/>메뉴 관리]
        K[📋 OrderManager<br/>주문 처리]
        L[💳 PaymentProcessor<br/>결제 처리]
    end
    
    subgraph "응답 생성 계층"
        M[📝 TextResponseSystem<br/>응답 생성]
        N[🔊 TTSManager<br/>음성 합성]
    end
    
    subgraph "데이터 저장소"
        O[(🗄️ 메뉴 설정<br/>menu_config.json)]
        P[(📊 주문 데이터)]
        Q[(📝 로그 데이터)]
    end
    
    A --> E
    B --> F
    C --> H
    D --> E
    
    E --> G
    F --> G
    G --> H
    H --> I
    I --> J
    I --> K
    I --> L
    
    J --> M
    K --> M
    L --> M
    M --> N
    
    J <--> O
    K <--> P
    M --> Q
    
    N --> R[🔊 음성 출력]
    M --> S[📱 텍스트 출력]
```

## 2. 데이터 흐름 다이어그램

```mermaid
sequenceDiagram
    participant U as 👤 사용자
    participant M as 🎤 마이크
    participant A as 🔊 음성전처리
    participant S as 🗣️ 음성인식
    participant I as 🧠 의도파악
    participant D as 💬 대화관리
    participant O as 📋 주문관리
    participant R as 📝 응답생성
    participant T as 🔊 TTS
    
    U->>M: 음성 입력
    M->>A: 실시간 음성 데이터
    A->>S: 전처리된 음성
    S->>I: 텍스트 변환
    I->>D: 의도 분석 결과
    D->>O: 주문 명령
    O->>R: 주문 상태
    R->>T: 응답 텍스트
    T->>U: 음성 응답
    
    Note over U,T: 전체 처리 시간: ~20초 (실측, 네트워크 포함)
```

## 3. 모듈별 상세 구조

```mermaid
graph LR
    subgraph "src/"
        subgraph "audio/"
            A1[preprocessing.py<br/>다중화자인식]
            A2[tts_manager.py<br/>음성합성]
        end
        
        subgraph "speech/"
            S1[recognition.py<br/>Whisper STT]
        end
        
        subgraph "conversation/"
            C1[intent.py<br/>의도파악]
            C2[dialogue.py<br/>대화관리]
        end
        
        subgraph "order/"
            O1[menu.py<br/>메뉴관리]
            O2[order.py<br/>주문처리]
        end
        
        subgraph "microphone/"
            M1[microphone_manager.py<br/>마이크관리]
            M2[vad_processor.py<br/>음성활동감지]
        end
        
        subgraph "testing/"
            T1[test_case_generator.py<br/>테스트생성]
            T2[test_runner.py<br/>테스트실행]
        end
    end
```

## 4. 키오스크 사용 시나리오

```mermaid
stateDiagram-v2
    [*] --> 대기상태
    대기상태 --> 음성감지 : 사용자 접근
    음성감지 --> 음성인식 : 음성 입력 시작
    음성인식 --> 의도파악 : STT 완료
    의도파악 --> 주문처리 : 주문 의도
    의도파악 --> 문의응답 : 문의 의도
    의도파악 --> 도움말 : 도움 요청
    
    주문처리 --> 메뉴확인 : 메뉴 검색
    메뉴확인 --> 옵션선택 : 메뉴 발견
    옵션선택 --> 주문확정 : 옵션 완료
    주문확정 --> 결제처리 : 결제 요청
    결제처리 --> 완료 : 결제 성공
    
    문의응답 --> 대기상태 : 응답 완료
    도움말 --> 대기상태 : 도움말 제공
    완료 --> 대기상태 : 주문 완료
    
    메뉴확인 --> 대기상태 : 메뉴 없음
    옵션선택 --> 주문처리 : 옵션 변경
```

## 5. 기술 스택 구성도

```mermaid
graph TB
    subgraph "프론트엔드 계층"
        F1[🎤 마이크 입력]
        F2[📝 텍스트 입력]
        F3[📁 파일 입력]
    end
    
    subgraph "AI/ML 계층"
        AI1[🤖 OpenAI Whisper<br/>음성인식]
        AI2[🧠 GPT-4o<br/>자연어처리]
        AI3[🔊 OpenAI TTS<br/>음성합성]
        AI4[📊 Silero VAD<br/>음성활동감지]
    end
    
    subgraph "비즈니스 로직 계층"
        BL1[🍔 메뉴 관리]
        BL2[📋 주문 처리]
        BL3[💬 대화 관리]
        BL4[🧪 테스트 시스템]
    end
    
    subgraph "데이터 계층"
        D1[📄 JSON 설정파일]
        D2[📊 로그 데이터]
        D3[🎵 임시 오디오 파일]
    end
    
    subgraph "인프라 계층"
        I1[🐍 Python 3.8+]
        I2[📦 pip 패키지 관리]
        I3[🔧 환경변수 설정]
    end
    
    F1 --> AI4
    F2 --> AI2
    F3 --> AI1
    
    AI4 --> AI1
    AI1 --> AI2
    AI2 --> BL3
    BL3 --> BL1
    BL3 --> BL2
    AI2 --> AI3
    
    BL1 --> D1
    BL2 --> D2
    AI1 --> D3
    
    AI1 --> I1
    AI2 --> I1
    BL1 --> I2
    BL2 --> I3
```

## 6. 성능 및 품질 지표

```mermaid
pie title 처리 시간 분포 (실측 기반)
    "네트워크 지연" : 35
    "서버 처리" : 25
    "텍스트 처리" : 15
    "음성 입력" : 10
    "TTS 생성" : 5
    "기타" : 10
```

```mermaid
xychart-beta
    title "처리 시간 분석 (초)"
    x-axis [음성입력, 네트워크전송, 서버처리, TTS생성, 텍스트처리, 메뉴로딩]
    y-axis "처리시간" 0 --> 2
    bar [2.0, 5.0, 7.0, 1.0, 3.0, 2.0]
```
