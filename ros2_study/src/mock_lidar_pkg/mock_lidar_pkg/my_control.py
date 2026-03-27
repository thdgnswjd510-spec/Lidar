import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import math
import random

class MockScanPub(Node):
    def __init__(self):
        super().__init__('mock_scan_pub')
        self.pub = self.create_publisher(LaserScan, '/scan', 10)
        self.timer = self.create_timer(2.0, self.timer_callback) # 2초 주기

    def timer_callback(self):
        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'laser_frame'
        
        # Lidar 기본 설정
        msg.angle_min = 0.0
        msg.angle_max = 2.0 * math.pi
        msg.angle_increment = math.radians(1.0)
        msg.range_min = 0.12
        msg.range_max = 3.5

        # 1. 기본 거리(3.5m)로 360개 생성
        ranges = [3.5] * 360

        # 2. 랜덤 패턴 결정 (전방, 좌, 우)
        case = random.choice([0, 90, 270]) 
        
        # 3. 해당 각도 주변에 벽(0.4m) 생성
        for i in range(case - 20, case + 21):
            ranges[i % 360] = 0.4

        msg.ranges = ranges
        self.pub.publish(msg)
        self.get_logger().info(f'Published: {case} deg wall')

def main():
    rclpy.init()
    rclpy.spin(MockScanPub())
    rclpy.shutdown()

if __name__ == '__main__':
    main()