import roslibpy
import numpy as np
import time


# 1. 우분투 ROS 2 PC 연결 설정
ROS_PC_IP = '192.168.0.130'
client = roslibpy.Ros(host=ROS_PC_IP, port=9090)
client.run()

# 2. 로봇에게 주행 명령을 내릴 퍼블리셔
cmd_pub = roslibpy.Topic(client, '/turtle1/cmd_vel', 'geometry_msgs/Twist')

# --- 전역 상태 변수 ---
current_mode = "AUTO"  # AUTO or MANUAL
is_handling_crash = False  # 긴급 회전 중인지 여부 (최우선 순위)


# 거북이를 즉시 정지
def stop_turtle():
    stop_msg = roslibpy.Message({
        'linear': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'angular': {'x': 0.0, 'y': 0.0, 'z': 0.0}
    })
    cmd_pub.publish(stop_msg)


def perform_180_turn():
    #Lidar나 키보드 입력을 무시하고 180도 제자리 회전을 직접 수행
    global is_handling_crash

    # 1. 모든 제어권 독점
    is_handling_crash = True
    print("\n[EMERGENCY] Wall Detected! Starting 180-degree turn.")

    # 2. 즉시 정지 후 대기 (관성 제거)
    stop_turtle()
    time.sleep(0.2)

    # 3. 180도 제자리 회전 명령 송출
    # turtlesim은 정확한 포즈 피드백이 없이 roslibpy만으로는 정밀 제어가 어려우므로,
    # 일정한 회전 속도와 시간을 주어 대략 180도를 돕니다.
    # 속도 3.14159 (PI) rad/s로 1초간 돌면 180도입니다.
    turn_msg = roslibpy.Message({
        'linear': {'x': 0.0, 'y': 0.0, 'z': 0.0},
        'angular': {'x': 0.0, 'y': 0.0, 'z': 3.14159}  # PI rad/s (약 180도/s)
    })
    cmd_pub.publish(turn_msg)

    # 회전하는 동안 기다림 (그림이 그려지는 시간)
    time.sleep(1.0)

    # 4. 회전 완료 후 정지
    stop_turtle()
    print("[EMERGENCY] Turn complete. Resuming normal operation.\n")
    time.sleep(0.2)

    # 5. 제어권 반납
    is_handling_crash = False


def rosout_callback(msg):
    #ROS 시스템 전체 로그를 구독하여 turtlesim의 벽 충돌 메시지를 감지
    try:
        # 메시지 원문
        log_text = msg.get('msg', '')

        # "Hit the wall!" 이라는 문자열이 포함되어 있다면?
        if "Hit the wall!" in log_text:
            # 주행 모드와 상관없이 긴급 회전 수행
            perform_180_turn()

    except Exception as e:
        pass  # 로그 파싱 에러는 무시


def scan_callback(msg):
    global current_mode, is_handling_crash

    # 긴급 복구 중이거나 수동 모드일 때는 Lidar 로직 무시
    if is_handling_crash or current_mode == "MANUAL":
        return

    ranges = np.array(msg['ranges'])
    ranges = np.where((ranges == 0.0) | np.isinf(ranges) | np.isnan(ranges), 3.5, ranges)

    front = np.r_[ranges[350:360], ranges[0:10]]
    left = ranges[80:100]
    right = ranges[260:280]

    front_dist = np.mean(front)
    left_dist = np.mean(left)
    right_dist = np.mean(right)

    safe_dist = 0.5

    twist = {'linear': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'angular': {'x': 0.0, 'y': 0.0, 'z': 0.0}}

    if front_dist < safe_dist:
        if left_dist > right_dist:
            action = "turn_left"
            twist['angular']['z'] = 2.5
        else:
            action = "turn_right"
            twist['angular']['z'] = -2.5
    else:
        action = "go_forward"
        twist['linear']['x'] = 2.0

    cmd_pub.publish(roslibpy.Message(twist))


# 3. 토픽 구독 시작
# A. Lidar 센서 데이터 구독
listener_scan = roslibpy.Topic(client, '/scan', 'sensor_msgs/LaserScan')
listener_scan.subscribe(scan_callback)

# B. ROS 시스템 로그 구독
listener_rosout = roslibpy.Topic(client, '/rosout', 'rcl_interfaces/msg/Log')
listener_rosout.subscribe(rosout_callback)

print("System Started with Emergency Recovery. Current Mode: AUTO")
print("Commands: [m] Toggle Mode | [w/a/s/d] Move (Manual) | [x] Stop | [q] Quit")

try:
    # 4. 키보드 입력을 받는 메인 루프
    while True:
        user_cmd = input().strip().lower()

        if user_cmd == 'q':
            break

        # 긴급 복구 중에는 키보드 명령 무시
        if is_handling_crash:
            print("[EMERGENCY] Recovery in progress. Key ignored.")
            continue

        elif user_cmd == 'm':
            current_mode = "MANUAL" if current_mode == "AUTO" else "AUTO"
            print(f"Mode switched to: {current_mode}")
            stop_turtle()

        elif current_mode == "MANUAL":
            twist = {'linear': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'angular': {'x': 0.0, 'y': 0.0, 'z': 0.0}}

            if user_cmd == 'w':
                twist['linear']['x'] = 2.0
                print("[MANUAL] Move Forward")
            elif user_cmd == 's':
                twist['linear']['x'] = -2.0
                print("[MANUAL] Move Backward")
            elif user_cmd == 'a':
                twist['angular']['z'] = 2.5
                print("[MANUAL] Turn Left")
            elif user_cmd == 'd':
                twist['angular']['z'] = -2.5
                print("[MANUAL] Turn Right")
            elif user_cmd == 'x':
                stop_turtle()
                print("[MANUAL] Stop")
            else:
                continue

            cmd_pub.publish(roslibpy.Message(twist))

except KeyboardInterrupt:
    pass
finally:
    print("\nStopping system...")
    stop_turtle()
    client.terminate()