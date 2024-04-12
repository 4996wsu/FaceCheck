import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image
import cv2
import os
import time
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import numpy as np
from database import update_student_attendance, getDate, getTime, retrieve_names_from_class

# Function to setup the device to run the models on
def setup_device():
    return torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Function to load the MTCNN and InceptionResnetV1 models
def load_models(device):
    mtcnn = MTCNN(keep_all=True, device=device)
    resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
    return mtcnn, resnet

# Function to prepare the data for face recognition by loading the embeddings and names
def prepare_data(device, section):
    if os.path.exists(f'{section}.pt'):
        return torch.load(f'{section}.pt', map_location=device)
    return None

# Function to recognize faces in a frame and return the recognized names
def recognize_faces(frame, device, mtcnn, resnet, embedding_list, name_list):
    # Convert the captured frame from BGR to RGB
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    
    # Detect faces in the frame
    img_cropped_list, prob_list = mtcnn(img, return_prob=True)
    
    recognized_names = []
    if img_cropped_list is not None:
        boxes, _ = mtcnn.detect(img)
        
        for i, prob in enumerate(prob_list):
            if prob > 0.90:  # If the detection probability is high enough

                # Get the embedding of the detected face
                emb = resnet(img_cropped_list[i].unsqueeze(0).to(device)).detach()
                # Calculate the distance between the detected face and the faces in the database
                dist_list = [torch.dist(emb, emb_db).item() for emb_db in embedding_list]
                # Find the minimum distance and the corresponding index
                min_dist = min(dist_list)
                min_dist_idx = dist_list.index(min_dist)
                # If the minimum distance is less than a threshold, consider the face recognized
                if min_dist < 0.9:
                    recognized_name = name_list[min_dist_idx]
                else:
                    recognized_name = "Unknown"
                # Append the recognized name to the list
                recognized_names.append(recognized_name)
                # Get the bounding box of the detected face
                box = boxes[i].astype(int)
                # Draw the bounding box and name on the frame
                frame = cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (255,0,0), 2)
                frame = cv2.putText(frame, f"{recognized_name} ", (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 1, cv2.LINE_AA)
            else:
                # If probability is low, consider the face as not detected/reliable enough
                #recognized_names.append("Unknown")
                continue
    return recognized_names, frame

# Function to update the attendance of the recognized students
def update_attendance(recognized_names, class_section,date ,time):
    
    # Mark present students
    for name in recognized_names:
        #use update attendance function from database.py to update the attendance of the students
        update_student_attendance(class_section, name, True, date, time)
        
    # Mark absent students (Removes present students from a list of all students first)
    students = retrieve_names_from_class(class_section)
    for name in students[:]:
        if name in recognized_names:
            students.remove(name)
            
    # Mark absent students
    for name in students:
        #use update attendance function from database.py to update the attendance of the students
        update_student_attendance(class_section, name, False, date, time)



#test function ignore this
def prepare_data_test(device, mtcnn, resnet):
    if os.path.exists('data.pt'):
        return torch.load('data.pt', map_location=device)
    
    print("data.pt not found, preparing data...")
    dataset = datasets.ImageFolder('photos')
    idx_to_class = {i: c for c, i in dataset.class_to_idx.items()}
    loader = DataLoader(dataset, collate_fn=lambda x: x[0])

    name_list, embedding_list = [], []

    for img, idx in loader:
        img = img.convert('RGB')
        face, prob = mtcnn(img, return_prob=True)
        if face is not None and prob > 0.92:
            # Assuming MTCNN returns a list of faces, take the first one
            face = face[0]  # Adjusted to ensure the tensor has the correct shape
            emb = resnet(face.unsqueeze(0).to(device))
            embedding_list.append(emb.detach())
            name_list.append(idx_to_class[idx])

    torch.save([embedding_list, name_list], 'data.pt')
    return embedding_list, name_list


# def main():
#     device = setup_device()
#     mtcnn, resnet = load_models(device)
#     embedding_list, name_list = prepare_data(device, mtcnn, resnet)
#     class_section = "CSC_4996_001"
#     cam = cv2.VideoCapture(0)

#     while True:
#         time.sleep(10)
#         ret, frame = cam.read()
#         if not ret:
#             print("Failed to grab frame, try again")
#             continue

#         try:
#             recognized_names = recognize_faces(frame, device, mtcnn, resnet, embedding_list, name_list)
#             if recognized_names:
#                 print(f"Recognized {len(recognized_names)} faces: {', '.join(recognized_names)}")
#                 update_attendance(recognized_names, class_section)
#             else:
#                 print("No recognized people in the frame.")
#         except Exception as e:
#             print(f"Error during detection or recognition: {e}")

# if __name__ == '__main__':
#     main()


