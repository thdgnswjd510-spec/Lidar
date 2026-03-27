import rclpy as rp
from rclpy.node import Node
from turtlesim.msg import Pose
from geometry_msgs.msg import Twist

class MoveAndSubscribe(Node):
    def __init__(self):
        super().__init__('move_and_sub')
        
        # 1. 속도 명령을 보낼 Publisher 생성
        self.publisher = self.create_publisher(Twist, '/turtlesim/turtle1/cmd_vel', 10)
        
        # 2. 위치 정보를 받을 Subscriber 생성
        self.subscription = self.create_subscription(Pose, '/turtle1/pose', self.callback, 10)
        
        # 3. 0.5초마다 거북이를 움직이는 타이머 생성
        self.timer = self.create_timer(0.5, self.move_turtle)

    def callback(self, msg):
        # 위치 정보를 들으면 출력
        self.get_logger().info(f"📍 현재 위치 -> X: {msg.x:.2f}, Y: {msg.y:.2f}")

    def move_turtle(self):
        # 앞으로 전진(linear.x)하며 회전(angular.z)하는 메시지 생성 및 전송
        msg = Twist()
        msg.linear.x = 2.0
        msg.angular.z = 1.0
        self.publisher.publish(msg)
        self.get_logger().info("🚀 거북이에게 이동 명령을 보냈습니다!")

# ... (이하 main 함수는 동일)
def main(args=None):
    rp.init(args=args)
    node = MoveAndSubscribe()
    try:
        rp.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rp.shutdown()

if __name__ == '__main__':
    main()