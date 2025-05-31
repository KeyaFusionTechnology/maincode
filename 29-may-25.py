import cv2
import numpy as np
import os
import time
import serial
from queue import Queue
import threading


input_folder = r"D:\image\rejected_shell"

arduino = serial.Serial(port='COM3', baudrate=115200)
command_queue = Queue()

def send_commands():
    while True:
        try:
            command = command_queue.get()
            if command is None:
                break
            arduino.write(command.encode('utf-8'))
            command_queue.task_done()
        except Exception as e:
            print(f"Error in send_commands: {e}")
            command_queue.task_done()

serial_thread = threading.Thread(target=send_commands, daemon=True)
serial_thread.start()

def check_rgb(image):
    try:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    except Exception as e:
        print(f"Error converting image to HSV: {e}")
        return False, False

    mask_red = cv2.inRange(hsv, np.array([10, 50, 90]), np.array([20, 90, 110]))
    mask_red2 = cv2.inRange(hsv, np.array([21, 59, 13]), np.array([37, 43, 21]))
    mask_red3 = cv2.inRange(hsv, np.array([15, 60, 10]), np.array([20, 70, 20]))
    mask_red4 = cv2.inRange(hsv, np.array([19, 28, 39]), np.array([19, 96, 7]))
    mask_red5 = cv2.inRange(hsv, np.array([25, 50, 70]), np.array([25, 75, 9]))

    mask_shell = cv2.inRange(hsv, np.array([8, 30, 9]), np.array([13, 255, 140]))
   
    mask_orange=cv2.inRange(hsv,np.array([26,21,20]),np.array([26,91,81]))
    
    orange_detected=np.count_nonzero(mask_orange)>150
    red_detected = np.count_nonzero(mask_red ) > 200
    red_detected1 = np.count_nonzero(mask_red2) > 200
    red_detected2 = np.count_nonzero(mask_red3 ) > 200
    red_detected3 = np.count_nonzero(mask_red4 ) > 100
    red_detected4 = np.count_nonzero(mask_red5) > 70

    red_dect = red_detected or red_detected1 or red_detected2 or red_detected3 or red_detected4
    shell_detected = np.count_nonzero(mask_shell) > 300

    return shell_detected, red_dect,orange_detected

def process_image(image_path):
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"Skipping {os.path.basename(image_path)}: Can't read.")
            return

        start_time = time.time()
        shell_detected, red_dect, orange_detected = check_rgb(image)
        filename = os.path.basename(image_path)

        if shell_detected:
            grade='shell'
            print(f"Processed: {filename} | Grade: {grade} | Time: {time.time() - start_time:.2f}s")
            command_queue.put('15|')
        elif red_dect:
            grade='red'
            print(f"Processed: {filename} | Grade: {grade} | Time: {time.time() - start_time:.2f}s")
            command_queue.put('15|')
        
        elif orange_detected:
            grade='orange'
            print(f"Processed: {filename} | Grade: {grade} | Time: {time.time() - start_time:.2f}s")
            command_queue.put('15|')

        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            white_pixel_count = np.count_nonzero(binary)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            black_dot_count = sum(1 for cnt in contours if cv2.contourArea(cnt) >= 200)

            if black_dot_count > 1:
                grade='blackdot'
                print(f"Processed: {filename} | Grade: {grade} | Time: {time.time() - start_time:.2f}s")
                command_queue.put('16|')
            else:
                if 35001 <= white_pixel_count <= 102000:
                    command_queue.put('14|')
                    grade = "180"
                elif 25001 <= white_pixel_count <= 35000:
                    command_queue.put('13|')
                    grade = "240"
                elif 22001 <= white_pixel_count <= 25000:
                    command_queue.put('12|')
                    grade = "320"
                elif 13000 <= white_pixel_count <= 22000:
                    command_queue.put('11|')
                    grade = "400"
                else:
                    grade = "1000"

                print(f"Processed: {filename} | Grade: {grade} | Pixels: {white_pixel_count} | Time: {time.time() - start_time:.2f}s")

        os.remove(image_path)

    except Exception as e:
        print(f"Error processing {image_path}: {e}")

def watch_folder():
    print("Watching folder for new images...")
    while True:
        files = sorted([os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.lower().endswith(".bmp")])
        if files:
            process_image(files[0])
        else:
            time.sleep(0.0001)

if __name__ == "__main__":
    watch_folder()
