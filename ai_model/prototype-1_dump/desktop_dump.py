import tkinter as tk
from tkinter import Toplevel, Label, Entry, Button, messagebox, simpledialog
from PIL import Image, ImageTk
import cv2
import os
import time
import subprocess
import sys


#this is old desktop app code which we used in first prototype
#DON'T USE THIS CODE


# soruce: https://stackoverflow.com/questions/7674790/bundling-data-files-with-pyinstaller-onefile
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)



def capture_images(name, num_images=100, update_label=None):
    folder_path = f'photos/{name}'
    os.makedirs(folder_path, exist_ok=True)

    camera = cv2.VideoCapture(0)
    count = 0
    start_time = time.time()

    cv2.namedWindow("Face Check")

    while True:
        result, frame = camera.read()
        if not result:
            print("Can't get a frame")
            break

        cv2.imshow("Face Check", frame)
        if time.time() - start_time >= 0.3:
            img_name = os.path.join(folder_path, f"{name}_{count:04}.png")
            cv2.imwrite(img_name, frame)
            print(f"{img_name} saved.")
            count += 1
            start_time = time.time()

        if count >= num_images:
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()

def start_capture():
    def submit_name():
        user_name = entry.get()
        if user_name:
            capture_images(user_name)
            input_dialog.destroy()

    input_dialog = Toplevel(root)
    input_dialog.title("Enter Name")
    input_dialog.geometry("400x400")
    input_dialog.configure(bg="Black")

    label = Label(input_dialog, text="Enter your name:", bg="Black", fg="White")
    label.pack(pady=(100, 10))

    entry = Entry(input_dialog)
    entry.pack(pady=10)

    submit_button = Button(input_dialog, text="Submit", command=submit_name)
    submit_button.pack(pady=20)

def face_detect():
    script_path = resource_path("detect.py")
    try:
        subprocess.run(["python", script_path], check=True)
        messagebox.showinfo("Complete", "Detection complete")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"An error occurred during detection: {e}")

root = tk.Tk()
root.title("Enrollment App")
root.geometry("1960x1080")

my_image = Image.open(resource_path("FaceCheckLogo.png"))
photo = ImageTk.PhotoImage(my_image)

image_label = Label(root, image=photo)
image_label.pack()


start_button = Button(root, text="Add A New Student", command=start_capture, font=("Helvetica", 16))
start_button.pack(pady=40)

train_button = Button(root, text="Face Detection", command=face_detect,font=("Helvetica", 16))
train_button.pack(pady=20)

root.mainloop()
