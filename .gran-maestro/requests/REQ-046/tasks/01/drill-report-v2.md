# REQ-046 드릴 런 V2 리포트 — 디에스솔루션 MAIN 재시도 결과

- 작성일: 2026-04-21
- 소속: REQ-046 / PLN-012 Phase C
- 전제: REQ-044 (`--download-assets`) + REQ-045 (init-project 하드닝) 완료 후 재시도

## 1. 요약

REQ-043 실패 후 파이프라인 개선(REQ-044/045) 적용한 재시도. **6섹션 재추출 + asset 다운로드 + gemini HTML/CSS 생성까지는 성공**했으나, 4종 게이트에서 **474건 위반 + CRITICAL 다수** 발견. 더 심각한 건 **validator 들이 exit code 를 올바르게 반환하지 않는 결함**이 드러남.

## 2. 실행 결과

| 단계 | 상태 | 비고 |
|---|---|---|
| 1. 6섹션 재추출 (--download-assets) | ✅ | SVG/PNG 실제 다운로드, local_path 기록 |
| 2. gemini dispatch (재시도 1회) | ⚠️ | 첫 시도는 Gemini API 429 (용량 부족), 2회 시도로 성공 |
| 3. index.html + common.css 생성 | ✅ | 15KB + 16KB |
| 4. img/ 복사 | ❌ | **비어있음** — gemini 가 asset 파일 복사 안 함 |
| 5. figma-validate | ❌ | 474건 위반 (295 CRITICAL), 하지만 **exit 0 반환** |
| 6. validate-semantic --profile basic | ❌ | CRITICAL 존재, 하지만 **exit 0 반환** |
| 7. 수렴 루프 | ⏹ | 재dispatch 중단 (근본 결함 해결이 우선) |

## 3. 발견 갭

### 갭 #7 — **validator 들이 exit code 를 올바르게 반환하지 않음** (CRITICAL 신규)

- `figma-validate.py`: 474건 위반 + CRITICAL 295건 있는데 `exit=0` 반환
- `validate-semantic.py --profile basic`: stdout 에 `❌ CRITICAL 위반이 있습니다. 반드시 수정하세요.` 출력하면서도 `exit=0` 반환
- **영향**: 수렴 루프(`post-impl-verify --converge`)가 exit code 기반으로 재dispatch 여부를 판단하므로 **CRITICAL 위반이 있어도 PASS 로 인식해 수렴 종료**. 파이프라인 전체가 무력화됨.
- **수정 필요**: 두 validator 모두 CRITICAL 건수 > 0 일 때 `sys.exit(1)` 반환 로직 추가
- **우선순위**: **최우선** — 이걸 고치지 않으면 다른 모든 수정이 무의미

### 갭 #8 — validate-semantic 의 `rules/rules.yaml` 상대 경로 버그

- cwd=dev-base 가 아닌 곳에서 호출 시 `FileNotFoundError: rules/rules.yaml`
- `tools/validate-semantic.py:2916` `open(rules_path, encoding="utf-8")` — 하드코딩된 상대경로
- **수정**: `Path(__file__).resolve().parent.parent / 'rules' / 'rules.yaml'` 로 변경

### 갭 #9 — gemini 가 asset 파일을 output/img 로 복사하지 않음 (CRITICAL)

- spec brief 에 "asset 파일들을 `extracted/{section}/{vectors|images}/` → `output/a_main/img/` 로 복사" 명시했으나 gemini 가 무시
- 결과: HTML 에는 `<img src="./img/xxx.svg">` 인데 해당 파일이 실제 img/ 에 없음 (asset_manifest_consistency CRITICAL)
- **수정**: gemini 브리프에서 이 지시를 더 강하게 하거나, PM 이 dispatch 후 자동 복사 스크립트를 실행

### 갭 #10 — gemini 가 asset_manifest `local_path` 형식 미준수 (CRITICAL)

- Manifest 의 local_path: `footer_bk/vectors/I130_11224;118_32115;118_32086.svg` (섹션/vectors/|images/ 하위 구조)
- gemini HTML src: `./img/I134_13603;131_11948;118_31987.svg` (평면 구조 + 다른 ID)
- gemini 가 manifest 를 제대로 참조하지 않고 자체 경로를 생성
- asset_manifest_consistency 검증 실패의 근본 원인

### 갭 #11 — gemini 가 CLAUDE.md 규칙 다수 위반

1. **모든 `<img>` 에 개별 클래스** (`class="Vector-I134_13603_131_11948_118_31987"`) — "모든 HTML 요소에 개별 클래스 부여 금지" 위반
2. **`<img_area>` wrapper 없음** — 이미지 래핑 규칙 위반, 39건 MAJOR
3. **`<p>` 태그 남용**: "T. 010-9015-6056", "F. 031-784-8283", "대표자. 김동석" 등 짧은 라벨에 `<p>` — 규칙 위반
4. **빈 `<div>` 존재** (line 47)
5. **:root 변수 누락** (`--width`, `--padding` 없음)
6. **font-family `pretendard` 46번 반복** (font_family_redundant)
7. **`word-break: keep-all` 미적용** (한국어 규칙)
8. **`font-size: clamp(14px, 1.2vw, 16px)` 베이스 미선언** (basic 프로파일)

→ gemini 가 spec.md 는 읽었지만 인라인 규칙 섹션을 진지하게 적용하지 않음. 아마 긴 프롬프트에 묻혔거나 gemini 모델 특성상 규칙 준수 약함.

### 갭 #12 — Gemini API 용량 가용성 (운영 리스크)

- 첫 시도: `gemini-3.1-pro-preview` 429 (3회 재시도 실패)
- 두번째 시도 (모델 지정 없음, 기본 모델 사용): 성공
- **운영 관점**: mst 워크플로우가 특정 gemini 모델을 강제하면 API 용량 문제로 파이프라인 중단 가능
- **완화**: `resolve-model` 에 fallback 체인 (e.g. `gemini-3.1 → gemini-2.5 → default`) 추가

## 4. 성공한 부분

- REQ-044 의 `--download-assets` 자체는 작동 (6 섹션 SVG 다운로드 정상)
- asset_manifest 에 `local_path` + 실제 SHA-256 기록 정상
- init-project.py (REQ-045) 자동 생성 정상

## 5. PLN-013 후속 작업 후보 (우선순위 순)

1. **(CRITICAL)** validator exit code 수정 (갭 #7)
   - `figma-validate.py`: CRITICAL 건수 > 0 → exit 1
   - `validate-semantic.py`: 동일
   - 단위 테스트 추가
2. **(CRITICAL)** `validate-semantic.py` 상대경로 버그 수정 (갭 #8)
3. **(HIGH)** PM 자동 asset 복사 단계 추가 (갭 #9)
   - `post-impl-verify.py` 에 "asset_manifest local_path → output/a_main/img/ 자동 복사" 옵션
4. **(HIGH)** gemini 브리프 재설계 (갭 #11)
   - 규칙을 짧은 체크리스트로 압축
   - `rules_version: 2` + `rule_ids` 형식 (퍼블리싱 템플릿 v2) 활용
5. **(MEDIUM)** local_path 경로 정규화 (갭 #10)
   - asset_manifest 의 local_path 를 output 기준으로 재매핑하는 헬퍼 추가
6. **(MEDIUM)** gemini 모델 fallback 체인 (갭 #12)

## 6. 평가 — 파이프라인 성숙도

**현재 상태**: **"구조적 결함 (structural defect)"**

- spec 생성·asset 다운로드·코드 생성까지는 작동하나,
- **검증 레이어가 거짓 PASS 를 반환**하므로 수렴 루프가 의미 없음
- gemini 의 규칙 준수가 저조해 자동 생성 결과를 그대로 배포 불가

**드릴 런의 가치**: 극도로 높음. validator exit code 결함은 **파이프라인 v2/v3 이후로 발견되지 않았던 핵심 갭**이며, PLN-013 을 열 충분한 근거다.

## 7. 다음 액션

- REQ-046 상태: `done` (드릴 런 목적 달성 — 갭 확실히 규명)
- PLN-012 상태: `completed` (3 REQ 모두 처리, 드릴 런 결과 리포트화)
- **PLN-013 신규 생성 권장** (validator exit code 수정 + gemini 규칙 준수 개선 중심)
