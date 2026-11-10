# Task Management Docker

Docker Compose 없이 Apache WEB, Tomcat WAS, Python Flask 애플리케이션,
MySQL을 각각 독립된 Docker 컨테이너로 빌드하고 실행하는 기본 업무 관리
서비스입니다.

## 1. 서비스 개요

-   **WEB:** Apache HTTP Server 2.4
-   **WAS / API Gateway:** Apache Tomcat 10.1 + Java Servlet
-   **Application:** Python Flask + Gunicorn
-   **Database:** MySQL 8.4
-   **컨테이너 관리:** Docker CLI (Compose 미사용)
-   **브라우저 접속:** `http://localhost:8080`

주요 기능: - 업무 목록 조회 - 업무 등록 - MySQL에 업무 데이터 저장 -
Apache Reverse Proxy를 통한 API 전달

## 2. 아키텍처

``` text
Browser (localhost:8080)
        |
        v
Apache WEB (container:80)
  - 정적 HTML 제공
  - /api/* Reverse Proxy
        |
        v
Tomcat WAS (container:8080)
  - Java Servlet API Gateway
        |
        v
Python Flask (container:5000)
  - 업무 API / 비즈니스 로직
        |
        v
MySQL (container:3306)
  - 업무 데이터 저장
```

모든 컨테이너는 사용자 정의 Docker 네트워크 `task-network`에 연결합니다.
컨테이너 간 통신에는 `localhost`가 아니라 컨테이너 이름과 내부 포트를
사용합니다.

## 3. 프로젝트 구조

``` text
task-management/
├── apache/
│   ├── Dockerfile
│   ├── conf/
│   │   └── task-proxy.conf
│   └── html/
│       └── index.html
├── tomcat/
│   ├── Dockerfile
│   ├── pom.xml
│   └── src/main/java/com/example/gateway/
│       └── PythonApiGateway.java
├── python/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
└── README.md
```

MySQL은 공식 이미지를 사용합니다. 실제 프로젝트에 추가 파일이 있다면 위
구조에 반영하면 됩니다.

## 4. 컨테이너 및 포트

  컨테이너        이미지                호스트 포트   컨테이너 포트
  --------------- ------------------- ------------- ---------------
  `task-apache`   `task-apache:1.0`            8080              80
  `task-tomcat`   `task-tomcat:1.0`            8081            8080
  `task-python`   `task-python:1.0`            5000            5000
  `task-mysql`    `mysql:8.4`                  3306            3306

일반 사용자는 Apache의 `http://localhost:8080`으로 접속합니다. 8081,
5000, 3306은 개발·점검용 직접 접근 포트입니다.

## 5. 사전 준비

-   Docker Engine 또는 Docker Desktop
-   터미널 (Linux / WSL 권장)
-   웹 브라우저

``` bash
docker --version
docker info
```

## 6. Docker 네트워크

``` bash
docker network create task-network
```

네트워크가 이미 있다면 중복 생성하지 않습니다.

``` bash
docker network ls
docker network inspect task-network
```

## 7. 이미지 빌드

각 서비스 디렉터리에서 개별적으로 빌드합니다.

``` bash
cd python
docker build -t task-python:1.0 .

cd ../tomcat
docker build -t task-tomcat:1.0 .

cd ../apache
docker build -t task-apache:1.0 .
```

이미지 확인:

``` bash
docker images
```

MySQL은 공식 이미지를 사용하므로 별도 빌드하지 않습니다.

## 8. 컨테이너 실행

아래 명령은 구성 예시입니다. 이미 실행 중인 컨테이너가 있다면 중복
실행하지 말고, 실제 MySQL 계정·비밀번호와 일치하도록 환경변수를
설정하세요.

### 8.1 MySQL

아직 MySQL 컨테이너를 만들지 않은 경우의 예시입니다. 비밀번호는 학습용
예시이므로 실제 환경에서는 변경하세요.

``` bash
docker run -d \
  --name task-mysql \
  --network task-network \
  -p 127.0.0.1:3306:3306 \
  -e MYSQL_ROOT_PASSWORD=루트비밀번호 \
  -e MYSQL_DATABASE=taskdb \
  -e MYSQL_USER=taskuser \
  -e MYSQL_PASSWORD=taskpass \
  --restart unless-stopped \
  mysql:8.4
```

초기화 후 `taskdb` 데이터베이스에 `tasks` 테이블을 생성하고 애플리케이션
계정 권한을 부여해야 합니다. 이미 구성한 MySQL 컨테이너가 있다면 이
명령을 다시 실행하지 않습니다.

### 8.2 Python

``` bash
docker run -d \
  --name task-python \
  --network task-network \
  -p 127.0.0.1:5000:5000 \
  -e DB_HOST=task-mysql \
  -e DB_PORT=3306 \
  -e DB_USER=taskuser \
  -e DB_PASSWORD=taskpass \
  -e DB_NAME=taskdb \
  --restart unless-stopped \
  task-python:1.0
```

환경변수의 DB 계정 정보는 실제 MySQL 설정과 일치해야 합니다.

### 8.3 Tomcat

Tomcat은 Python 컨테이너 이름 `task-python`으로 내부 포트 5000에
접근합니다.

``` bash
docker run -d \
  --name task-tomcat \
  --network task-network \
  -p 127.0.0.1:8081:8080 \
  -e PYTHON_API_URL=http://task-python:5000 \
  --restart unless-stopped \
  task-tomcat:1.0
```

`PYTHON_API_URL`은 실제 컨테이너 이름에 맞춰 지정해야 합니다. 이를
누락하면 기본 주소가 실제 컨테이너 이름과 달라져 502 오류가 발생할 수
있습니다.

### 8.4 Apache

``` bash
docker run -d \
  --name task-apache \
  --network task-network \
  -p 127.0.0.1:8080:80 \
  --restart unless-stopped \
  task-apache:1.0
```

실행 상태 확인:

``` bash
docker ps
```

## 9. Apache Reverse Proxy

`apache/conf/task-proxy.conf`에는 다음 Proxy 규칙만 둡니다.

``` apache
ProxyPreserveHost On

ProxyPass        /api/ http://task-tomcat:8080/api/
ProxyPassReverse /api/ http://task-tomcat:8080/api/
```

Apache 공식 이미지에는 기본 설정 파일
`/usr/local/apache2/conf/httpd.conf`가 이미 포함되어 있습니다.
`task-proxy.conf`에 `Listen 80`, `ServerRoot`, 전체 `LoadModule` 목록 등
메인 설정을 복사하지 마세요. `Listen` 및 모듈을 중복 선언하면 Apache가
시작되지 않을 수 있습니다.

Apache Dockerfile은 `proxy_module`과 `proxy_http_module`을 활성화하고
`task-proxy.conf`를 메인 설정에 포함해야 합니다.

## 10. API 및 브라우저 테스트

### 헬스 체크

Apache 경유:

``` bash
curl -i http://localhost:8080/api/health
```

Tomcat 직접 접근:

``` bash
curl -i http://localhost:8081/api/health
```

정상 응답 예시:

``` json
{"database":"connected","status":"healthy"}
```

### 업무 목록 조회

``` bash
curl http://localhost:8080/api/tasks
```

### 업무 등록

``` bash
curl -X POST http://localhost:8080/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Docker 통합 테스트","description":"Apache부터 MySQL까지 요청 전달 확인"}'
```

정상 응답 예시:

``` json
{"id":3,"message":"Task created"}
```

실제 ID는 기존 데이터에 따라 달라집니다.

### 브라우저

`http://localhost:8080`에 접속한 뒤 다음을 확인합니다.

1.  웹 페이지가 표시되는지 확인
2.  기존 업무 목록이 나타나는지 확인
3.  새 업무를 등록
4.  등록 후 목록이 갱신되는지 확인
5.  새로고침 후에도 데이터가 남아 있는지 확인

## 11. MySQL 데이터 확인

``` bash
docker exec -it task-mysql mysql \
  --default-character-set=utf8mb4 \
  -u taskuser -p taskdb
```

MySQL 프롬프트에서:

``` sql
SHOW TABLES;
SELECT * FROM tasks;
```

`status` 컬럼은 테이블 정의에 따라 `대기`, `진행 중`, `완료` ENUM 값을
사용합니다. 애플리케이션에서 전달하는 값은 ENUM에 정의된 값과 정확히
일치해야 합니다.

한글이 터미널에서 깨져 보이면 서버 데이터와 클라이언트 표시 문제를
구분해 확인합니다. `HEX(title)`, `HEX(description)`, `HEX(status)`로
저장된 바이트를 확인하고, 연결 문자 집합이 `utf8mb4`인지 점검합니다.

## 12. 관리 명령어

### 상태 확인

``` bash
docker ps
docker ps -a
```

### 로그 확인

``` bash
docker logs --tail 100 task-apache
docker logs --tail 100 task-tomcat
docker logs --tail 100 task-python
docker logs --tail 100 task-mysql
```

실시간 로그:

``` bash
docker logs -f task-apache
```

### 컨테이너 내부 접속

``` bash
docker exec -it task-apache sh
docker exec -it task-tomcat sh
docker exec -it task-python sh
docker exec -it task-mysql bash
```

### 중지 및 시작

``` bash
docker stop task-apache task-tomcat task-python task-mysql
docker start task-mysql task-python task-tomcat task-apache
```

## 13. 트러블슈팅 기록

### Python에서 MySQL 업무 등록 실패

-   **증상:** API가 `Database error`를 반환하거나 MySQL에서
    `Data truncated for column 'status'`가 발생함.
-   **원인:** INSERT 시 전달한 상태 문자열이 ENUM에 정의된 값과 일치하지
    않음.
-   **확인 및 조치:** 테이블의 `SHOW CREATE TABLE tasks;` 결과를
    확인하고 Python 기본 상태값 및 입력 검증 값을 ENUM 값과 일치시킴.

### MySQL 한글이 `??`로 표시됨

-   **증상:** 터미널에서 한글이 물음표로 표시됨.
-   **확인:** `SHOW VARIABLES LIKE 'character_set%';`, `HEX()` 조회로
    저장된 데이터와 연결 문자 집합을 확인함.
-   **조치:** MySQL 접속에 `--default-character-set=utf8mb4`를 사용하고
    서버·DB·테이블·연결의 문자 집합을 점검함.

### Tomcat에서 Python API 호출 시 502

-   **증상:** Tomcat API가 `502 Bad Gateway`를 반환함.
-   **원인:** Servlet 기본 API 주소는 `python-api:5000`이었지만 실제
    Python 컨테이너 이름은 `task-python`이었음.
-   **조치:** Tomcat 실행 시
    `-e PYTHON_API_URL=http://task-python:5000`을 지정함.

### Apache 컨테이너가 재시작됨

-   **증상:** `Cannot define multiple Listeners on the same IP:port`
    오류가 발생함.
-   **원인:** Proxy 설정 파일에 메인 `httpd.conf` 내용이 잘못 들어가
    `Listen 80`과 모듈 선언이 중복됨.
-   **조치:** `task-proxy.conf`에는 Proxy 지시어만 남기고 기본
    `httpd.conf`는 공식 이미지의 파일을 사용함.

### Apache에서 백엔드 API 연결 실패

-   Apache와 Tomcat이 같은 `task-network`에 연결되어 있는지 확인합니다.
-   Proxy 대상이 `http://task-tomcat:8080/api/`인지 확인합니다.
-   Tomcat의 `http://localhost:8081/api/health`가 정상 응답하는지 먼저
    확인합니다.
-   컨테이너 간 요청에는 호스트 포트가 아닌 내부 포트를 사용합니다.

## 14. 학습 내용 및 개선 과제

이번 프로젝트에서 실습한 내용:

-   Docker 이미지 빌드 및 컨테이너 실행
-   사용자 정의 Docker 네트워크
-   컨테이너 이름 기반 서비스 디스커버리
-   호스트 포트와 컨테이너 포트의 차이
-   Apache Reverse Proxy
-   Tomcat Java Servlet 기반 API Gateway
-   Python Flask와 MySQL 연동
-   환경변수로 서비스 설정 분리
-   컨테이너 로그 기반 장애 분석
-   UTF-8 및 MySQL `utf8mb4` 문자 집합

향후 개선 과제:

-   Docker Compose를 이용한 다중 컨테이너 관리
-   MySQL 볼륨을 이용한 데이터 영속성
-   `.env` 및 Docker secrets를 이용한 비밀정보 관리
-   API 입력 검증과 예외 처리 강화
-   HTTPS 및 보안 헤더 적용
-   컨테이너 헬스 체크와 시작 순서 관리
-   로깅 및 모니터링
-   사용자 인증 및 사용자별 업무 관리

## License

학습 및 개인 실습 목적으로 작성한 프로젝트입니다.
