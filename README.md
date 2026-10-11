# opportunity-scrap

POPOK의 기회 탭에 사용할 지원사업, 오디션, 채용·협업 공고를 수집하는 독립 Python 파이프라인입니다.

## 원칙

- 웹앱과 크롤러를 분리합니다.
- 수집 원본과 정규화 결과를 SQLite에 먼저 보관합니다.
- 신규 데이터는 Supabase에 `draft / needs_review / is_verified=false`로 저장합니다.
- 동일한 `source + external_id`는 다시 삽입하지 않고 변경된 필드만 갱신합니다.
- 자동 공개는 하지 않습니다. POPOK 관리자 화면에서 검수 후 공개합니다.
- 출처의 robots.txt와 이용 정책을 준수합니다.

## 지원 출처

| 출처 | 코드 | 상태 |
|---|---|---|
| 아트누리 | `artnuri` | 초기 지원 |
| 아트모아 | `artmore` | 초기 지원, 실데이터 점검 필요 |
| 예술경영지원센터 | - | robots.txt 제한으로 미지원 |

## 처리 흐름

```text
출처별 크롤러
  → 정규화
  → 필수값·날짜·URL 검증
  → 실행 내부 중복 제거
  → SQLite 원본 백업
  → Supabase 변경 계획 생성
  → --apply일 때만 draft로 반영
```

검증에 실패한 데이터도 SQLite에는 남지만 Supabase에는 전송하지 않습니다.

## 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env`에 POPOK와 같은 Supabase 프로젝트의 서버 전용 키를 설정합니다.

```env
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_KEY
SUPABASE_TABLE=opportunities
SQLITE_PATH=data/opportunities.sqlite
CRAWLER_USER_AGENT=POPOKOpportunityBot/0.1 (+contact: admin@popok.kr)
```

Service Role Key는 Git에 커밋하지 마세요.

## 실행

먼저 dry-run으로 실행합니다. Supabase 자격 증명이 없어도 SQLite 백업까지 동작합니다.

```bash
python scripts/update_opportunities.py --source artnuri --limit 10
python scripts/update_opportunities.py --source artmore --limit 10
python scripts/update_opportunities.py --source all --limit 20
```

검증된 행을 Supabase에 반영하려면 명시적으로 `--apply`를 붙입니다.

```bash
python scripts/update_opportunities.py --source artnuri --limit 20 --apply
```

반영된 행은 공개되지 않습니다. POPOK 관리자에서 검수 후 다음 값을 설정해야 사용자 화면에 나타납니다.

```text
publication_status = published
review_status = approved
is_verified = true
```

## 테스트

```bash
python -m unittest discover -s tests -v
```

## 현재 범위와 다음 작업

초기 버전은 안전한 골격입니다. 운영 전에 다음을 확인해야 합니다.

1. POPOK의 `opportunities` 마이그레이션을 실제 Supabase에 적용합니다.
2. 아트누리와 아트모아의 최신 HTML로 파서를 dry-run 검증합니다.
3. `.env`를 로컬 또는 실행 서버에만 등록합니다.
4. 수동 실행 결과가 안정되면 GitHub Actions나 서버 Cron을 추가합니다.
5. 자동 공개는 충분한 표본 검수 후 출처별로 별도 도입합니다.

