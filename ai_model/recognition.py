import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image
import cv2
import os
import time
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

# Assuming 'update_student_attendance', 'getDate', and 'getTime' are defined in 'database.py'
from database import update_student_attendance, getDate, getTime, retrieve_names_from_class

def setup_device():
    return torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def load_models(device):
    mtcnn = MTCNN(keep_all=True, device=device)
    resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)
    return mtcnn, resnet

def prepare_data(device, section):
    if os.path.exists(f'{section}.pt'):
        return torch.load(f'{section}.pt', map_location=device)
    return None

#test function
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

def recognize_faces(frame, device, mtcnn, resnet, embedding_list, name_list):
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    boxes, _ = mtcnn.detect(img)
    faces = mtcnn(img)
    recognized_names = []

    if faces is not None:
        for face in faces:
            emb = resnet(face.to(device).unsqueeze(0))
            dist_list = [torch.dist(emb, ebd).item() for ebd in embedding_list]
            min_dist = min(dist_list)
            if min_dist < 0.90:
                min_dist_idx = dist_list.index(min_dist)
                recognized_names.append(name_list[min_dist_idx])
            else:
                recognized_names.append("Unknown")

    return recognized_names

def update_attendance(recognized_names, class_section):
    date = getDate()
    time = getTime()
    
    # Mark present students
    for name in recognized_names:
        update_student_attendance(class_section, name, True, date, time)
        
    # Mark absent students (Removes present students from a list of all students first)
    students = retrieve_names_from_class()
    for name in students[:]:
        if name in recognized_names:
            students.remove(name)
    for name in students:
        update_student_attendance(class_section, name, False, date, time)
        

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


