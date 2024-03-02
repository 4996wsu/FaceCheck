import tkinter as tk
from tkinter import Label, Button, Entry
from PIL import Image, ImageTk
import cv2
import numpy as np
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
import os
import sys
import threading  # For running the attendance process without freezing the GUI
import time
# Assuming recognition.py functions are accessible as described
from recognition import setup_device, load_models, prepare_data, recognize_faces, update_attendance

# Function to handle resource paths (for PyInstaller)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Function to start attendance process
def start_attendance(class_section):
    def attendance_process():
        device = setup_device()
        mtcnn, resnet = load_models(device)
        embedding_list, name_list = prepare_data(device, mtcnn, resnet)
        cam = cv2.VideoCapture(1)

        while True:
            ret, frame = cam.read()
            if not ret:
                print("Failed to grab frame, try again")
                continue

            recognized_names = recognize_faces(frame, device, mtcnn, resnet, embedding_list, name_list)
            if recognized_names:
                print(f"Recognized {len(recognized_names)} faces: {', '.join(recognized_names)}")
                update_attendance(recognized_names, class_section.get())  # Use the class_section from Entry widget
            else:
                print("No recognized people in the frame.")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            time.sleep(10)  # Wait for 10 seconds before capturing the next frame

        cam.release()
        cv2.destroyAllWindows()

    # Start attendance process in a separate thread to prevent GUI freezing
    threading.Thread(target=attendance_process).start()

# GUI setup
root = tk.Tk()
root.title("Enrollment and Attendance App")
root.geometry("800x600")

my_image = Image.open(resource_path("FaceCheckLogo.png"))
photo = ImageTk.PhotoImage(my_image)

image_label = Label(root, image=photo)
image_label.pack(pady=20)

# Class section input
class_section_label = Label(root, text="Enter Class Section:", font=("Helvetica", 12))
class_section_label.pack()
class_section_entry = Entry(root, font=("Helvetica", 12))
class_section_entry.pack()

attendance_button = Button(root, text="Start Attendance", font=("Helvetica", 16), command=lambda: start_attendance(class_section_entry))
attendance_button.pack(pady=20)

root.mainloop()
