# Implementation Request — 디에스솔루션 MAIN HTML/CSS (드릴 재시도)

- Request: REQ-046 / Task: 01
- Working Directory: `/mnt/d/위링/2026-04-21 디에스솔루션/`
- Spec Directory: `/mnt/d/위링/2026-04-21 디에스솔루션/extracted/`
- Output Target: `/mnt/d/위링/2026-04-21 디에스솔루션/output/a_main/`

## 구현 컨텍스트

REQ-044 에서 `--download-assets` 기능이 추가되어 이제 `extracted/{section}/vectors/*.svg` 와 `extracted/{section}/images/*.png` 에 실제 asset 파일이 있다. 각 섹션의 `{section}_asset_manifest.json` 에 `local_path` 필드가 있다. 이걸 활용해 디에스솔루션 Figma MAIN 페이지 (6개 섹션: header_b / MV / sec_1 / sec_2 / sec_5 / footer_bk) 를 HTML/CSS 로 구현한다.

## 자기탐색 지시

1. 각 섹션 spec 전체 읽기:
   ```bash
   for f in /mnt/d/위링/2026-04-21\ 디에스솔루션/extracted/*_spec.md; do echo "=== $f ==="; cat "$f"; done
   ```
2. asset manifest 읽어 경로 확인:
   ```bash
   for f in /mnt/d/위링/2026-04-21\ 디에스솔루션/extracted/*_asset_manifest.json; do echo "=== $f ==="; cat "$f"; done
   ```
3. 템플릿 참조: `/mnt/d/dev-base/templates/index.html` (골격), `/mnt/d/dev-base/templates/css/reset.css` (reset)
4. 구현:
   - `output/a_main/index.html`: 6개 섹션 순서대로 (header_b → MV → sec_1 → sec_2 → sec_5 → footer_bk). 의미 있는 클래스명(`main_`, `main_visual`, `main_intro` 등 — `sec_숫자` 금지)
   - `output/a_main/common.css`: 통합 CSS — 한 줄 포맷, hex 전용, flexbox 전용, basic 프로파일
   - `output/a_main/reset.css`: `/mnt/d/dev-base/templates/css/reset.css` 복사
   - `output/a_main/img/`: `extracted/{section}/{vectors|images}/*` 를 여기로 복사 (asset_manifest 의 `local_path` 는 spec 디렉토리 기준이므로 `./img/filename` 으로 재매핑)
5. self-check — 완료 전 아래 모두 YES:
   - 6개 섹션 모두 HTML 반영
   - spec text_nodes[].characters 가 byte-exact 로 HTML 에 (NBSP, `\n` → `<br>`, 연속 공백 보존)
   - frame_nodes 계층 = HTML DOM 계층
   - asset_manifest 의 이미지만 `<img src>` 사용 (AI 합성 금지)
   - CSS 한 줄 포맷, hex 전용, `sec_숫자` 클래스 없음

## 규칙 (CRITICAL)

### CSS
- 한 줄 셀렉터, hex 전용, flexbox 전용, grid/float 금지
- line-height 무단위 비율, letter-spacing em, border-radius 원형 50%/pill 2em
- padding/margin/gap 고정 px (100px 이상만 clamp())
- `sec_1`, `section_01`, `box1` 절대 금지 → 의미 있는 영문명

### HTML
- `<figure>/<figcaption>/<main>/<article>` 금지
- 짧은 라벨은 `<span>`, 95자 초과/줄바꿈 포함 시만 `<p>`
- 모든 요소 개별 클래스 금지 — 부모+태그 선택자 우선
- header/footer 에 페이지 프리픽스 금지

### 구조 불변 원칙
1. text byte-exact (NBSP / 연속 공백 / 줄바꿈 모두 원본)
2. DOM 계층 = spec frame_nodes 계층 (wrapper 임의 삭제 금지)
3. 수치 정확성 (padding/gap 소수점까지)
4. asset_manifest 원본 이미지만

## 완료 조건

작업 완료 후 아래 명령 전부 exit 0:

```bash
cd "/mnt/d/위링/2026-04-21 디에스솔루션"
python3 /mnt/d/dev-base/tools/figma-validate.py --spec-dir extracted/ --html output/a_main/index.html --css output/a_main/common.css
python3 /mnt/d/dev-base/tools/validate-semantic.py --html output/a_main/index.html --css output/a_main/common.css --profile basic
```

git commit 금지 (PM 이 후속 처리).
