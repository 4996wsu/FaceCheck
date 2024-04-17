import tkinter as tk
from tkinter import ttk
from tkinter import Label, Button, Entry, messagebox
from PIL import Image, ImageTk
import cv2
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
import os
import sys
import threading
import time
from database import combine_pt_files, download_file_combine, retrieve_encodings_from_class, retrieve_class_embedding, retrieve_encodings_from_class, update_class_encoding, download_pt_file_student, get_doc, get_low_attendance_students,update_overall_attendance,getDate,get_class_id
from recognition import setup_device, load_models, prepare_data, recognize_faces, update_attendance
from firebase_admin import firestore, credentials, initialize_app
from pathlib import Path
import firebase_admin
from datetime import datetime, timedelta
import numpy as np
from database import get_name, get_class_name
from database import update_class_photo,getTime

# Global variables
global attendance_running
attendance_running = False
global_class_id = ""



# Firebase setup
if not firebase_admin._apps:
    cred_path = 'db_credentials.json'
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {'storageBucket': 'facecheck-93450.appspot.com'})
# Initialize Firestore DB
db = firestore.client()

#function to get resource path(pictures)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

#function to validate class id
def class_id_validation(class_id):
    doc = get_doc("class_doc")
    class_list = list(doc['classes'].keys())
    if class_id in class_list:
        return True, doc['classes'][class_id]
    return False, None

#function to get the validate the class time
def time_validation(class_info):
    now = datetime.now()
    week_day = now.strftime("%A")
    if week_day in class_info['schedule']:

        # change the format
        class_start_new = class_info['schedule'][week_day][0].replace('.', ':')
        class_end_new = class_info['schedule'][week_day][1].replace('.', ':')

        # Convert the class start and end times to datetime objects
        class_start_time = datetime.strptime(class_start_new, '%H:%M')
        class_end_time = datetime.strptime(class_end_new, '%H:%M')

        # Set the class start and end times to the current date with the specified hour and minute
        class_start_time = now.replace(hour=class_start_time.hour, minute=class_start_time.minute, second=0, microsecond=0)
        class_end_time = now.replace(hour=class_end_time.hour, minute=class_end_time.minute, second=0, microsecond=0)

        # It gives professor 15 minutes more time to start the class
        if class_start_time - timedelta(minutes=15) <= now <= class_end_time:
            return True
    return False



#function that will check the inputted class id and time is valid or not
def attempt_start_attendance():
    # it will validate the class id and time and accordingly start the attendance and also create/download the class embedding
    global global_class_id  # Refer to the global variable

    # Validate the user's selections
    if any([
        subject_combobox.get() == "Select subject",
        course_number_combobox.get() == "Select course number",
        class_section_combobox.get() == "Select class section",
        term_combobox.get() == "Select term",
        year_combobox.get() == "Select year",
    ]):
        messagebox.showerror("Error", "Please make valid selections for all fields.")


    #change the format of term code
    term_code_mapping = {"Summer": "S", "Winter": "W", "Fall": "F"}
    selected_term_code = term_code_mapping.get(term_combobox.get(), None)
    # Check if the term code is valid
    if selected_term_code is None:
        messagebox.showerror("Error", "Please select a valid term.")
        return
    # Construct the class ID to make it so that it matches the format in the database
    class_id = f"{subject_combobox.get()}_{course_number_combobox.get()}_{class_section_combobox.get()}_{selected_term_code}_{year_combobox.get()}"
    
    # Check if all dropdown menus have been selected
    if not all([subject_combobox.get(), course_number_combobox.get(), class_section_combobox.get(), selected_term_code, year_combobox.get()]):
        messagebox.showerror("Error", "Please select all class information.")
        return
    # Check if the class ID exists
    exists, class_data = class_id_validation(class_id)
    if not exists:
        messagebox.showerror("Error", "Class ID does not exist. Please enter a valid one.")
        return
    # retrieve the class embedding
    global_class_id = class_id
    if retrieve_class_embedding(class_id) != "NO ENCODING":
        download_file_combine(retrieve_class_embedding(class_id), f'{class_id}.pt')
    # If the class embedding does not exist, combine the PT files and save that in the database
    else:
        combine_pt_files(class_id) 
    
    #GET THE CLASS INFO
    class_name =get_class_name(class_id)
    class_id_label.config(text=f"{class_name}")
    attendance_button.pack_forget()
    end_attendance_button.pack(pady=20)

    # Start a new thread to handle the attendance process
    threading.Thread(target=start_attendance, args=(class_id,)).start()



def start_attendance(class_id):
    # Start the attendance process and that's why attendance_running is set to True
    global attendance_running
    attendance_running = True

    #start the attendance process
    def attendance_process():
        global_class_id = class_id  # Ensure access to the global variable

        # Set up the device and load the models
        device = setup_device()
        mtcnn, resnet = load_models(device)
        
        # Retrieve the embeddings and names from the PT file
        embedding_list, name_list = torch.load(f'{class_id}.pt', map_location=device)
        cam = cv2.VideoCapture(0)

        #ensure the attendance is taken every 3 minutes
        last_update_time = datetime.now() - timedelta(minutes=3)
        recognized_names = []
        
        # Run the attendance process
        while attendance_running:

            # Capture the frame from the webcam
            ret, frame = cam.read()
            if not ret:
                print("Failed to grab frame, try again")
                continue
            # Resize the frame for better performance
            current_time = datetime.now()
            
            # Recognize the faces in the frame
            temp_recognized_names, annotated_frame = recognize_faces(frame, device, mtcnn, resnet, embedding_list, name_list)
            recognized_names.extend(temp_recognized_names)

            cv2.imshow('Live Attendance Monitoring', annotated_frame)

            # Update the attendance every 10 seconds(Chnage the time to 10 seconds for testing purpose)
            if (current_time - last_update_time) >= timedelta(seconds=10):
                #get the date and time
                date= getDate()
                time=getTime()
        
                print(f"Updating attendance for {len(set(recognized_names))} faces")

                # Update the class photo and attendance
                update_class_photo(class_id, frame,date,time)
                update_attendance(set(recognized_names), class_id,date,time)
                recognized_names = []
                last_update_time = current_time

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cam.release()
        cv2.destroyAllWindows()
    # Start the attendance process in a new thread
    threading.Thread(target=attendance_process).start()

def reset_ui():
    # Clear the window and dropdown frames
    clear_window()
    
    # Repack the image and label at the top
    image_label.pack(pady=20)
    class_id_label = Label(root, text="Select Your Class Information", font=("Helvetica", 16, "bold"))
    class_id_label.pack()

    # Repack the frames for dropdown menus
    row1_frame.pack(pady=5)
    row2_frame.pack(pady=5)
    
    # Reset the combobox selections to the placeholder values
    subject_combobox.set("Select subject")
    course_number_combobox.set("Select course number")
    class_section_combobox.set("Select class section")
    term_combobox.set("Select term")
    year_combobox.set("Select year")

    # Repack the comboboxes into their respective frames
    subject_combobox.pack(side=tk.LEFT, padx=10)
    course_number_combobox.pack(side=tk.LEFT, padx=10)
    class_section_combobox.pack(side=tk.LEFT, padx=10)
    term_combobox.pack(side=tk.LEFT, padx=10)
    year_combobox.pack(side=tk.LEFT, padx=10)

    # Show the "Start Attendance" button again
    attendance_button.pack(pady=20)

#function to clear the window
def clear_window():
    for widget in root.pack_slaves():
        widget.pack_forget()


#function to show the list of students with low attendance as option
def show_low_attendance_options(student_ids):
    # Clear the window to show the low attendance options
    clear_window()

    attention_label = Label(root, text="Attention Needed!", font=("Helvetica", 16, "bold"), pady=20)
    attention_label.pack()

    subtitle_label = Label(root, text="Please select IDs to adjust attendance", font=("Helvetica", 14), pady=10)
    subtitle_label.pack()
    names=get_name(student_ids)
    # Create a checkbox for each student
    global checkbox_vars
    checkbox_vars = {student_id: tk.IntVar() for student_id in student_ids}

    list_frame = tk.Frame(root)
    list_frame.pack(pady=20)
    i=0
    for student_id, var in checkbox_vars.items():
        tk.Checkbutton(list_frame, text=f"{names[i]} {student_id} ", variable=var, font=("Helvetica", 14)).pack(anchor=tk.CENTER)
        i=i+1
    # submit button for the low attendance students
    global submit_button
    submit_button = Button(root, text="Submit", font=("Helvetica", 16), command=process_manual_attendance)
    submit_button.pack(pady=20)


#function to check the low attendance students
def check_low_attendance_students(section):
    # Get the low attendance students from the database.py file
    low_attendance_students = get_low_attendance_students(section)
    if low_attendance_students:
        # Show the low attendance students as options
        show_low_attendance_options(low_attendance_students)
    else:
        messagebox.showinfo("Attendance", "No students with low attendance.")
        # Reset the UI for the new session
        reset_ui()



def stop_attendance():
    global global_class_id  # Ensure access to the global variable
    # Set the attendance_running variable to False to stop the attendance process
    global attendance_running
    attendance_running = False

    # Hide the end attendance button 
    end_attendance_button.pack_forget()
    attendance_button.pack(pady=20)  

    messagebox.showinfo("Attendance", "Attendance has ended.")
    os.remove(f'{global_class_id}.pt')


    # Check for low attendance students
    if global_class_id:  # Check if global_class_id has been set
        check_low_attendance_students(global_class_id) 
    else:
        print("No class ID was set. No low attendance check performed.")
    



#function to process the manual selection of students
def process_manual_attendance():
    global global_class_id  

    # Use the globally stored class_id
    class_id = global_class_id
    selected_students = [student_id for student_id, var in checkbox_vars.items() if var.get() == 1]
    all_students = checkbox_vars.keys()

    # Process each student, setting attendance based on selection
    for student_id in all_students:
        isSelected = student_id in selected_students
        # Call update_overall_attendance from the database.py file
        update_overall_attendance(class_id, student_id, isSelected, getDate())

    print("Selected students:", selected_students)
    # Reset the UI for the new session
    reset_ui()

# Custom combobox class to set the font size for the dropdown menus
class CustomCombobox(ttk.Combobox):
    def __init__(self, parent, values, font_size, **kwargs):
        self.font_size = font_size
        self.font = ("Helvetica", self.font_size)
        super().__init__(parent, values=values, font=self.font, **kwargs)
        self.option_add('*TCombobox*Listbox.Font', self.font)



# UI Setup
root = tk.Tk()
root.title("Enrollment and Attendance App")
root.geometry("1000x600")

# Image display
my_image = Image.open(resource_path("FaceCheckLogo.png"))
photo = ImageTk.PhotoImage(my_image)
image_label = Label(root, image=photo)
image_label.pack(pady=20)

class_id_label = Label(root, text="Select Your Class Information", font=("Helvetica", 16, "bold"))
class_id_label.pack()

# Dropdown menus for class detail selection
subjects, course_numbers, class_sections, terms, years = get_class_id('class_doc')
row1_frame = tk.Frame(root)
row2_frame = tk.Frame(root)

# Pack frames into the window
row1_frame.pack(pady=10)
row2_frame.pack(pady=10)

# Create comboboxes for the user to select class information
subject_combobox = CustomCombobox(row1_frame, values=["Select subject"] + subjects, font_size=12, state="readonly")
course_number_combobox = CustomCombobox(row1_frame, values=["Select course number"] + course_numbers, font_size=12, state="readonly")
class_section_combobox = CustomCombobox(row1_frame, values=["Select class section"] + class_sections, font_size=12, state="readonly")
term_combobox = CustomCombobox(row2_frame, values=["Select term"] + terms, font_size=12, state="readonly")
year_combobox = CustomCombobox(row2_frame, values=["Select year"] + years, font_size=12, state="readonly")

# Set the comboboxes to display the placeholder text by default
subject_combobox.current(0)
course_number_combobox.current(0)
class_section_combobox.current(0)
term_combobox.current(0)
year_combobox.current(0)


# Pack the comboboxes into their respective frame
subject_combobox.pack(side=tk.LEFT, padx=10)
course_number_combobox.pack(side=tk.LEFT, padx=10)
class_section_combobox.pack(side=tk.LEFT, padx=10)

term_combobox.pack(side=tk.LEFT, padx=10)
year_combobox.pack(side=tk.LEFT, padx=10)

# Attendance control buttons
attendance_button = Button(root, text="Start Attendance", font=("Helvetica", 16), command=attempt_start_attendance)
attendance_button.pack(pady=20)

end_attendance_button = Button(root, text="End Attendance", font=("Helvetica", 16), command=stop_attendance)
end_attendance_button.pack_forget()

root.mainloop()