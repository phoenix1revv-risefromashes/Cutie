import math
import signal

import subprocess

import sys

import subprocess

from array import array

import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32
from std_msgs.msg import String


class CutieMicNode(Node):

    def __init__(self):
        super().__init__("cutie_mic")

        self.declare_parameter('device', "hw:CARD=Array,DEV=0")
        self.declare_parameter('sample_rate', 16000)
        self.declare_parameter('channels', 2)
        self.declare_parameter('chunk_duration', 0.1)
        self.declare_parameter("sound_threshold", 0.016)


        self.device = self.get_parameter('device').value
        self.sample_rate = int(self.get_parameter('sample_rate').value)
        self.channels= int(self.get_parameter('channels').value)
        self.chunk_duration = float(self.get_parameter('chunk_duration').value)
        self.sound_threshold = float(self.get_parameter('sound_threshold').value)


        self.bytes_per_sample = 2

        self.frames_per_chunk = int(self.sample_rate * self.chunk_duration)

        self.bytes_per_chunk = (self.frames_per_chunk *  self.bytes_per_sample)

        
        #Creating publishers:
        self.loudness_publisher = self.create_publisher(Float32,
                                                        "/cutie/mic/loudness",
                                                        10)
        
        self.status_publisher=self.create_publisher(
            String,
            'cutie/mic/status',
            10
        )
        
        self.last_status = None

        
        
       


        self.timer = self.create_timer(
            self.chunk_duration,
            self.process_audio_chunk
        )


        self.get_logger().info("cutie_mic node started...")
        self.get_logger().info(f"Device: {self.device}")
        self.get_logger().info(f"Sample Rate: {self.sample_rate} Hz")
        self.get_logger().info(f"Channels: {self.channels}")
        self.get_logger().info(f'Sound Threshold: {self.sound_threshold}')
        
        self.audio_process = self.start_audio_capture()

        

    def start_audio_capture(self):
        command = [
            'arecord',
            '-q',
            '-D',
            str(self.device),
            '-f',
            "S16_LE",
            '-r',
            str(self.sample_rate),
            '-c',
            str(self.channels),
            '-t',
            'raw',
        ]

        try:

            return subprocess.Popen(
                command,
                stdout = subprocess.PIPE,
                stderr= subprocess.PIPE,
                preexec_fn=lambda : signal.signal(signal.SIGINT, signal.SIG_IGN)

                
            )
        except FileNotFoundError:
            self.getl_logger().error('arecord not found. Install alsa-utils.')
            raise
        
        except Exception as error :
            self.get_logger().error(f'Failed to start arecord: {error}')
            raise

    
        

    
    def process_audio_chunk(self):

        if self.audio_process.poll() is not None:
            self.publish_status('mic_erros')
            self.get_logger().error("arecord stopped unexpectedly")
            return
        
        raw_audio = self.audio_process.stdout.read(self.bytes_per_chunk)

        if not raw_audio:
            self.publish_status("Mic error")
            self.get_logger().warning("No microphone audio received")
            return
        
        loudness = self.calculate_rms_loudness(raw_audio)

        self.publish_loudness (loudness)

        if loudness>= self.sound_threshold:
            self.publish_status("sound_detected")
        else:
            self.publish_status("quiet")


    
    def publish_loudness(self,loudness):
        message = Float32()
        message.data= float(loudness)
        
        self.loudness_publisher.publish(message)


    
    def publish_status(self,status):
        message= String()
        message.data= status

        self.status_publisher.publish(message)

        if status !=self.last_status:
            self.get_logger().info(f'mic status: {status}')
            self.last_status = status
        



    def calculate_rms_loudness(self,raw_audio):
        samples = array('h')
        samples.frombytes(raw_audio)

        if sys.byteorder !='little':
            samples.byteswap()

        if not samples:
            return 0.00
        
        square_sum = sum(sample * sample for sample in samples)
        mean_square = square_sum/len(samples)
        rms = math.sqrt(mean_square)

        return rms/32768.0
    


    def destroy_node(self):

        if hasattr(self, 'audio_process') and self.audio_process:
            self.audio_process.terminate()

            try:
                self.audio_process.wait(timeout=2.0)

            except subprocess.TimeoutExpired():
                self.audio_process.kill()
            
            super().__destroy_node()
    


def main(args=None):
    rclpy.init(args=args)

    node = CutieMicNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()

        rclpy.shutdown()




if __name__ == '__main__':
    main()


        






    