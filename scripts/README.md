# Figma 추출 스크립트 실행 가이드

이 스크립트는 브레인바디 페이지 기준으로 다음 규칙을 반영해 HTML을 생성합니다.
- 라벨형 텍스트(`BrainBody`, `MRI`, `그린몰` 계열)는 `span` 우선
- 문단형 텍스트만 `p` 판정
- `characterStyleOverrides` 누적 병합 규칙 적용
- 텍스트 태그 과잉(`p`) 방지

## 실행 예시

```bash
cd /mnt/d/dev-base
python3 scripts/figma_extract_to_html.py \
  /mnt/c/Users/water/Downloads/260212_그린몰_랜딩적용(브레인바디)/html/figma_grinmall_brianbody_260212_page.json \
  /mnt/c/Users/water/Downloads/260212_그린몰_랜딩적용(브레인바디)/html/index.html \
  -o /mnt/c/Users/water/Downloads/260212_그린몰_랜딩적용(브레인바디)/html/index.html
```

## 다른 Codex AI에게 요청할 때 권장 문구

- 동일 규칙으로 재추출해 달라  
`/mnt/d/dev-base/scripts/figma_extract_to_html.py`를 `rules`의 현재 브레인바디 규칙 기준으로 실행해서
`/mnt/c/Users/water/Downloads/260212_그린몰_랜딩적용(브레인바디)/html/index.html`을 갱신해줘.

- 새 JSON 기준으로 반복 적용해 달라  
지금 폴더의 스크립트로 `python3 scripts/figma_extract_to_html.py <figma_json> <template_html> -o <output_html>` 형태로 실행해 결과물과 `git diff`를 확인해 달라고 요청하면 됩니다.

## 실행 전 확인

- 의존성: `beautifulsoup4` 설치 시 더 정교한 치환, 미설치 시 정규식 치환으로 동작
- 출력 결과는 템플릿 기준 `<section class='container'>` 또는 `<main>` 내부에만 주입됩니다.

## 참고
- 공통 추출 규칙: `rules/common.md`
- 랜딩 규칙: `rules/landing.md`
- 브레인바디 전용 규칙: `rules/brainbody_extraction_automation.md`
