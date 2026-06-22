import queue

import shutil

import subprocess 
import threading

from pathlib import Path

import rclpy
from rclpy.node import Node

from std_msgs.msg import String

class CutieSpeakerNode(Node):
    def __init__(self):
        super().__init__('cutie_speaker')

        self.declare_parameter('voice_model_path', '/home/phoenix/projects/Cutie/models/voices/female/en_US-amy-medium.onnx')
        self.declare_parameter('output_wav_path', '/tmp/cutie_speaker_output.wav')
        self.declare_parameter('audio_player', 'aplay')
        self.declare_parameter('max_text_length', 300)

        self.voice_model_path = self.get_parameter('voice_model_path').value
        self.output_wav_path = self.get_parameter('output_wav_path').value
        self.audio_player = self.get_parameter('audio_player').value
        self.max_text_length = self.get_parameter('max_text_length').value


        self.speech_queue=queue.Queue()

        self.status_publisher = self.create_publisher(
            String,
            '/cutie/speaker/status',
            10
            
        )

        self.say_subscriber = self.create_subscription(
            String,
            'cutie/speaker/say',
            self.handle_say_message,
            10,
        )

        self.worker_thread = threading.Thread(
            target=self.speech_worker,
            daemon=True
        )

        self.worker_thread.start()

        self.publish_status('idle')


        self.get_logger().info('Cutie speaker node started.')
        self.get_logger().info('listening on /cutie/speaker/say')
        self.get_logger().info(f'Voice Model: {self.voice_model_path}')

    
    def clean_text(self, text:str) -> str:
        cleaned = text.strip()

        if not cleaned:
            return ""

        if len(cleaned) > self.max_text_length:
            cleaned = cleaned[ : self.max_text_length]
            self.get_logger().warn('Speech text was too long and got shortened')

        return cleaned
    


    #defining the queue line for the TTS 
    def handle_say_message(self, msg:String):
        text = self.clean_text(msg.data)

        if not text:
            self.get_logger().warn('Received empty speech')
            return
        
        self.speech_queue.put(text)

        self.publish_status('queued')

        self.get_logger().info(f'Queued speech: {text}')


    
    def speech_worker(self):
        '''
        This is the background worker for speech to text conversion
        '''

        while True:
            text =self.speech_queue.get()

            try:
                self.generate_speech(text)
                self.play_speech()

                self.publish_status('done')

            except Exception as error:
                self.get_logger().error(f'Speech failed: {error}')
                self.publish_status('error')
            
            finally:
                self.publish_status('idle')
                self.speech_queue.task_done()

    

    def generate_speech(self, text:str):
        model_path = Path(self.voice_model_path).expanduser()
        output_path = Path(self.output_wav_path).expanduser()

        if not model_path.exists():
            raise RuntimeError (f'voice model not found at : {model_path}')
        
        if not shutil.which('piper'):
            raise RuntimeError('Piper command not found. Install pyper-tts or check $PATH')
        
        self.publish_status('generating')

        self.get_logger().info('Generating speech with piper..."')

        command = [
            'piper',
            '--model',
            str(model_path),
            '--output-file',
            str(output_path)

        ]

        subprocess.run(
            command,
            input=text,
            text=True,
            check=True,
            timeout=30
        )

        self.get_logger().info(f'Generated speech WAV: {output_path}')


    def play_speech(self):
        output_path = Path(self.output_wav_path).expanduser()

        if not output_path:
            raise FileNotFoundError(f'Generated WAV not found: {output_path} ')
        
        if not shutil.which(self.audio_player):
            raise RuntimeError(f'Audio player not found: {self.audio_player}')
        
        self.publish_status('speaking')

        self.get_logger().info('playing generated speech')

        subprocess.run(
            [self.audio_player, '-q', str(output_path)],
            check=True,
            timeout=30
        )

        self.get_logger().info('finished playing the speech.')

    
    def publish_status(self, status:str):
        msg=String()
        msg.data = status

        self.status_publisher.publish(msg)
        




def main(args=None):
    rclpy.init(args=args)
    node=CutieSpeakerNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        node.get_logger().info('Cutie Speaker node stopped by user')
    
    finally:
        node.destroy_node()
        rclpy.shutdown()


    
if __name__ == '__main__':
    main()

        













        








        


