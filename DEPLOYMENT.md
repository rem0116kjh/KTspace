# Streamlit Community Cloud 배포 안내

## 배포 정보

| 항목 | 값 |
|-----|-----|
| **메인 파일 경로** | `app.py` |
| **브랜치명** | `main` |
| **저장소** | https://github.com/luka0116kjh/KTspace |

## 사전 준비

### 1. 필수 파일 확인
- ✅ `requirements.txt` — 모든 필수 패키지 포함 (streamlit, pandas, numpy, matplotlib, openai, python-dotenv)
- ✅ `packages.txt` — Ubuntu APT 패키지 (fonts-nanum 포함, matplotlib 한글 폰트 대응)
- ✅ `.gitignore` — `.streamlit/` 포함 (secrets 보호)
- ✅ `.env.example` — 로컬 개발 템플릿

### 2. Secrets 설정
Streamlit Community Cloud 웹 콘솔에서 **Secrets** 메뉴로 이동 후, 다음을 추가:

```toml
OPENAI_API_KEY = "sk-proj-..."  # OpenAI API 키 (선택사항)
```

> **참고**: 이 키가 없어도 앱은 정상 작동합니다. 기본 해설로 시작되며, 나중에 키를 추가하면 AI 해설 기능이 활성화됩니다.

## 배포 단계

### 1단계: Streamlit Community Cloud 연결
1. https://streamlit.io/cloud에 접속
2. GitHub 계정으로 로그인
3. 저장소 `https://github.com/luka0116kjh/KTspace` 선택
4. 앱 정보 입력:
   - **Main file path**: `app.py`
   - **Branch**: `main`

### 2단계: 배포 실행
"Deploy" 버튼을 클릭하면 자동으로:
1. `packages.txt` 읽음 → `fonts-nanum` 설치 (한글 폰트)
2. `requirements.txt` 읽음 → Python 패키지 설치
3. `.env` 무시 (git에 포함 안 됨, 안전함)
4. `app.py` 실행 → Streamlit 앱 시작

### 3단계: Secrets 추가 (선택)
배포 후 대시보드에서 앱의 **Settings** → **Secrets** 진입 후:
```toml
OPENAI_API_KEY = "sk-proj-..."
```
저장하면 앱이 자동으로 재시작되고 AI 해설이 활성화됩니다.

## README 최상단 배지 (선택)

배포 완료 후 README.md 최상단에 다음을 추가:

```markdown
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](YOUR_DEPLOYMENT_URL)
```

> `YOUR_DEPLOYMENT_URL`은 배포 후 Streamlit Cloud가 제공하는 URL로 교체 (예: `https://ktspace.streamlit.app`)

## 배포 후 확인 사항

- [ ] 앱이 정상 로드되는가
- [ ] 프리셋 100개가 모두 나타나는가
- [ ] 그래프에 한글 레이블이 정상 표시되는가 (한글 폰트)
- [ ] "설명을 더 쉽게 바꾸기" 버튼이 나타나는가 (기본 해설 표시)
- [ ] (선택) Secrets에 API 키를 추가했으면 AI 해설이 작동하는가

## 트러블슈팅

### 문제: "ModuleNotFoundError: No module named 'streamlit'"
→ `requirements.txt`가 로드되지 않음. GitHub에 커밋됐는지 확인.

### 문제: 그래프에 한글이 깨짐 (□□□□)
→ `packages.txt`가 없거나 로드 안 됨. 파일 생성 후 재배포.

### 문제: "OPENAI_API_KEY가 필요합니다" 경고
→ 의도된 동작. 기본 해설로 계속 작동. 필요하면 Secrets에 키 추가.

### 문제: .env 파일이 클라우드에도 적용되지 않음
→ 정상. `.env`는 로컬 개발용. 클라우드는 `Secrets` 메뉴에서 설정.

## 파일별 역할

| 파일 | 용도 |
|-----|-----|
| `app.py` | 메인 Streamlit 앱 |
| `solar_system_sim_v2_openai.py` | 물리 계산 엔진 |
| `scenario_catalog.py` | 100개 프리셋 정의 |
| `requirements.txt` | Python 패키지 (pip) |
| `packages.txt` | Ubuntu APT 패키지 |
| `.env.example` | 로컬 개발용 키 템플릿 (클라우드: 무시) |
| `.gitignore` | `.env`, `.streamlit/` 등 보호 |
| `README.md` | 사용자 문서 |

## 배포 후 업데이트

코드를 수정하고 `main` 브랜치에 푸시하면 자동으로 재배포됩니다.
