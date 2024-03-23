import tkinter as tk
from tkinter import Label, Button, Entry, messagebox
from PIL import Image, ImageTk
import cv2
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
import os
import sys
import threading
import time
from database import combine_pt_files, download_file_combine, retrieve_encodings_from_class, retrieve_class_embedding, retrieve_encodings_from_class, update_class_encoding, download_pt_file_student, get_doc
from recognition import setup_device, load_models, prepare_data, recognize_faces,recognize_faces, update_attendance
from firebase_admin import firestore, credentials, initialize_app
from pathlib import Path
import firebase_admin
from datetime import datetime, timedelta
import numpy as np

if not firebase_admin._apps:
    cred_path = 'db_credentials.json'
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {'storageBucket': 'facecheck-93450.appspot.com'})

db = firestore.client()




# this is not the file to use 
#don't use it 












def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def class_section_validation(class_section):
    doc = get_doc("class_doc")
    class_list = list(doc['classes'].keys())
    if class_section in class_list:
        return True, doc['classes'][class_section]
    return False, None

def time_validation(class_info):
    now = datetime.now()
    week_day = now.strftime("%A")
    if week_day in class_info['schedule']:
        class_start_new = class_info['schedule'][week_day][0].replace('.', ':')
        class_end_new = class_info['schedule'][week_day][1].replace('.', ':')

        class_start_time = datetime.strptime(class_start_new, '%H:%M')
        class_end_time = datetime.strptime(class_end_new, '%H:%M')

        class_start_time = now.replace(hour=class_start_time.hour, minute=class_start_time.minute, second=0, microsecond=0)
        class_end_time = now.replace(hour=class_end_time.hour, minute=class_end_time.minute, second=0, microsecond=0)

        if class_start_time - timedelta(minutes=15) <= now <= class_end_time:
            return True
    return False

attendance_running = False

def attempt_start_attendance():
    class_section = class_section_entry.get().upper()
    exists, class_data = class_section_validation(class_section)
    
    if not exists:
        messagebox.showerror("Error", "Class section does not exist. Please enter a valid one.")
        return
    
    if retrieve_class_embedding(class_section) != "NO ENCODING":
        download_file_combine(retrieve_class_embedding(class_section), f'{class_section}.pt')
    else:
        combine_pt_files(class_section)

    threading.Thread(target=start_attendance, args=(class_section,)).start()
    
    # Hide Start Attendance button and show End Attendance button
    class_section_label.config(text=f"Class Section: {class_section}")
    attendance_button.pack_forget()
    end_attendance_button.pack(pady=20)

def start_attendance(class_section):
    def attendance_process():
        global attendance_running

        attendance_running = True
        device = setup_device()
        mtcnn, resnet = load_models(device)
        
        embedding_list, name_list = torch.load(f'{class_section}.pt', map_location=device)
        cam = cv2.VideoCapture(0)

        while attendance_running:
            ret, frame = cam.read()
            if not ret:
                print("Failed to grab frame, try again")
                continue
            cv2.imshow('frame', frame)

            recognized_names = recognize_faces(frame, device, mtcnn, resnet, embedding_list, name_list)
            

            if recognized_names:
                print(f"Recognized {len(recognized_names)} faces: {', '.join(recognized_names)}")
                update_attendance(recognized_names, class_section)
            else:
                print("No recognized people in the frame.")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            time.sleep(50)

        cam.release()
        cv2.destroyAllWindows()

    threading.Thread(target=attendance_process).start()

def stop_attendance():
    global attendance_running
    attendance_running = False
    class_section_label.config(text="")
    #os.remove('CSC_4996_001.pt')
    
    # Hide End Attendance button and show Start Attendance button
    end_attendance_button.pack_forget()
    attendance_button.pack(pady=20)
    
    messagebox.showinfo("Attendance", "Attendance has ended.")  

root = tk.Tk()
root.title("Enrollment and Attendance App")
root.geometry("1000x900")

my_image = Image.open(resource_path("FaceCheckLogo.png"))
photo = ImageTk.PhotoImage(my_image)

image_label = Label(root, image=photo)
image_label.pack(pady=20)

class_section_label = Label(root, text="", font=("Helvetica", 12))
class_section_label.pack()

class_section_entry = Entry(root, font=("Helvetica", 12))
class_section_entry.pack()

attendance_button = Button(root, text="Start Attendance", font=("Helvetica", 16), command=attempt_start_attendance)
attendance_button.pack(pady=20)

end_attendance_button = Button(root, text="End Attendance", font=("Helvetica", 16), command=stop_attendance)
# Initially hide the End Attendance button
end_attendance_button.pack_forget()

root.mainloop()
