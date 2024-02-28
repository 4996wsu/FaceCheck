import tkinter as tk
from tkinter import Label, Button
from PIL import Image, ImageTk
import cv2
import numpy as np
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
import os
import sys

# Function to handle resource paths (for PyInstaller)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Function to start attendance process
def start_attendance():
    # Load face encodings and names
    data = np.load('face_encodings.npy', allow_pickle=True).item()
    names = list(data.keys())
    encodings = [torch.Tensor(encoding) for encoding in list(data.values())]

    # Initialize MTCNN and InceptionResnetV1
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    mtcnn = MTCNN(image_size=160, margin=0, keep_all=True, device=device)
    resnet = InceptionResnetV1(pretrained=None).eval().to(device)

    # Load the fine-tuned model
    model_path = 'trained_face_encoding_model_2.pt'  # Update this path to your fine-tuned model
    resnet.load_state_dict(torch.load(model_path, map_location=device))
    resnet.classify = False  # Ensure the model is set to return embeddings

    cam = cv2.VideoCapture(0)

    while True:
        ret, frame = cam.read()
        if not ret:
            print("Fail to grab frame, try again")
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)

        # Detect faces
        boxes, _ = mtcnn.detect(img)
        if boxes is not None:
            faces = mtcnn(img)

            for face, box in zip(faces, boxes):
                face = face.to(device)  # Ensure the face tensor is on the same device as the model
                emb = resnet(face.unsqueeze(0)).detach().cpu()

                # Compare face encoding with known encodings
                dists = [torch.norm(emb - encoding, p=2).item() for encoding in encodings]
                min_dist = min(dists)
                idx = dists.index(min_dist)

                name = "Unknown"
                if min_dist < 0.9:  # Threshold for matching, adjust based on your fine-tuning results
                    name = names[idx]

                # Draw rectangle and name
                box = np.array(box).astype(int)  # Convert box coordinates to integers
                frame = cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
                cv2.putText(frame, name, (box[0], box[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

        cv2.imshow("Attendance", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

# GUI setup
root = tk.Tk()
root.title("Enrollment and Attendance App")
root.geometry("800x600")

my_image = Image.open(resource_path("FaceCheckLogo.png"))
photo = ImageTk.PhotoImage(my_image)

image_label = Label(root, image=photo)
image_label.pack(pady=20)

attendance_button = Button(root, text="Start Attendance", command=start_attendance, font=("Helvetica", 16))
attendance_button.pack(pady=40)

root.mainloop()
