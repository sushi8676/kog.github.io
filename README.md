# LoL 아이템 비교표 웹사이트

## 배포 (별도 프로그램 설치 불필요)
1. GitHub에서 **새 공개 저장소**를 만듭니다.
2. 이 ZIP 안의 **lol_item_website 폴더 내부 파일과 .github 폴더까지** 저장소 루트에 업로드합니다.
3. GitHub 저장소 **Settings → Pages → Build and deployment → Source: GitHub Actions**를 선택합니다.
4. **Actions → Deploy LoL Item Website → Run workflow**를 실행하거나 `main`에 커밋을 추가합니다.
5. 배포가 성공하면 Pages 화면에 접속 주소가 표시됩니다. (보통 `https://사용자명.github.io/저장소명/`)

## 데이터 정확성 및 자동 업데이트 (중요)
- 현시점 `site/data/items.json`에는 과거 작업에서 확보한 **16개 부분 확인값**만 들어 있습니다. 모든 협곡 아이템에 대한 검증은 미완료입니다.
- 코드가 사용하는 아이템의 스탯·가격 출처는 나무위키로 한정합니다. 데이터 수집기(`scripts/collector.py`)는 나무위키의 시작·기본·서사·전설·장화 문서를 읽습니다.
- 자동 수집 기능은 **실제 나무위키 접근 및 추출 정확성을 확인하지 못했습니다**. 사이트에 190개가 자동으로 채워진다고 보장하지 않습니다.
- GitHub Actions는 수요일마다 수집을 **시도**하고 진단 기록을 남깁니다. 부정확한 자동 수집값이 공개되는 것을 막기 위해 새 데이터 자동 배포는 차단했습니다.
- 패치 버전도 자동으로 확정하지 않습니다. `items.json`의 `patch`는 **해당 자료가 검증된 패치**를 기록하는 값이며, 검증 없이 고치면 안 됩니다.
- 나무위키 자체의 최신 수정 시점이 실제 게임 패치보다 늦을 수 있습니다.
- GitHub 계정 연결/저장소 생성/Pages 설정이 필요하며 **이 ZIP만으로 공개 웹 주소가 자동 생성되지는 않습니다**.

## 구조
- `site/index.html` : 검색·필터·정렬·CSV 다운로드 가능한 웹사이트
- `site/data/items.json`: 웹사이트가 표시하는 데이터
- `scripts/collector.py`: 나무위키 HTML의 후보 정보 추출 및 검토 대상 분리
- `scripts/publish.py`: 안전 검사 후 (승인된 경우에만) 게시 데이터 교체
- `.github/workflows/website.yml`: GitHub Pages 자동 배포
- `.github/workflows/check-items.yml`: 정기 추출 검사 (배포하지 않음)
