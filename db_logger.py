import roslibpy
import numpy as np
import pymysql
import json
import time

# 1. MySQL DB 연결 설정
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='1234',
    database='rosdb',
    charset='utf8'
)
cursor = conn.cursor()

# 2. 테이블 확인 및 생성
create_table_query = """
CREATE TABLE IF NOT EXISTS lidardata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ranges JSON,
    `when` DATETIME DEFAULT CURRENT_TIMESTAMP,
    action VARCHAR(50)
)
"""
cursor.execute(create_table_query)
conn.commit()
print(" MySQL 'lidardata' 테이블 준비 완료!")

# 3. ROS PC(우분투) 연결 설정
ROS_PC_IP = '192.168.0.130'
client = roslibpy.Ros(host=ROS_PC_IP, port=9090)

listener = roslibpy.Topic(client, '/scan', 'sensor_msgs/LaserScan')

def scan_callback(msg):
    # 1. 원본 데이터 Numpy 배열 변환
    ranges = np.array(msg['ranges'])

    # 2. 자율주행 코드와 완전히 동일한 노이즈 전처리
    # 0.0이나 무한대 값을 안전거리 밖인 3.5m로 치환하여 에러 방지
    ranges_clean = np.where((ranges == 0.0) | np.isinf(ranges) | np.isnan(ranges), 3.5, ranges)

    # 3. 자율주행 코드와 동일한 스캔 각도 및 계산 방식 적용
    front = np.r_[ranges_clean[350:360], ranges_clean[0:10]]
    left  = ranges_clean[80:100]
    right = ranges_clean[260:280]

    front_dist = np.mean(front)
    left_dist  = np.mean(left)
    right_dist = np.mean(right)

    # 4. 자율주행 코드와 동일한 판단 로직
    SAFE_DIST = 0.5

    if front_dist < SAFE_DIST:
        action = "turn_left" if left_dist > right_dist else "turn_right"
    else:
        action = "go_forward"

    # 5. DB에 데이터 INSERT
    try:
        ranges_json = json.dumps(ranges.tolist()) # DB에는 가공 전 원본 데이터 저장
        insert_query = "INSERT INTO lidardata (ranges, action) VALUES (%s, %s)"
        cursor.execute(insert_query, (ranges_json, action))
        conn.commit()

        # 터미널 로그 출력
        print(f"[{cursor.lastrowid:04d}번 로그] 상태: {action:12} | 전방: {front_dist:.2f}m | 좌: {left_dist:.2f}m | 우: {right_dist:.2f}m")

    except Exception as e:
        print(f" DB 저장 에러: {e}")

# 구독 시작
listener.subscribe(scan_callback)
client.on_ready(lambda: print('ROS PC 연결 완료'))

try:
    client.run_forever()
except KeyboardInterrupt:
    print("\n 로깅 시스템을 종료합니다.")
    cursor.close()
    conn.close()
    client.terminate()