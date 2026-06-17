import rclpy
import cv2

from rclpy.node import Node

from sensor_msgs.msg import Image

from cv_bridge import CvBridge

class CameraNode(Node):

    def __init__(self):
        super().__init__('cutie_camera_node')
        self.declare_parameter('camera_index',0)
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)
        self.declare_parameter('fps', 30)
        self.declare_parameter('topic_name', '/cutie/camera/image_raw')

        self.camera_index = self.get_parameter('camera_index').value
        self.frame_width = self.get_parameter('frame_width').value
        self.frame_height = self.get_parameter('frame_height').value
        self.fps = self.get_parameter('fps').value
        self.topic_name = self.get_parameter('topic_name').value



        self.bridge= CvBridge()



        self.image_publisher = self.create_publisher(Image, 
                                                     self.topic_name,
                                                     10)
        


        self.camera= cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
        if not self.camera.isOpened():
            self.get_logger().error(
                f'Could not open camera {self.camera_index}\n'
                f'Try checking camea with : v4l2 --list-devices'
            )
            raise RuntimeError('failed to open camera')
        self.get_logger().info(
            f'Camera opened successfully at index: {self.camera_index}\nPublishing to: {self.topic_name}'
        )

        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.camera.set(cv2.CAP_PROP_FPS, self.fps)


        timer_period = 1/float(self.fps)
        self.timer= self.create_timer(
            timer_period,
            self.publish_frame
        )

    

    def publish_frame(self):
        if not self.camera.isOpened():
            return
        
        success, frame = self.camera.read()

        if not success:
            self.get_logger().warn(
                f'Failed to read frames from the camera'
            )
            return

        image_msg = self.bridge.cv2_to_imgmsg(
            frame,
            encoding='bgr8'
        )

        

        image_msg.header.stamp = self.get_clock().now().to_msg()
        image_msg.header.frame_id ='cutie_camera_frame'

        self.image_publisher.publish(image_msg)



    def destroy_node(self):
        if hasattr(self, 'camera') and self.camera.isOpened():
            self.camera.release()
        super().destroy_node()



    
def main(args=None):
    rclpy.init(args=args)

    node =CameraNode()

    try:
        rclpy.spin(node)
    
    except KeyboardInterrupt:
        node.get_logger.info('Camera Node stopped by user')
    
    finally:
        node.destroy_node()
        rclpy.shutdown()





if __name__ == '__main__':
    main()




        







            
        

        

        




        
















    
