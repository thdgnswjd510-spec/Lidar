# ROS 2 Lidar Autonomous Driving & Logging System

## 프로젝트 개요
ROS 2(Ubuntu) 환경에서 2초 주기로 발행되는 모의 Lidar 센서 데이터(`/scan`)를 Windows 로컬 PC에서 수신하여 자율주행 모션을 결정하고, 해당 데이터를 데이터베이스에 적재하는 시스템입니다. 수집된 센서 데이터는 추후 머신러닝(ML) 학습용 데이터셋으로 가공하여 활용할 수 있습니다.

## 요구 사항
- **Language:** Python 3.x
- **Database:** MySQL 8.0+
- **Environment:** ROS 2 (Ubuntu 가상 머신), Windows (로컬 환경)
- **ROS 2 Packages:** `rosbridge_server`, `turtlesim`

## 패키지 설치
로컬 PC(Windows)에서 프로젝트 실행에 필요한 파이썬 라이브러리를 설치합니다.
```bash
pip install roslibpy numpy pymysql pandas
```

## 데이터베이스 스키마 셋업
데이터 로깅을 위해 MySQL에 접속하여 아래 DDL을 통해 테이블을 생성합니다.

```sql
CREATE DATABASE rosdb;
USE rosdb;

CREATE TABLE IF NOT EXISTS lidardata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ranges JSON,
    `when` DATETIME DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(50)
);
```

## 시스템 구성 및 파일 설명

### 1. `drive.py` (주행 제어 모듈)
모의 Lidar 데이터를 수신하여 장애물을 회피하고 Turtlesim을 제어합니다.

- **Hybrid Mode:** `AUTO` / `MANUAL` 주행 모드 실시간 전환 지원.
- **판단 로직:** `/scan` 데이터를 전처리(노이즈 및 inf 값 치환)하여 안전거리(0.5m) 기준으로 조향 방향(좌/우/직진)을 결정합니다.
- **긴급 회피:** `/rosout` 로그를 구독하여 "Hit the wall!" 충돌 발생 시 제어권을 독점하고 180도 긴급 회피 기동을 수행합니다.

### 2. `db_logger.py` (데이터 수집 모듈)
주행 로직과 동일한 기준을 적용하여 센서 원본 데이터와 라벨(Action)을 DB에 저장합니다.

- 수신된 360도 Lidar 데이터를 JSON 형태로 직렬화합니다.
- 현재 주행 상태(`turn_left`, `turn_right`, `go_forward`)를 판단하여 원본 데이터와 함께 `rosdb.lidardata` 테이블에 실시간 INSERT 합니다.

### 3. `parsing.py` (학습용 데이터 전처리 모듈)
DB에 적재된 Raw 데이터를 머신러닝 모델 학습에 적합한 CSV 형태로 변환합니다.

- JSON 형태의 Lidar 데이터를 360개의 독립된 컬럼(`range_0` ~ `range_359`)으로 분할합니다.
- 정답지(Label) 역할을 하는 `action` 컬럼을 병합하여 총 361열의 DataFrame을 생성하고, `lidar_parsed_data.csv` 파일로 추출합니다.

### 4. `meseeage.py` (Turtlesim 텍스트 렌더링)
Turtlesim 화면에 지정된 영문 텍스트를 그리는 유틸리티입니다.

- 좌표 데이터 기반의 폰트 렌더링 시스템을 구현했습니다.
- `teleport_absolute` 서비스를 이용하여 이동 궤적 없이 텍스트를 깔끔하게 출력합니다.
- 화면 자동 초기화(`/reset`, `/kill` 서비스) 기능을 포함합니다.

## 실행 방법

*주의: 각 파이썬 스크립트 상단의 `ROS_PC_IP` 값을 현재 ROS 2가 실행 중인 Ubuntu PC의 IP 주소로 변경한 뒤 실행해야 합니다.*

### Step 1. ROS 2 환경 구성 (Ubuntu)
Ubuntu 환경에서 터미널(창 4개)을 열어 통신 및 제어 환경을 구성합니다.

1. **Turtlesim 노드 실행**
2. **Rosbridge Server 실행 (외부 통신용)**
   ```bash
   ros2 run rosbridge_server rosbridge_websocket
   ```
3. **모의 Lidar 데이터 퍼블리셔 실행**
4. **기타 제어용 노드 실행**

### Step 2. 자율주행 및 로깅 실행 (Windows)
Windows 로컬 환경에서 독립된 터미널 2개를 열어 각각 실행합니다.

```bash
python drive.py
python db_logger.py
```

### Step 3. 데이터 추출 (Windows)
주행 및 데이터 수집 완료 후, 아래 스크립트를 실행하여 ML용 CSV 데이터를 추출합니다.

```bash
python parsing.py
```

### [Optional] 텍스트 렌더링 기능 사용
Turtlesim 화면에 간단한 영문 메시지를 그리고 싶을 때 실행합니다. (실행 후 터미널에 영문 입력 시 해당 모양으로 주행하며 글자를 그림)

```bash
python meseeage.py
```
