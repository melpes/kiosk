# 🎤 음성 키오스크 파이프라인 & 신뢰도 알고리즘 분석

## 📖 목차
1. [전체 시스템 아키텍처](#전체-시스템-아키텍처)
2. [파이프라인 플로우](#파이프라인-플로우)
3. [신뢰도 및 판단 알고리즘](#신뢰도-및-판단-알고리즘)
4. [화자 분리 알고리즘](#화자-분리-알고리즘)
5. [메뉴 매칭 시스템](#메뉴-매칭-시스템)
6. [성능 모니터링](#성능-모니터링)

---

## 🏗️ 전체 시스템 아키텍처

```mermaid
graph TB
    subgraph "입력 계층"
        A[🎤 음성 입력] --> B[📝 텍스트 입력]
    end
    
    subgraph "전처리 계층"
        C[🔧 AudioProcessor]
        D[🗣️ Speaker Separation]
        E[🎯 VAD Processing]
    end
    
    subgraph "인식 계층"
        F[🗨️ Speech Recognition<br/>Whisper]
        G[🧠 Intent Recognition<br/>GPT-4o]
    end
    
    subgraph "비즈니스 로직"
        H[💬 Dialogue Manager]
        I[🍔 Order Manager]
        J[📋 Menu System]
    end
    
    subgraph "출력 계층"
        K[📞 Response Builder]
        L[🔊 TTS Manager]
        M[📱 Client Response]
    end
    
    A --> C
    C --> D
    D --> E
    E --> F
    B --> G
    F --> G
    G --> H
    H --> I
    H --> J
    I --> K
    J --> K
    K --> L
    L --> M
    
    style F fill:#e1f5fe
    style G fill:#f3e5f5
    style H fill:#e8f5e8
    style I fill:#fff3e0
```

---

## 🔄 파이프라인 플로우

### 전체 처리 흐름

```mermaid
flowchart TD
    Start([🎤 음성 입력 시작]) --> AudioCheck{음성 데이터<br/>유효성 검사}
    
    AudioCheck -->|유효| PreProcess[🔧 오디오 전처리]
    AudioCheck -->|무효| ErrorHandle[❌ 오류 처리]
    
    PreProcess --> SpeakerSep[🗣️ 화자 분리]
    SpeakerSep --> VAD[🎯 VAD 처리]
    VAD --> STT[🗨️ 음성인식<br/>Whisper]
    
    STT --> ConfidenceCheck{음성인식<br/>신뢰도 검사}
    ConfidenceCheck -->|높음 ≥0.7| Intent[🧠 의도 인식]
    ConfidenceCheck -->|낮음 <0.7| LowConfidence[⚠️ 낮은 신뢰도<br/>경고]
    
    LowConfidence --> Intent
    Intent --> IntentCheck{의도 인식<br/>신뢰도 검사}
    
    IntentCheck -->|충분| Dialogue[💬 대화 관리]
    IntentCheck -->|불충분| Fallback[🔄 발음 유사도<br/>처리]
    
    Fallback --> Dialogue
    Dialogue --> Order[🍔 주문 처리]
    Order --> Menu[📋 메뉴 검색]
    Menu --> Response[📞 응답 생성]
    Response --> End([✅ 응답 완료])
    
    ErrorHandle --> End
    
    style ConfidenceCheck fill:#ffeb3b
    style IntentCheck fill:#ff9800
    style Fallback fill:#f44336
```

---

## 🎯 신뢰도 및 판단 알고리즘

### 1. 음성 인식 신뢰도 계산

```mermaid
graph LR
    subgraph "Whisper 세그먼트 분석"
        A[📊 avg_logprob] --> B[🔢 exp 변환]
        B --> C[📏 길이 가중평균]
        C --> D[📈 최종 신뢰도]
    end
    
    subgraph "신뢰도 분류"
        D --> E{신뢰도 값}
        E -->|≥ 0.9| F[🟢 매우 높음]
        E -->|≥ 0.7| G[🔵 높음]
        E -->|≥ 0.5| H[🟡 보통]
        E -->|< 0.5| I[🔴 낮음]
    end
```

**알고리즘 상세:**
```python
def _calculate_confidence(self, segments: list) -> float:
    total_confidence = 0.0
    total_length = 0
    
    for segment in segments:
        # 로그 확률을 실제 확률로 변환
        avg_logprob = segment.get("avg_logprob", -1.0)
        segment_confidence = min(1.0, max(0.0, np.exp(avg_logprob)))
        
        # 세그먼트 길이로 가중평균
        segment_length = len(segment.get("text", ""))
        total_confidence += segment_confidence * segment_length
        total_length += segment_length
    
    return total_confidence / total_length if total_length > 0 else 0.5
```

### 2. 의도 인식 임계값 시스템

```mermaid
graph TD
    subgraph "의도별 임계값"
        A[CANCEL<br/>0.9] --> A1[🚨 최고 보안]
        B[MODIFY<br/>0.8] --> B1[⚡ 높은 정확성]
        C[PAYMENT<br/>0.8] --> C1[💳 금전 거래]
        D[ORDER<br/>0.7] --> D1[🍔 일반 주문]
        E[INQUIRY<br/>0.6] --> E1[❓ 정보 제공]
        F[UNKNOWN<br/>0.0] --> F1[🔄 폴백 처리]
    end
    
    style A fill:#ff5722
    style B fill:#ff9800
    style C fill:#2196f3
    style D fill:#4caf50
    style E fill:#9c27b0
    style F fill:#607d8b
```

**임계값 설정 논리:**
- **CANCEL (0.9)**: 잘못된 취소 방지 - 가장 높은 확신 필요
- **MODIFY/PAYMENT (0.8)**: 주문 변경 및 결제 - 높은 정확성 요구
- **ORDER (0.7)**: 일반 주문 - 표준 임계값
- **INQUIRY (0.6)**: 단순 문의 - 관대한 임계값

---

## 🗣️ 화자 분리 알고리즘

### 고급 AI 모델 기반 분리

```mermaid
flowchart TB
    subgraph "Step 1: Diarization"
        A[🎤 원본 오디오] --> B[🔍 Pyannote<br/>화자 구분]
        B --> C[👥 화자별<br/>세그먼트]
    end
    
    subgraph "Step 2: Source Separation"
        C --> D[🎯 SepFormer<br/>음성 분리]
        D --> E[🗣️ 분리된<br/>음성들]
    end
    
    subgraph "Step 3: Speaker Recognition"
        E --> F[🧬 ECAPA-TDNN<br/>임베딩 추출]
        F --> G[📐 코사인 유사도<br/>계산]
    end
    
    subgraph "Step 4: Selection"
        G --> H{유사도 비교}
        H --> I[🎯 최고 유사도<br/>화자 선택]
    end
    
    style B fill:#e3f2fd
    style D fill:#f3e5f5
    style F fill:#e8f5e8
    style I fill:#fff3e0
```

### 유사도 계산 메커니즘

```mermaid
graph LR
    subgraph "임베딩 비교"
        A[🎭 주 화자<br/>임베딩] --> C[📐 코사인 유사도]
        B[🗣️ 분리음성<br/>임베딩] --> C
        C --> D{유사도 값}
    end
    
    subgraph "품질 판단"
        D -->|≥ 0.7| E[🟢 고품질]
        D -->|≥ 0.5| F[🟡 보통품질]
        D -->|< 0.5| G[🔴 저품질<br/>경고]
    end
```

**코사인 유사도 공식:**
```python
similarity = torch.nn.functional.cosine_similarity(
    main_speaker_embedding, separated_embedding, dim=0
).item()

# 임계값: 0.5 미만 시 품질 경고
if similarity < 0.5:
    print("⚠️ 유사도가 낮음 - 결과 품질 주의")
```

### 폴백 메커니즘

```mermaid
flowchart TD
    A[🚀 고급 모델 시도] --> B{모델 사용<br/>가능?}
    
    B -->|✅ 가능| C[🔬 AI 기반 분리]
    B -->|❌ 불가능| D[⚡ 에너지 기반 분리]
    
    C --> E{분리 성공?}
    E -->|✅ 성공| F[✨ 고품질 결과]
    E -->|❌ 실패| G{폴백 활성화?}
    
    G -->|✅ 활성화| D
    G -->|❌ 비활성화| H[📄 원본 반환]
    
    D --> I[📊 에너지 임계값<br/>분리]
    I --> F
    
    style C fill:#4caf50
    style D fill:#ff9800
    style F fill:#2196f3
```

---

## 🔤 발음 유사도 처리 시스템

### LLM 기반 발음 오류 처리

```mermaid
graph TB
    subgraph "입력 처리"
        A[🗣️ 음성인식 결과] --> B{발음 오류<br/>감지}
    end
    
    subgraph "LLM 프롬프트 처리"
        B -->|오류 있음| C[🧠 GPT-4o<br/>유사도 분석]
        B -->|정확함| D[✅ 직접 처리]
        
        C --> E[📝 발음 패턴<br/>매칭]
        E --> F[🔄 의미 변환]
    end
    
    subgraph "예시 변환"
        G["본품" → "단품"]
        H["휴지" → "취소"]
        I["베그맥" → "빅맥"]
    end
    
    F --> G
    F --> H
    F --> I
    
    style C fill:#e1f5fe
    style E fill:#f3e5f5
```

**발음 유사도 프롬프트 지침:**
```
- 발음 유사도를 고려하여 가장 적절한 의도 선택
- 발음 유사도가 70% 이상인 경우 가장 유사한 의미로 이해
- 이상한 단어 = 유사한 실제 단어로 자동 변환
```

---

## 🍔 메뉴 매칭 시스템

### 검색 알고리즘 계층

```mermaid
flowchart TD
    A[🔍 메뉴 검색 요청] --> B[📝 텍스트 전처리]
    
    B --> C{1차: 정확한<br/>이름 매칭}
    C -->|발견| D[✅ 완전 일치]
    C -->|없음| E{2차: 키워드<br/>검색}
    
    E -->|발견| F[🔤 키워드 매칭]
    E -->|없음| G{3차: 부분<br/>문자열}
    
    G -->|발견| H[📄 부분 매칭]
    G -->|없음| I[❌ 매칭 실패]
    
    D --> J[📊 결과 정렬]
    F --> J
    H --> J
    J --> K[🎯 최종 결과]
    
    style C fill:#4caf50
    style E fill:#2196f3
    style G fill:#ff9800
```

### 키워드 추출 알고리즘

```mermaid
graph LR
    subgraph "텍스트 분석"
        A[📝 입력 텍스트] --> B[🔤 소문자 변환]
        B --> C[✂️ 단어 분리<br/>정규식]
        C --> D[📏 길이 필터링<br/>≥2글자]
    end
    
    subgraph "키워드 생성"
        D --> E[🔑 전체 단어<br/>키워드]
        D --> F[✂️ 부분 문자열<br/>2글자 조합]
        E --> G[📚 키워드 집합]
        F --> G
    end
    
    style C fill:#e3f2fd
    style G fill:#e8f5e8
```

**키워드 추출 예시:**
```
입력: "빅맥세트"
→ 키워드: {"빅맥세트", "빅맥", "맥세", "세트"}

입력: "Big Mac"
→ 키워드: {"big", "mac", "bi", "ig", "ma", "ac"}
```

---

## 📊 성능 모니터링 & 분석

### 신뢰도 분포 분석

```mermaid
pie title 신뢰도 분포 예시
    "Very High (≥0.9)" : 35
    "High (0.7-0.9)" : 40
    "Medium (0.5-0.7)" : 20
    "Low (<0.5)" : 5
```

### 처리 시간 성능 지표

```mermaid
graph TB
    subgraph "성능 메트릭"
        A[⏱️ 음성인식<br/>평균 2.3초]
        B[🧠 의도파악<br/>평균 0.8초]
        C[💬 대화처리<br/>평균 0.5초]
        D[📞 응답생성<br/>평균 0.3초]
    end
    
    subgraph "전체 파이프라인"
        E[🎯 총 처리시간<br/>평균 3.9초]
    end
    
    A --> E
    B --> E
    C --> E
    D --> E
    
    style E fill:#4caf50
```

### 오류 처리 흐름

```mermaid
flowchart TD
    A[❌ 오류 발생] --> B{오류 유형<br/>분류}
    
    B -->|음성인식| C[🎤 STT 오류]
    B -->|의도파악| D[🧠 Intent 오류]
    B -->|시스템| E[⚙️ System 오류]
    
    C --> F[🔄 재시도 유도]
    D --> G[💭 발음 유사도<br/>처리]
    E --> H[🚨 관리자 알림]
    
    F --> I[📝 사용자 피드백]
    G --> I
    H --> I
    
    style B fill:#ff9800
    style I fill:#4caf50
```

---

## 🎛️ 시스템 설정 & 임계값

### 주요 설정값

| 구분 | 파라미터 | 기본값 | 설명 |
|------|----------|--------|------|
| 음성인식 | confidence_threshold | 0.5 | 음성인식 최소 신뢰도 |
| 화자분리 | speaker_similarity | 0.5 | 화자 유사도 임계값 |
| VAD | vad_threshold | 0.2-0.25 | 음성 활동 감지 민감도 |
| 의도인식 | order_confidence | 0.7 | 주문 의도 임계값 |
| 의도인식 | cancel_confidence | 0.9 | 취소 의도 임계값 |
| 발음처리 | pronunciation_similarity | 70% | 발음 유사도 기준 |

### 환경별 최적화

```mermaid
graph TB
    subgraph "조용한 환경"
        A[🔇 VAD: 0.1<br/>매우 민감]
        B[🎯 Confidence: 0.8<br/>높은 기준]
    end
    
    subgraph "보통 환경"
        C[🔉 VAD: 0.25<br/>표준]
        D[🎯 Confidence: 0.7<br/>표준 기준]
    end
    
    subgraph "시끄러운 환경"
        E[🔊 VAD: 0.4<br/>둔감]
        F[🎯 Confidence: 0.6<br/>관대한 기준]
    end
    
    style A fill:#e8f5e8
    style C fill:#fff3e0
    style E fill:#ffebee
```

---

## 🎯 핵심 특징 요약

### 💡 시스템 강점

1. **다층적 신뢰도 관리**: 각 처리 단계별 독립적 신뢰도 검증
2. **적응적 임계값**: 의도별 위험도에 따른 차등 기준 적용
3. **지능적 폴백**: 고급 모델 실패 시 기본 알고리즘 자동 전환
4. **LLM 기반 유연성**: 발음 오류를 자연어 이해로 처리
5. **실시간 모니터링**: 성능 지표 및 오류율 지속적 추적

### 🔄 지속적 개선 포인트

- 화자별 학습 데이터 축적으로 개인화 향상
- 환경 조건별 동적 임계값 조정
- 멀티모달 입력 지원 (음성 + 제스처)
- 감정 분석 기반 서비스 품질 향상

---

*이 문서는 음성 키오스크 시스템의 전체 파이프라인과 신뢰도 알고리즘을 종합적으로 분석한 기술 문서입니다.*