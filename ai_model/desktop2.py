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
from database import combine_pt_files, download_file_combine, retrieve_encodings_from_class, retrieve_class_embedding, retrieve_encodings_from_class, update_class_encoding, download_pt_file_student, get_doc, get_low_attendance_students,update_overall_attendance,getDate
from recognition import setup_device, load_models, prepare_data, recognize_faces, update_attendance
from firebase_admin import firestore, credentials, initialize_app
from pathlib import Path
import firebase_admin
from datetime import datetime, timedelta
import numpy as np

global attendance_running
attendance_running = False

if not firebase_admin._apps:
    cred_path = 'db_credentials.json'
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {'storageBucket': 'facecheck-93450.appspot.com'})

db = firestore.client()

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
    
    class_section_label.config(text=f"Class Section: {class_section}")
    attendance_button.pack_forget()
    end_attendance_button.pack(pady=20)

def start_attendance(class_section):
    global attendance_running
    attendance_running = True

    def attendance_process():
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        mtcnn, resnet = load_models(device)
        load_data = torch.load(f'{class_section}.pt', map_location=device)
        embedding_list, name_list = load_data[0], load_data[1]
        cam = cv2.VideoCapture(0)

        last_update_time = datetime.now() - timedelta(minutes=3)
        recognized_names = []

        while attendance_running:
            ret, frame = cam.read()
            if not ret:
                print("Failed to grab frame, try again")
                continue

            current_time = datetime.now()
            temp_recognized_names, annotated_frame = recognize_faces(frame, device, mtcnn, resnet, embedding_list, name_list)
            recognized_names.extend(temp_recognized_names)
            cv2.imshow('Live Attendance Monitoring', annotated_frame)

            if (current_time - last_update_time) >= timedelta(seconds=10):
                print(f"Updating attendance for {len(set(recognized_names))} faces")
                update_attendance(set(recognized_names), class_section)
                recognized_names = []
                last_update_time = current_time

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cam.release()
        cv2.destroyAllWindows()

    threading.Thread(target=attendance_process).start()


def stop_attendance():
    global attendance_running
    attendance_running = False
    class_section_label.pack_forget()
    end_attendance_button.pack_forget()
    attendance_button.pack_forget()
    image_label.pack_forget()  
    class_section_entry.pack_forget()

    messagebox.showinfo("Attendance", "Attendance has ended.")
    check_low_attendance_students(class_section_entry.get())

def check_low_attendance_students(section):
    low_attendance_students = get_low_attendance_students(section)
    if low_attendance_students:
        show_low_attendance_options(low_attendance_students)
    else:
        messagebox.showinfo("Attendance", "No students with low attendance.")
        reset_ui()

def show_low_attendance_options(student_ids):
    clear_window()

    attention_label = Label(root, text="Attention Needed!", font=("Helvetica", 16, "bold"), pady=20)
    attention_label.pack()

    subtitle_label = Label(root, text="Please select IDs to adjust attendance", font=("Helvetica", 14), pady=10)
    subtitle_label.pack()

    global checkbox_vars
    checkbox_vars = {student_id: tk.IntVar() for student_id in student_ids}

    list_frame = tk.Frame(root)
    list_frame.pack(pady=20)

    for student_id, var in checkbox_vars.items():
        tk.Checkbutton(list_frame, text=student_id, variable=var).pack(anchor=tk.CENTER)

    global submit_button
    submit_button = Button(root, text="Submit", command=process_selections)
    submit_button.pack(pady=20)

def process_selections():
    # Assuming 'section' is available globally or fetched from another source
    global class_section_entry
    section = class_section_entry.get()
    selected_students = [student_id for student_id, var in checkbox_vars.items() if var.get() == 1]
    all_students = checkbox_vars.keys()

    # Process each student, setting attendance based on selection
    for student_id in all_students:
        isSelected = student_id in selected_students
        # Assuming 'getDate()' returns the current date in the desired format
        update_overall_attendance(section, student_id, isSelected, getDate())

    print("Selected students:", selected_students)
    reset_ui()


def reset_ui():
    clear_window()
    image_label.pack(pady=20)
    class_section_label.pack()
    class_section_entry.pack()
    attendance_button.pack(pady=20)

def clear_window():
    for widget in root.pack_slaves():
        widget.pack_forget()

# def attempt_start_attendance():
#     class_section = class_section_entry.get()
#     if class_section:
#         class_section_label.config(text=class_section)
#         attendance_button.pack_forget()
#         end_attendance_button.pack(pady=20)
#         start_attendance(class_section)
#     else:
#         messagebox.showerror("Error", "Please enter a class section.")

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
end_attendance_button.pack_forget()

root.mainloop()

