# TaskFlow - Docker CRUD 예제

Apache HTTP Server + Tomcat(Java Servlet API Gateway) + Python Flask + MySQL로 구성한 기본 업무 관리 서비스입니다.

## 1. 아키텍처

```text
Browser
  | HTTP :8080
  v
Apache HTTP Server
  | /          -> 정적 HTML/CSS/JS
  | /api/*     -> Tomcat :8080/api/*
  v
Tomcat 10.1 (Java Servlet API Gateway)
  | HTTP 내부 통신
  v
Python Flask + Gunicorn :5000
  | MySQL Connector/Python
  v
MySQL 8.4 :3306
```

Tomcat은 Python 코드를 직접 실행하지 않습니다. 이 예제에서는 Tomcat Servlet이 요청을 Python Flask API로 전달하는 게이트웨이 역할을 합니다. 실제 Python 중심 서비스라면 Apache에서 Flask/Gunicorn으로 직접 프록시하는 구성이 더 단순합니다.

## 2. 실행

Docker Desktop 또는 Docker Engine과 Docker Compose가 필요합니다.

```bash
docker compose up -d --build
```

브라우저에서 다음 주소로 접속합니다.

```text
http://localhost:8080
```

## 3. 상태 확인 및 로그

```bash
docker compose ps
docker compose logs -f apache tomcat python-api mysql
```

Python API 헬스 체크(컨테이너 내부):

```bash
docker compose exec python-api python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/health').read().decode())"
```

## 4. REST API

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/tasks` | 전체 업무 조회 |
| GET | `/api/tasks/{id}` | 단일 업무 조회 |
| POST | `/api/tasks` | 업무 등록 |
| PUT | `/api/tasks/{id}` | 업무 수정 |
| DELETE | `/api/tasks/{id}` | 업무 삭제 |

등록 예시:

```bash
curl -X POST http://localhost:8080/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Docker 학습","description":"Compose 실습","status":"진행 중"}'
```

조회:

```bash
curl http://localhost:8080/api/tasks
```

수정:

```bash
curl -X PUT http://localhost:8080/api/tasks/1 \
  -H 'Content-Type: application/json' \
  -d '{"title":"Docker 학습 완료","description":"CRUD 구현","status":"완료"}'
```

삭제:

```bash
curl -X DELETE http://localhost:8080/api/tasks/1
```

## 5. 종료 및 데이터 초기화

컨테이너만 종료:

```bash
docker compose down
```

DB 볼륨까지 삭제(저장된 업무 데이터 영구 삭제):

```bash
docker compose down -v
```

## 6. 주의사항

- `db/init.sql`은 MySQL 데이터 디렉터리가 처음 생성될 때만 실행됩니다. 스키마를 변경하고 초기화하려면 개발 데이터가 삭제되는 점을 확인한 뒤 `docker compose down -v`를 사용하세요.
- 예제 계정/비밀번호는 로컬 실습 전용입니다. 실제 배포에서는 `.env`, Docker secrets 또는 클라우드 비밀 관리 서비스를 사용하세요.
- MySQL 포트는 호스트에 공개하지 않고 Docker 내부 네트워크에서만 접근합니다.
- 이 예제는 인증/인가, CSRF 방어, HTTPS, 운영용 비밀 관리가 없는 학습용 Basic CRUD입니다.
