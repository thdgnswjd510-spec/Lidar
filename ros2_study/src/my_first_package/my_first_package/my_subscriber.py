import rclpy as rp
from rclpy.node import Node
from turtlesim.msg import Pose

class TurtlesimSubscriber(Node):

    def __init__(self):
        super().__init__('turtlesim_subscriber')
        # /turtle1/pose 토픽을 구독합니다.
        self.subscription = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.callback,
            10)

    def callback(self, msg):
        # 거북이의 위치 정보를 터미널에 출력합니다.
        print(f"X: {msg.x:.2f}, Y: {msg.y:.2f}, Theta: {msg.theta:.2f}")

def main(args=None):
    rp.init(args=args)

    turtlesim_subscriber = TurtlesimSubscriber()
    
    try:
        # 노드를 계속 실행하며 콜백 함수를 호출합니다.
        rp.spin(turtlesim_subscriber)
    except KeyboardInterrupt:
        print("\n노드를 종료합니다.")
    finally:
        turtlesim_subscriber.destroy_node()
        rp.shutdown()

if __name__ == '__main__':
    main()