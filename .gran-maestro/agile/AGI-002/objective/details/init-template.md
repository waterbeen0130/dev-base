<!-- source-mapping: original=Q&A 대화 sections=[DOD-005] -->
# init-project.py — 새 룰 강제 CLAUDE.md 템플릿

> 이 문서는 objective.md의 상세 참조 문서입니다.
> 관련 DoD: DOD-005

## 개요

`tools/init-project.py` 가 새 프로젝트 초기화 시 배포할 CLAUDE.md 템플릿을 정의. 이 템플릿이 페이지 prefix / 공통 영역 prefix 없음 / 시멘틱 마크업 / 들여쓰기 / hex/em/px 같은 새 룰을 처음부터 강제하도록 설계.

## 설계 결정

### AD: 템플릿 1개 (publishing) 만 유지
- **결정**: basic / landing 둘 다 같은 베이스 CLAUDE.md 사용 + project-type 별 차이만 부분 추가
- **근거**: 룰 일관성 유지. 디에스솔루션 같은 landing 도, 일반 sub 페이지 basic 도 같은 컨벤션
- **영향 범위**: dev-base/rules/templates/

## 상세 명세

### init-project.py 가 배포할 CLAUDE.md 템플릿 핵심 내용

```markdown
# Claude 규칙 (이 프로젝트)

## 응답 언어
- 한국어
- 코드 주석: 영어만

## 절대 금지
- generate.py / json-to-html.py 같은 자동 코드 생성 스크립트 작성
- 자동 재시도 / auto-repair 루프 사용 (post-impl-verify --converge 등)
- POLICY-1 (VERTICAL frame margin-bottom 강제)
- 도구 단위 테스트 통과 = 파이프라인 통과로 간주
- Figma 노드명 (header_b, footer_bk, sec_1, _v2 등) 을 클래스명에 박기
- site_, g_, common_ 같은 추측 prefix 사용

## CSS / HTML 규칙
- **클래스 명명**:
  - 공통 영역: `.header`, `.footer`, `.logo`, `.gnb`, `.utils`, `.sns`, `.copyright` (prefix 없음)
  - 페이지 전용: `{페이지명}_{역할}` 패턴 (예: `main_mv`, `main_intro`, `sub_about`)
  - 공통 컴포넌트 충돌 방지: `.header .logo`, `.footer .logo` 식 부모 스코핑
- **HTML 들여쓰기**: 4-space, 시멘틱 마크업 강제 (`<nav><ul><li><a>`)
- **CSS 셀렉터**: 한 줄 형식
- **색상**: hex 만 (`#fff`, `#212121`), 투명도 필요 시만 rgba()
- **font-size**: landing px 만, basic 은 PC rem + 모바일 px
- **letter-spacing**: em 단위
- **line-height**: 무단위 비율
- **레이아웃**: flexbox 전용 (Grid 금지)
- **padding/margin/gap**: 고정 px (≥100px 만 clamp)

## Figma 워크플로우 (이 프로젝트에서 강제)

1. `python3 D:/dev-base/tools/figma-section-spec.py --file-key K --node-id N --output extracted/`
2. `python3 D:/dev-base/tools/figma-png-download.py --file-key K --node-ids N1,N2,... --output figma-png/ --include-fills`
3. `python3 D:/dev-base/tools/asset-copy.py --extracted extracted/ --img img/`
4. `python3 D:/dev-base/tools/select-ai.py --extracted extracted/ --figma-png figma-png/ --img img/ --project-type {basic|landing}` → 외주 AI 선정
5. 선정된 AI 에게 spec.json (정확한 값) + PNG (시각 참조) 전달 → HTML/CSS 생성
6. `python3 D:/dev-base/tools/pm-verify.py --spec-dir extracted/ --html index.html --css css/common.css --img img/ --profile {basic|landing}`
7. Playwright 1920px 렌더 → 사용자 시각 비교

## 검증
- pm-verify 실행 후 컨벤션 + broken link 모두 PASS 여야 commit
- 도구 단위 테스트만 통과한 채 보고 금지 (end-to-end 1 페이지 + pm-verify 통과 후 보고)
```

### init-project.py 변경 사항

```python
# 새로 추가:
def write_claude_md(project_dir, project_type):
    template = read_template(f"templates/CLAUDE-{project_type}.md")
    target = project_dir / "CLAUDE.md"
    if target.exists():
        # 기존 CLAUDE.md 가 있으면 .bak 으로 백업
        target.rename(target.with_suffix(".md.bak"))
    target.write_text(template, encoding="utf-8")

def verify_claude_md(project_dir):
    """배포 후 키워드 검증"""
    content = (project_dir / "CLAUDE.md").read_text(encoding="utf-8")
    required_keywords = [
        "공통 영역: `.header`",
        "페이지 전용: `{페이지명}_{역할}",
        "들여쓰기: 4-space",
        "시멘틱 마크업 강제",
        "hex 만",
        "letter-spacing: em",
        "flexbox 전용",
        "figma-png-download.py",
        "asset-copy.py",
        "pm-verify.py",
        "select-ai.py",
        "POLICY-1",  # 금지 키워드
    ]
    missing = [k for k in required_keywords if k not in content]
    return missing
```

### 인자

```bash
python3 tools/init-project.py {project_dir} --type basic|landing --publishing
```

기존 인자 유지. `--publishing` 플래그가 있으면 새 워크플로우 강제.

### 검증 절차

1. `init-project.py /tmp/test-project --type landing --publishing` 실행
2. `/tmp/test-project/CLAUDE.md` 존재 확인
3. `verify_claude_md(Path("/tmp/test-project"))` → 빈 리스트 (누락 0건)
4. 폴더 구조 확인 (`css/`, `js/`, `img/`, `extracted/`, `figma-png/`)

## Q&A 보강 사항

- **Q5 답변**: 호환성 모든 프로젝트 지원 X
  - 결정: 새 워크플로우 강제는 신규 프로젝트만. 기존 프로젝트 (디에스솔루션 등) 는 영향 X
- **Q6 답변**: 디에스솔루션 배제, 현재 변경 로직 최적화에만 몰두
  - 결정: init-project.py 가 배포한 CLAUDE.md 는 디에스솔루션 사례 인용 X
