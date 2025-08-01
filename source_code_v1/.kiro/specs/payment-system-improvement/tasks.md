# Implementation Plan

- [x] 1. DialogueManager에 결제 처리 tool 추가





  - DialogueManager 클래스에 process_payment 메서드 구현
  - print문을 사용하여 결제 진행 과정을 단계별로 표시
  - 주문 요약 정보를 받아서 결제 완료 메시지 반환
  - _Requirements: 1.1, 2.1, 2.2, 2.3_

- [ ] 2. DialogueManager에 결제 상태 관리 기능 추가




  - 세션별 결제 확인 대기 상태를 추적하는 딕셔너리 추가
  - 결제 확인 상태 설정 및 해제 메서드 구현
  - 세션 종료 시 결제 상태 정리 로직 추가
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 3. 결제 의도 처리 로직 개선




  - _handle_payment_intent 메서드에서 결제 확인 상태 확인 로직 추가
  - 긍정적 응답("네", "예", "알겠다", "확인") 감지 시 process_payment tool 호출
  - 결제 완료 후 상태 초기화 및 새 주문 준비 로직 구현
  - _Requirements: 1.1, 1.2, 1.3_

- [ ] 4. OrderManager의 주문 추가 메시지 개선




  - add_item 메서드의 성공 메시지에 세부 옵션 정보 포함
  - "빅맥 단품 1개", "빅맥 세트 1개" 형식으로 메시지 포맷팅
  - 옵션이 없는 경우와 있는 경우를 구분하여 처리
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 5. 주문 성공 응답 생성 로직 개선




  - _generate_order_success_response 메서드에서 세부 옵션 표시
  - 여러 항목 추가 시에도 각 항목의 옵션을 명확하게 구분
  - 동일 메뉴의 다른 옵션을 별도 항목으로 표시
  - _Requirements: 3.1, 3.2, 3.3_
-

- [ ] 6. 결제 확인 응답에서 긍정 응답 감지 개선



  - _generate_contextual_response 메서드에서 결제 상태 확인
  - 결제 확인 대기 중일 때 긍정 응답 패턴 매칭 강화
  - LLM 응답 대신 직접 결제 처리로 분기하는 로직 구현
  - _Requirements: 1.1, 1.2, 4.2_