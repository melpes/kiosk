# 제거된 패키지들과 제거 이유

## 🗑️ 제거된 패키지들 (총 56개 → 22개로 축소)

### **자동 설치되는 의존성 패키지들**
- `aiohappyeyeballs`, `aiohttp`, `aiosignal` → fastapi/uvicorn이 자동 설치
- `async-timeout`, `frozenlist`, `multidict`, `yarl` → aiohttp 의존성
- `attrs`, `certifi`, `charset-normalizer`, `idna`, `urllib3` → requests 의존성
- `h11`, `httpcore`, `httpx`, `sniffio` → fastapi/uvicorn 의존성
- `annotated-types`, `pydantic_core` → pydantic 의존성
- `packaging`, `platformdirs`, `filelock` → torch/transformers 의존성
- `tokenizers`, `safetensors`, `huggingface-hub` → transformers 의존성
- `tiktoken` → openai 의존성
- `six`, `pytz`, `tzdata` → python-dateutil 의존성

### **코드에서 직접 사용되지 않는 패키지들**
- `datasets` → HuggingFace 데이터셋 (현재 사용 안함)
- `pandas`, `pyarrow`, `pyarrow-hotfix` → 데이터 분석 (현재 사용 안함)
- `scikit-learn` → 머신러닝 (현재 사용 안함)
- `networkx` → 그래프 분석 (현재 사용 안함)
- `scipy` → 과학 계산 (librosa가 자동 설치)
- `sympy`, `mpmath` → 수학 계산 (현재 사용 안함)
- `numba`, `llvmlite` → JIT 컴파일 (librosa 최적화용, 자동 설치)

### **오디오 처리 관련 중복/불필요**
- `audioread` → librosa가 자동 설치
- `soxr` → 리샘플링 (librosa 내장 기능 사용)
- `pooch` → 데이터 다운로드 (librosa 의존성)
- `lazy_loader` → 지연 로딩 (librosa 의존성)
- `joblib`, `threadpoolctl` → 병렬 처리 (scikit-learn 의존성)

### **기타 유틸리티**
- `decorator` → 데코레이터 유틸리티 (현재 사용 안함)
- `dill` → 객체 직렬화 (현재 사용 안함)
- `more-itertools` → 이터레이터 유틸리티 (현재 사용 안함)
- `tqdm` → 진행률 표시 (현재 사용 안함)
- `xxhash` → 해시 함수 (현재 사용 안함)
- `msgpack` → 직렬화 (현재 사용 안함)
- `multiprocess` → 멀티프로세싱 (현재 사용 안함)

### **테스트 관련**
- `iniconfig`, `pluggy`, `tomli`, `exceptiongroup` → pytest 의존성
- `distro` → 시스템 정보 (현재 사용 안함)

### **윈도우 전용**
- `win32_setctime` → Windows 파일 시간 설정 (선택적)
- `cffi`, `pycparser` → C 확장 빌드 (자동 설치)

### **Jinja2 관련**
- `Jinja2`, `MarkupSafe` → 템플릿 엔진 (현재 사용 안함)

## 📊 **최적화 결과**
- **이전**: 96줄 (약 56개 패키지)
- **이후**: 34줄 (22개 패키지) 
- **축소율**: 63% 감소
- **설치 시간**: 대폭 단축 예상
- **의존성 충돌**: 최소화