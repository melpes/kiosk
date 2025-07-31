# 🧪 테스트 데이터 설정 파일 관리 가이드

홈 디렉토리에서 테스트 모드에서 사용되는 예시 데이터들을 별도 파일로 관리할 수 있도록 설정했습니다.

## 📁 파일 구조

```
test_config/
├── test_data_config.json      # 테스트 데이터 설정 파일
├── manage_test_data.py        # 설정 파일 관리 도구
├── test_config_example.py     # 사용 예제
└── TEST_DATA_README.md        # 이 파일
```

## 🚀 빠른 시작

### 1. 설정 파일 확인
```bash
python test_config/manage_test_data.py status
```

### 2. 은어 목록 확인
```bash
python test_config/manage_test_data.py slang
```

### 3. 메뉴 목록 확인
```bash
python test_config/manage_test_data.py menu
```

## 🔧 관리 도구 사용법

### 기본 명령어
```bash
python test_config/manage_test_data.py [명령] [옵션]
```

### 사용 가능한 명령어

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `status` | 현재 설정 상태 표시 | `python test_config/manage_test_data.py status` |
| `slang` | 은어 목록 표시 | `python test_config/manage_test_data.py slang` |
| `menu` | 메뉴 목록 표시 | `python test_config/manage_test_data.py menu` |
| `add-slang` | 은어 추가 | `python test_config/manage_test_data.py add-slang "새은어" "전체메뉴명"` |
| `remove-slang` | 은어 제거 | `python test_config/manage_test_data.py remove-slang "상스치콤"` |
| `add-menu` | 메뉴 추가 | `python test_config/manage_test_data.py add-menu "새메뉴"` |
| `remove-menu` | 메뉴 제거 | `python test_config/manage_test_data.py remove-menu "빅맥"` |
| `add-edge` | 엣지 케이스 추가 | `python test_config/manage_test_data.py add-edge "새엣지케이스"` |
| `reset` | 기본 설정으로 초기화 | `python test_config/manage_test_data.py reset` |
| `backup` | 설정 파일 백업 | `python test_config/manage_test_data.py backup` |

## 📋 설정 파일 구조

### test_data_config.json
```json
{
  "slang_mappings": {
    "상스치콤": "상하이 스파이시 치킨버거 콤보",
    "베토디": "베이컨 토마토 디럭스",
    "빅맥콤": "빅맥 콤보",
    ...
  },
  "menu_items": [
    "빅맥",
    "상하이 스파이시 치킨버거",
    "베이컨 토마토 디럭스",
    ...
  ],
  "quantity_expressions": [
    "한 개",
    "하나",
    "1개",
    "두 개",
    ...
  ],
  "option_expressions": [
    "라지로",
    "미디움으로",
    "세트로",
    "콤보로",
    ...
  ],
  "informal_patterns": [
    "{menu} 줘",
    "{menu} 하나 줘",
    "{menu} 주문할게",
    ...
  ],
  "complex_patterns": [
    "빅맥 주문하고 치즈버거는 취소해주세요",
    "치즈버거를 빅맥으로 바꾸고 콜라도 추가해주세요",
    ...
  ],
  "edge_cases": [
    "",
    "아아아아아",
    "123456789",
    "피자 주문하겠습니다",
    ...
  ],
  "test_config": {
    "max_tests_per_category": 50,
    "include_slang": true,
    "include_informal": true,
    "include_complex": true,
    "include_edge_cases": true,
    "timeout_seconds": 30
  }
}
```

## 🎯 실제 사용 예제

### 1. 새로운 은어 추가
```bash
# 새로운 은어 추가
python test_config/manage_test_data.py add-slang "맥스파이시" "맥스파이시 상하이버거"

# 추가된 은어 확인
python test_config/manage_test_data.py slang
```

### 2. 새로운 메뉴 추가
```bash
# 새로운 메뉴 추가
python test_config/manage_test_data.py add-menu "더블치즈버거"

# 추가된 메뉴 확인
python test_config/manage_test_data.py menu
```

### 3. 새로운 엣지 케이스 추가
```bash
# 새로운 엣지 케이스 추가
python test_config/manage_test_data.py add-edge "한글과 영어 혼용: Big Mac 주세요"
```

### 4. 설정 백업
```bash
# 자동 백업 (타임스탬프 포함)
python test_config/manage_test_data.py backup

# 사용자 지정 이름으로 백업
python test_config/manage_test_data.py backup my_backup_config.json
```

## 🔄 프로젝트에서 사용하기

### TestCaseGenerator에서 커스텀 설정 파일 사용
```python
from src.testing.test_case_generator import TestCaseGenerator
from pathlib import Path

# test_config 디렉토리의 설정 파일 사용
project_root = Path(__file__).parent.parent
config_file = project_root / "test_config" / "test_data_config.json"

# 커스텀 설정 파일로 초기화
generator = TestCaseGenerator(config_file_path=str(config_file))

# 테스트케이스 생성
test_cases = generator.generate_mcdonald_test_cases()
```

## 📊 테스트 카테고리

### 1. 🗣️ 은어 테스트 (slang)
- **설정**: `slang_mappings`
- **예시**: "상스치콤 주세요", "베토디 하나"
- **목적**: 맥도날드 은어 인식 테스트

### 2. 💬 반말 테스트 (informal)
- **설정**: `informal_patterns`
- **예시**: "빅맥 줘", "치즈버거로 바꿔줘"
- **목적**: 반말 입력 인식 테스트

### 3. 🔄 복합 의도 테스트 (complex)
- **설정**: `complex_patterns`
- **예시**: "빅맥 주문하고 치즈버거는 취소해주세요"
- **목적**: 여러 의도가 섞인 입력 테스트

### 4. 📝 일반 테스트 (normal)
- **설정**: `menu_items`, `quantity_expressions`, `option_expressions`
- **예시**: "빅맥 세트 하나 주문하겠습니다"
- **목적**: 일반적인 주문 패턴 테스트

### 5. ⚠️ 엣지 케이스 (edge)
- **설정**: `edge_cases`
- **예시**: "", "피자 주문하겠습니다", "빅맥!!! 주세요@@@"
- **목적**: 예외 상황 처리 테스트

## 💡 팁과 주의사항

### ✅ 권장사항
- 정기적으로 설정 파일을 백업하세요
- 새로운 은어나 메뉴를 추가할 때는 의미있는 이름을 사용하세요
- 엣지 케이스는 실제 사용자가 입력할 수 있는 예외 상황을 고려하세요

### ⚠️ 주의사항
- 설정 파일을 수정한 후에는 테스트를 다시 실행해야 합니다
- 은어 매핑은 정확한 전체 메뉴명으로 설정해야 합니다
- 패턴에서 `{menu}`는 실제 메뉴명으로 자동 치환됩니다

### 🔧 문제 해결
- 설정 파일이 없으면 기본 설정으로 자동 생성됩니다
- JSON 형식 오류가 있으면 기본 설정으로 초기화됩니다
- 백업 파일을 사용하여 이전 설정을 복원할 수 있습니다

## 📞 지원

문제가 발생하거나 추가 기능이 필요하면:
1. 설정 파일을 백업하세요
2. `python test_config/manage_test_data.py status`로 현재 상태를 확인하세요
3. 필요시 `python test_config/manage_test_data.py reset`으로 초기화하세요

---

**마지막 업데이트**: 2024년 12월 