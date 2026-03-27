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
print("✅ MySQL 'lidardata' 테이블 준비 완료!")

# 3. ROS PC(우분투) 연결 설정
ROS_PC_IP = '192.168.0.130'
client = roslibpy.Ros(host=ROS_PC_IP, port=9090)

listener = roslibpy.Topic(client, '/scan', 'sensor_msgs/LaserScan')

# --- 상태 관리를 위한 전역 변수 (히스테리시스 적용) ---
current_action = "go_forward"

def scan_callback(msg):
    global current_action
    ranges = np.array(msg['ranges'])

    # --- [연동 핵심] 주행 로직과 동일한 180도 와이드 스캔 및 필터링 적용 ---
    front_wide_scan = np.r_[ranges[270:360], ranges[0:90]]
    left_side = ranges[45:135]
    right_side = ranges[225:315]

    # 아군 거북이(0.5m ~ 1.3m) 필터링
    mask = (front_wide_scan > 0.5) & (front_wide_scan < 1.3)
    valid_front = front_wide_scan[~mask]
    valid_front = valid_front[valid_front > 0.05] # 오류값 제거

    # 거리 계산
    front_dist = np.min(valid_front) if len(valid_front) > 0 else 10.0
    left_dist = np.mean(left_side[left_side > 1.3]) if len(left_side[left_side > 1.3]) > 0 else 10.0
    right_dist = np.mean(right_side[right_side > 1.3]) if len(right_side[right_side > 1.3]) > 0 else 10.0

    # --- 주행 로직과 동일한 상태 머신 (DB 기록용) ---
    SAFE_DIST = 2.5
    CLEAR_DIST = 2.8

    if current_action == "go_forward":
        if front_dist < SAFE_DIST:
            current_action = "turn_left" if left_dist > right_dist else "turn_right"
    else:
        if front_dist > CLEAR_DIST:
            current_action = "go_forward"

    # --- 4. DB에 데이터 INSERT ---
    try:
        ranges_json = json.dumps(ranges.tolist())
        insert_query = "INSERT INTO lidardata (ranges, action) VALUES (%s, %s)"
        cursor.execute(insert_query, (ranges_json, current_action))
        conn.commit()

        # 터미널 로그 출력
        print(f"[{cursor.lastrowid:04d}번 로그] 상태: {current_action:12} | 실제벽 거리: {front_dist:.2f}m")

    except Exception as e:
        print(f"❌ DB 저장 에러: {e}")

# 구독 시작
listener.subscribe(scan_callback)
client.on_ready(lambda: print('🌐 ROS PC 연결 완료! DB 로깅 시스템 가동 시작.'))

try:
    client.run_forever()
except KeyboardInterrupt:
    print("\n🛑 로깅 시스템을 종료합니다.")
    cursor.close()
    conn.close()
    client.terminate()