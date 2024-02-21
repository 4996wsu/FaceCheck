import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image
import cv2
import os
import time
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

from database import update_student_attendance

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

def prepare_data():
    mtcnn = MTCNN(image_size=240, margin=0, keep_all=False, min_face_size=40, device=device)
    resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

    dataset = datasets.ImageFolder('photos')
    idx_to_class = {i: c for c, i in dataset.class_to_idx.items()}
    loader = DataLoader(dataset, collate_fn=lambda x: x[0])

    name_list, embedding_list = [], []

    for img, idx in loader:
        img = img.convert('RGB')
        face, prob = mtcnn(img, return_prob=True)
        if face is not None and prob > 0.92:
            emb = resnet(face.unsqueeze(0).to(device))
            embedding_list.append(emb.detach())
            name_list.append(idx_to_class[idx])

    torch.save([embedding_list, name_list], 'data.pt')

if not os.path.exists('data.pt'):
    print("data.pt not found, preparing data...")
    prepare_data()

load_data = torch.load('data.pt', map_location=device)
embedding_list, name_list = [emb.to(device) for emb in load_data[0]], load_data[1]
class_section="CSC_4996_001"
mtcnn = MTCNN(keep_all=True, device=device)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

cam = cv2.VideoCapture(0)

while True:
    time.sleep(10)
    ret, frame = cam.read()
    if not ret:
        print("Failed to grab frame, try again")
        continue

    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    try:
        boxes, _ = mtcnn.detect(img)
        faces = mtcnn(img)
        recognized_names = []

        if faces is not None:
            for face in faces:
                try:
                    # Directly use the tensor for InceptionResnetV1
                    emb = resnet(face.to(device).unsqueeze(0))

                    dist_list = [torch.dist(emb, ebd).item() for ebd in embedding_list]
                    min_dist = min(dist_list)
                    if min_dist < 0.90:
                        min_dist_idx = dist_list.index(min_dist)
                        recognized_names.append(name_list[min_dist_idx])
                    else:
                        recognized_names.append("Unknown")
                except Exception as e:
                    print(f"Error processing face: {e}")
                    recognized_names.append("Unknown")

            if recognized_names:
                print(f"Recognized {len(recognized_names)} faces: {', '.join(recognized_names)}")
            else:
                print("No recognized people in the frame.")
                
        for name in recognized_names:
            update_student_attendance(class_section, name, '02_08_2024', '17_40_00', True)
    except Exception as e:
        print(f"Error during detection or recognition: {e}")
        continue  # Continue to the next frame
