# Implementation Plan

- [ ] 1. 프로젝트 구조 설정 및 기본 모델 정의









  - src/testing/ 및 src/microphone/ 디렉토리 생성
  - TestCase, TestResult, MicrophoneConfig 등 핵심 데이터 모델 클래스 구현
  - 기본 인터페이스 정의
  - _Requirements: 1.1, 2.1, 3.1, 4.1_

- [x] 2. 테스트케이스 생성 및 실행 시스템 구현


















  - TestCaseGenerator 클래스로 맥도날드 특화 테스트케이스 생성 ("상스치콤", "베토디" 등 은어, 반말, 복합 의도 포함)
  - TestRunner 클래스로 테스트케이스 실행 및 결과 수집
  - 기존 VoiceKioskPipeline.process_text_input()과 연동하여 테스트 실행
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 3. 테스트 결과 분석 및 보고서 생성 구현














  - ResultAnalyzer로 성공률, 처리 시간, 의도별 정확도 분석
  - ReportGenerator로 텍스트 및 마크다운 보고서 생성
  - 통계 데이터 포맷팅 및 오류 분류 기능
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. VAD 기반 마이크 입력 시스템 구현





  - VADProcessor 클래스로 Silero VAD 모델 통합 및 음성 활동 감지
  - AudioRecorder 클래스로 sounddevice 기반 실시간 녹음 및 WAV 파일 생성
  - reference/input_as_mic.py의 로직을 참조하여 구현
  - _Requirements: 2.1, 2.2, 2.3, 4.1_

- [x] 5. MicrophoneInputManager 통합 및 오류 처리





  - MicrophoneInputManager로 VAD, 녹음, 실시간 처리 통합
  - 마이크 하드웨어 오류, VAD 모델 로딩 실패 등 오류 처리
  - 마이크 설정 조정 및 상태 모니터링 기능
  - _Requirements: 2.4, 4.2, 4.3, 4.4, 4.5_

- [x] 6. VoiceKioskPipeline 확장 및 메인 인터페이스 통합





  - VoiceKioskPipeline에 run_test_mode() 및 run_microphone_mode() 메서드 추가
  - 기존 process_audio_input() 메서드와 마이크 입력 연동
  - main.py에 테스트 모드 및 마이크 모드 선택 옵션 추가
  - _Requirements: 1.5, 2.4, 2.5_

- [x] 7. 설정 시스템 확장 및 의존성 설치





  - ConfigManager에 TestConfiguration 및 마이크 설정 추가
  - requirements.txt에 torch, sounddevice, scipy 추가
  - 환경 변수를 통한 설정 관리 및 검증
  - _Requirements: 4.1, 4.2_

- [x] 8. 기본 테스트 및 문서화





  - 핵심 기능에 대한 기본 테스트 작성 (TestCaseGenerator, MicrophoneInputManager)
  - 사용자 가이드 및 API 문서 작성
  - 실제 사용 예제 및 설정 가이드 제공
  - _Requirements: 1.1, 2.1, 3.5, 4.5_