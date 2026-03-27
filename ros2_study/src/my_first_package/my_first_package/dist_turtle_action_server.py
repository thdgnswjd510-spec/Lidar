import rclpy as rp
from rclpy.action import ActionServer
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from my_first_package_msgs.action import DistTurtle 
from turtlesim.msg import Pose
from geometry_msgs.msg import Twist 
import time
import math
from my_first_package.my_subscriber import TurtlesimSubscriber
from rcl_interfaces.msg import SetParametersResult

class TurtleSub_Action(TurtlesimSubscriber):
    def __init__(self, ac_server):
        super().__init__()
        self.ac_server = ac_server

    def callback(self, msg):
        self.ac_server.current_pose = msg

class DistTurtleServer(Node):
    def __init__(self):
        super().__init__('dist_turtle_action_server')
        self.total_dist = 0.0
        self.is_first_time = True
        self.current_pose = Pose()
        self.previous_pose = Pose()
        self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.action_server = ActionServer(self, DistTurtle, 'dist_turtle', self.execute_callback)
        self.declare_parameter('quantile_time', 0.75)
        self.declare_parameter('almost_goal_time', 0.95)
        self.get_logger().info('Dist turtle action server is started.')

        (quantile_time_param, almost_goal_time_param) = self.get_parameters(
            ['quantile_time', 'almost_goal_time'])
            
        self.quantile_time = quantile_time_param.value
        self.almost_goal_time = almost_goal_time_param.value

        output_msg ="quantile_time is"+str(self.quantile_time)+"."
        output_msg=output_msg+"and almost_goal_time is"+str(self.almosts_time)+"."
        self.get_logger().info(output_msg)

        
        self.add_on_set_parameters_callback(self.parameter_callback)

        print('초기 파라미터 값 설정 완료:', self.quantile_time, self.almost_goal_time)


    def parameter_callback(self, params): 
        for param in params:
            print(param.name, "is changed to", param.value)

            if param.name == 'quantile_time':
                self.quantile_time = param.value
            if param.name == 'almost_goal_time':
                self.almost_goal_time = param.value

        print('현재 업데이트된 파라미터 값:', self.quantile_time, self.almost_goal_time)
        return SetParametersResult(successful=True)

    def calc_diff_pose(self):
        if self.is_first_time:
            self.previous_pose.x = self.current_pose.x
            self.previous_pose.y = self.current_pose.y
            self.is_first_time = False
            return 0.0

        # 피타고라스 정리 괄호 수정된 상태 유지
        diff_dist = math.sqrt((self.current_pose.x - self.previous_pose.x)**2 + \
                              (self.current_pose.y - self.previous_pose.y)**2)

        # 값 복사 (주소 복사 방지)
        self.previous_pose.x = self.current_pose.x
        self.previous_pose.y = self.current_pose.y

        return diff_dist

    def execute_callback(self, goal_handle):
        self.get_logger().info('액션 목표를 수신했습니다! 거북이 출발!')
        feedback_msg = DistTurtle.Feedback()
        
        msg = Twist()
        # 원래 요청받은 초기 속도 저장
        original_linear_x = goal_handle.request.linear_x
        msg.linear.x = original_linear_x
        msg.angular.z = goal_handle.request.angular_z

        # 루프 시작 전 초기화
        self.total_dist = 0.0
        self.is_first_time = True
        target_dist = goal_handle.request.dist

        while rp.ok(): # 안전한 루프 종료 조건
            diff = self.calc_diff_pose()
            self.total_dist += diff
            
            feedback_msg.remained_dist = target_dist - self.total_dist
            goal_handle.publish_feedback(feedback_msg)

            progress_ratio = self.total_dist / target_dist if target_dist > 0 else 1.0
            

            if progress_ratio >= self.almost_goal_time:
                msg.linear.x = original_linear_x * 0.2  
            elif progress_ratio >= self.quantile_time:
                msg.linear.x = original_linear_x * 0.5  
            else:
                msg.linear.x = original_linear_x     
            # -------------------------------------------------------------------

            self.publisher.publish(msg)

            tmp=feedback_msg.remained_dist-goal_handle.request.dist+self.quantile_time
            tmp= abs(tmp)

            if tmp<0.02:
                output_msg='The turtle passes the'+str(self.quantile_time)+'point.'
                output_msg=output_msg + ':'+str(tmp)
                self.get_logger().info(output_msg)
            
            if feedback_msg.remained_dist < 0.1: # 0.1m 이내 도달 시 정지
                break
            
            time.sleep(0.01)

        # 멈춤 명령 전송
        stop_msg = Twist()
        self.publisher.publish(stop_msg)

        goal_handle.succeed()
        result = DistTurtle.Result()
        result.pos_x = self.current_pose.x
        result.pos_y = self.current_pose.y
        result.pos_theta = self.current_pose.theta
        result.result_dist = self.total_dist

        self.get_logger().info('목표 지점에 정확히 도착했습니다!')
        return result

def main(args=None):
    rp.init(args=args)

    executor = MultiThreadedExecutor()

    ac = DistTurtleServer()
    sub = TurtleSub_Action(ac_server=ac)

    executor.add_node(sub)
    executor.add_node(ac)

    try:
        executor.spin()
    finally:
        executor.shutdown()
        sub.destroy_node()
        ac.destroy_node()
        rp.shutdown()

if __name__ == '__main__':
    main()