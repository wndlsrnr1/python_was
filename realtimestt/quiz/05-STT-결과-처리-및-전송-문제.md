# STT 결과 처리 및 전송 문제

## 객관식 문제

### 1. STT 결과 파이프라인의 처리 순서는?

① gRPC 응답 → 메시지 포맷 변환 → 결과 파싱 → WebSocket 전송  
② gRPC 응답 → 결과 파싱 → 메시지 포맷 변환 → WebSocket 전송  
③ 결과 파싱 → gRPC 응답 → 메시지 포맷 변환 → WebSocket 전송  
④ 메시지 포맷 변환 → gRPC 응답 → 결과 파싱 → WebSocket 전송  

**정답**: ②  
**해설**: STT 결과는 gRPC 응답을 받아 결과를 파싱하고, WebSocket 메시지 포맷으로 변환한 후 클라이언트로 전송합니다.

---

### 2. Handler 패턴의 장점이 아닌 것은?

① 단일 책임 원칙 준수  
② Handler가 Consumer에 직접 의존하여 강한 결합  
③ 테스트 용이성  
④ 재사용성  

**정답**: ②  
**해설**: Handler 패턴은 Consumer에 직접 의존하지 않고 `send_func`를 파라미터로 받아 느슨한 결합을 유지합니다. 강한 결합은 장점이 아닙니다.

---

### 3. 임시 결과(interim)와 최종 결과(final)의 차이점은?

① 임시 결과는 변경되지 않지만 최종 결과는 변경될 수 있다  
② 임시 결과는 변경될 수 있지만 최종 결과는 변경되지 않는다  
③ 둘 다 변경될 수 있다  
④ 둘 다 변경되지 않는다  

**정답**: ②  
**해설**: 임시 결과(interim)는 발화 도중의 부분적인 인식 결과로 변경될 수 있지만, 최종 결과(final)는 완성된 발화 부분에 대한 확정된 결과로 변경되지 않습니다.

---

### 4. Context 전달 패턴의 장점이 아닌 것은?

① 명시적 의존성  
② 함수가 어떤 정보를 필요로 하는지 명확  
③ SessionContext에 직접 의존  
④ 테스트 용이성  

**정답**: ③  
**해설**: Context 전달 패턴은 SessionContext에 직접 의존하지 않고 필요한 정보를 함수 파라미터로 명시적으로 전달합니다. 이는 장점입니다.

---

### 5. WebSocket 메시지 포맷에서 시퀀스 번호는 어디서 조회하나요?

① gRPC 응답에서  
② SessionContext에서  
③ STT 설정에서  
④ 오디오 큐에서  

**정답**: ②  
**해설**: 시퀀스 번호는 `get_sequence_number` 함수를 통해 SessionContext에서 조회합니다. 이는 메시지 순서를 추적하는 데 사용됩니다.

---

## 빈칸 채우기

### 6. Handler 패턴에서 ResponseHandler는 Consumer에 직접 의존하지 않고 (    )를 파라미터로 받습니다.

**정답**: send_func  
**해설**: ResponseHandler는 Consumer에 직접 의존하지 않고 `send_func`를 파라미터로 받아 느슨한 결합을 유지합니다.

---

### 7. STT 결과 메시지의 type 필드는 (    )로 설정됩니다.

**정답**: transcription  
**해설**: STT 결과를 WebSocket으로 전송할 때 메시지의 `type` 필드는 `"transcription"`으로 설정됩니다.

---

### 8. 임시 결과는 (    ) 피드백을 제공하고, 최종 결과는 (    ) 전사본 저장에 사용됩니다.

**정답**: 실시간, 최종  
**해설**: 임시 결과는 실시간 자막이나 진행 상황 표시에 사용되고, 최종 결과는 최종 전사본 저장이나 분석에 사용됩니다.

---

### 9. STTHandler는 (    )를 통해 SessionContext에서 시퀀스 번호를 조회합니다.

**정답**: get_sequence_number  
**해설**: `get_sequence_number`는 Callable 함수로 전달되어 SessionContext에서 시퀀스 번호를 조회합니다.

---

### 10. Handler 간 의존성에서 MessageHandler는 (    )를 참조하지만, ResponseHandler와 STTHandler는 (    )합니다.

**정답**: Consumer, 독립적  
**해설**: MessageHandler는 Consumer 참조가 필요하지만, ResponseHandler와 STTHandler는 독립적이며 `send_func`를 파라미터로 받습니다.

---

## O/X 문제

### 11. WebSocket 전송 실패는 로깅만 하고 계속 진행한다.

**정답**: O  
**해설**: WebSocket 전송 실패는 로깅만 하고 계속 진행합니다. 다음 결과는 정상적으로 전송될 수 있기 때문입니다.

---

### 12. Handler 패턴을 사용하면 각 Handler가 하나의 책임만 가져 테스트가 용이하다.

**정답**: O  
**해설**: Handler 패턴은 단일 책임 원칙을 준수하여 각 Handler가 하나의 책임만 가지므로, 각 Handler를 독립적으로 테스트할 수 있습니다.

---

## 서술형 문제

### 13. Handler 패턴의 장점을 설명하세요.

**정답**:  
Handler 패턴의 장점은 다음과 같습니다:
1. **단일 책임 원칙**: 각 Handler가 하나의 책임만 가집니다.
2. **테스트 용이성**: 각 Handler를 독립적으로 테스트할 수 있습니다.
3. **재사용성**: Handler를 다른 Consumer에서도 사용할 수 있습니다.
4. **유지보수성**: 변경 사항이 해당 Handler에만 영향을 미칩니다.
5. **느슨한 결합**: Handler가 Consumer에 직접 의존하지 않고 함수를 파라미터로 받습니다.

**해설**: Handler 패턴은 코드 구조를 개선하고 유지보수성을 향상시킵니다.

