# Figma 추출 스크립트 실행 가이드

이 스크립트는 Figma JSON을 HTML로 변환할 때 규칙(profile)을 선택해 반복 가능한 추출 품질을 맞춥니다.

- `brainbody`: 브레인바디 랜딩처럼 라벨 보존이 중요한 페이지에 맞춘 엄격 모드
- `general`: 일반 페이지용 기본 모드(라벨 후보를 줄이고 문단 판정을 상대적으로 넓게 적용)
- `auto`(기본): 파일명 기반으로 자동 전환
  - 파일명에 `brainbody`/`brianbody`가 있으면 `brainbody`
  - 그 외에는 `general`

공통 동작
- 라벨형 텍스트 판단에서 과도한 `<p>` 분류를 줄임
- `characterStyleOverrides` 누적 병합 규칙 유지
- 텍스트 태그 과잉(`p`)를 줄이도록 보정

## 실행 예시

```bash
cd /mnt/d/dev-base
python3 scripts/figma_extract_to_html.py \
  /mnt/c/Users/water/Downloads/260212_그린몰_랜딩적용(브레인바디)/html/figma_grinmall_brianbody_260212_page.json \
  /mnt/c/Users/water/Downloads/260212_그린몰_랜딩적용(브레인바디)/html/index.html \
  -o /mnt/c/Users/water/Downloads/260212_그린몰_랜딩적용(브레인바디)/html/index.html

# 자동(profile=auto, 기본값)
python3 scripts/figma_extract_to_html.py \
  <figma_json_path> <template_html_path> -o <output_html_path>

# 브레인바디 규칙 강제 적용
python3 scripts/figma_extract_to_html.py \
  <figma_json_path> <template_html_path> -o <output_html_path> --profile brainbody

# 일반 페이지 규칙 적용
python3 scripts/figma_extract_to_html.py \
  <figma_json_path> <template_html_path> -o <output_html_path> --profile general
```

## 다른 Codex AI에게 요청할 때 권장 문구

- 동일 규칙으로 재추출해 달라  
`/mnt/d/dev-base/scripts/figma_extract_to_html.py`를 실행하고 `--profile`을 명시해서 처리해줘.
예: 브레인바디 페이지라면 `--profile brainbody`, 일반 페이지라면 `--profile general`.

- 새 JSON 기준으로 반복 적용해 달라  
`python3 scripts/figma_extract_to_html.py <figma_json> <template_html> -o <output_html> --profile <auto|brainbody|general>` 형태로 실행해 결과물을 확인해달라고 요청해.

## 실행 전 확인

- 의존성: `beautifulsoup4` 설치 시 더 정교한 치환, 미설치 시 정규식 치환으로 동작
- 출력 결과는 템플릿 기준 `<section class='container'>` 또는 `<main>` 내부에만 주입됩니다.

## 참고
- 공통 추출 규칙: `rules/common.md`
- 랜딩 규칙: `rules/landing.md`
- 브레인바디 전용 규칙: `rules/brainbody_extraction_automation.md`
