import rclpy
from rclpy.node import Node
from std_srvs.srv import SetBool # 예시: 로봇 동작 스위치

class RobotControlServer(Node):
    def __init__(self):
        super().__init__('robot_control_server')
        # 'set_robot_mode'라는 이름의 서비스 서버 생성
        self.srv = self.create_service(SetBool, 'set_robot_mode', self.control_callback)

    def control_callback(self, request, response):
        if request.data:
            self.get_logger().info('로봇 주행 모드 활성화!')
            response.success = True
            response.message = "Robot is now in AUTO mode."
        else:
            self.get_logger().info('로봇 정지 모드!')
            response.success = True
            response.message = "Robot is now in MANUAL mode."
        return response

def main():
    rclpy.init()
    node = RobotControlServer()
    rclpy.spin(node)
    rclpy.shutdown()