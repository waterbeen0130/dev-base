> AUTO-GENERATED — critic: claude | IDN-002

# 비평 — IDN-002

## opinion-figma-fidelity(codex).md

- **근거 약함**: `842:196`의 `images:{}` 를 "누락 증거"로 제시하나, `images` 딕셔너리는 Figma token 미전달 시 빈 `{}`가 되므로 추출 로직 결함인지 API 응답 문제인지 구분되지 않는다.
- **추측 기반**: "vector_nodes 없어 fidelity 불가"라고 했으나 `figma-section-spec.py:373–418`에 `normalize_vector_node`가 이미 구현되어 있다. 샘플 섹션에 해당 노드가 없는 것이 이유다.
- **over-engineering**: `constraints` + absolute 배치 spec 추가는 flexbox 전용 규칙(CLAUDE.md)과 충돌하며, 디자이너 의도와 CSS 관행 불일치를 spec으로 해결할 수 없다.

## opinion-schema(gemini).md

- **근거 약함**: Pydantic SSOT 제안이 "Python 기반이므로 가능"만 근거다. 두 스크립트는 별개 프로세스이므로 공유 패키지 없이 import만으로 동작하지 않는다. 도입 비용 미서술.
- **over-engineering**: 배열 좌표 강제 정렬은 Figma 노드 순서(z-order 반영)를 무시해 HTML DOM 순서가 틀어질 수 있다.

## opinion-risk(claude).md — figma-fidelity와 충돌

risk #5("VERTICAL itemSpacing → gap 금지 규칙 충돌")는 figma-fidelity Top5("layoutSizing + layoutGrow 추가")와 **방향이 상반된다.** 한쪽은 필드 추가, 다른 쪽은 추가하면 규칙 충돌이라고 경고한다. PM이 우선순위를 결정하지 않으면 합성 스펙이 모순을 포함하게 된다.

## 5개 의견 전체의 공통 누락

- **디자이너 피드백 루프 부재**: 렌더링 불가 속성(FILL + absolute 혼용)이 있을 때 파이프라인이 디자이너에게 어떻게 알리는지 아무도 다루지 않았다.
- **로컬 폰트 렌더링 차이**: `lineHeightRatio ±0.05` 허용 오차는 OS별 렌더링 차이(Windows vs macOS ±0.1 이상)를 반영하지 않는다.
- **CI 비용**: validate-semantic.py(3051줄) 실행 시간 + Figma API latency가 파이프라인에 미치는 영향을 분석한 의견이 없다.

## "완전 동일한 추출물" 목표 자체의 문제

Figma는 래스터 합성 렌더러이고 브라우저는 레이아웃 엔진이다. 픽셀 완전성은 달성 불가 목표다. 5개 의견 모두 이 전제를 비판하지 않고 "필드 추가"로 해결하려 한다. 현재 9개 검증 카테고리가 이미 **의미론적 동일성** 방향으로 설계되어 있다는 점이 강점이며, 과도한 필드 확장보다 이 방향을 유지하는 것이 실용적이다.

---

## 합성 전 PM이 반드시 되짚어야 할 반론 Top 3

1. **fills[] 상세화 전 하위호환 마이그레이션 전략 없으면 기존 extracted/ spec.json 전량 무효화.** 필드 추가 우선순위 전에 schema_version 분기 + 마이그레이션 스크립트 범위를 먼저 확정해야 한다.

2. **VERTICAL frame itemSpacing → CSS 변환 규칙을 spec-level 정책으로 결정하지 않으면 gap 금지 규칙과의 충돌이 재dispatch 루프를 일으킨다.** fidelity vs rules.yaml 우선순위를 명문화해야 외주 에이전트가 일관된 판단을 내린다.

3. **Pydantic SSOT는 현 단계 over-engineering일 가능성이 높다.** fills 구조화·effects 추가를 단순 dict 확장으로 먼저 적용하고, 검증 안정화 이후 Pydantic 전환을 검토하는 순서가 리스크 최소화 경로다.
