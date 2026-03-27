import rclpy as rp
from rclpy.node import Node
from turtlesim.msg import Pose
from my_first_package_msgs.msg import CmdAndPoseVel
from geometry_msgs.msg import Twist

class CmdAndPose(Node):
    def __init__(self):
        super().__init__('turtle_cmd_pose')
        
        # 메시지 초기화
        self.cmd_pose = CmdAndPoseVel()
        
        # 구독(Subscription) 설정
        self.sub_pose = self.create_subscription(Pose, '/turtle1/pose', self.callback_pose, 10)
        self.sub_cmdvel = self.create_subscription(Twist, '/turtle1/cmd_vel', self.callback_cmd, 10)
        
        # 발행(Publisher) 설정
        self.publisher = self.create_publisher(CmdAndPoseVel, '/cmd_and_pose', 10)
        
        # 타이머 설정 (1초마다 발행)
        self.timer_period = 1.0
        self.timer = self.create_timer(self.timer_period, self.timer_callback)

    def callback_pose(self, msg):
        # turtlesim/msg/Pose에서 오는 데이터 저장
        self.cmd_pose.pose_x = msg.x
        self.cmd_pose.pose_y = msg.y
        # 주의: .msg 파일에 정의한 이름이 'linear_vel'인지 확인하세요!
        self.cmd_pose.linear_vel = msg.linear_velocity
        self.cmd_pose.angular_vel = msg.angular_velocity
        

    def callback_cmd(self, msg):
        # geometry_msgs/msg/Twist에서 오는 조종 명령 저장
        # 주의: .msg 파일의 변수명이 'cmd_vel_linear'인지 'cmd_linear'인지 확인!
        self.cmd_pose.cmd_vel_linear = msg.linear.x
        # 조종 명령으로 받은 각속도를 저장 (위치 정보와 변수명이 겹치지 않게 주의)
        self.cmd_pose.cmd_vel_angular = msg.angular.z 
        

    def timer_callback(self):
        self.publisher.publish(self.cmd_pose)
        self.get_logger().info('Publishing combined Cmd and Pose data...')


def main(args=None):
    rp.init(args=args)
    turtle_cmd_pose_node = CmdAndPose()
    
    try:
        rp.spin(turtle_cmd_pose_node)
    except KeyboardInterrupt:
        pass
    finally:
        turtle_cmd_pose_node.destroy_node()
        rp.shutdown()

if __name__ == '__main__':
    main()