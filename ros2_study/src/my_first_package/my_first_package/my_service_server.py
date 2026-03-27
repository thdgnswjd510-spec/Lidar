import rclpy as rp
from rclpy.node import Node
import numpy as np
from my_first_package_msgs.srv import MultiSpawn
from turtlesim.srv import TeleportAbsolute, Spawn
import time

class MultiSpawning(Node):

    def __init__(self):
        super().__init__('multi_spawn')
        self.server = self.create_service(MultiSpawn, 'multi_spawn', self.callback_service)
        self.spawn = self.create_client(Spawn, '/spawn')
        
     
        while not self.spawn.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Spawn service not available, waiting...')
            
        self.center_x = 5.54
        self.center_y = 5.54

    def calc_position(self, n, r):
        gap_theta = 2 * np.pi / n
        theta = [gap_theta * i for i in range(n)]
        x = [r * np.cos(th) for th in theta]
        y = [r * np.sin(th) for th in theta]
        return x, y, theta

    def callback_service(self, request, response):
        x, y, theta = self.calc_position(request.num, 3)

        for n in range(len(theta)):
            req = Spawn.Request()
            
           
            req.x = float(x[n] + self.center_x)
            req.y = float(y[n] + self.center_y)
            req.theta = float(theta[n]+(np.pi/2))
            
            
            timestamp = self.get_clock().now().nanoseconds
            req.name = f"turtle_multi_{n}_{str(timestamp)[-4:]}" 
            
          
            self.spawn.call_async(req)
            time.sleep(0.05)

        response.x = [float(val) for val in x]
        response.y = [float(val) for val in y]
        response.theta = [float(val) for val in theta]

        self.get_logger().info(f'{request.num} turtles are being spawned!')
        return response

def main(args=None):
    rp.init(args=args)
    multi_spawn = MultiSpawning()
    try:
        rp.spin(multi_spawn)
    except KeyboardInterrupt:
        pass
    finally:
        multi_spawn.destroy_node()
        rp.shutdown()

if __name__ == '__main__':
    main()