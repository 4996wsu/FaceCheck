import torch
from facenet_pytorch import InceptionResnetV1, MTCNN
from PIL import Image
from torchvision import datasets
from torch.utils.data import DataLoader
import numpy as np
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Load the data
load_data = torch.load('CSC_4996_001_W_2024.pt', map_location=device)
embedding_list, name_list = [emb.to(device) for emb in load_data[0]], load_data[1]

# Load the test dataset
test_dataset = datasets.ImageFolder('test_data')
test_loader = DataLoader(test_dataset, collate_fn=lambda x: x[0])

# Initialize the face detection and recognition models
mtcnn = MTCNN(keep_all=True, device=device)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

correct_predictions = 0
total_predictions = 0

# Iterate over the test dataset
for img, idx in test_loader:
    img = img.convert('RGB')
    boxes, probs = mtcnn.detect(img)
    faces = mtcnn(img)
    
    if faces is not None:
        for face in faces:
            emb = resnet(face.to(device).unsqueeze(0))
            dist_list = [torch.dist(emb, ebd).item() for ebd in embedding_list]
            min_dist = min(dist_list)
            min_dist_idx = dist_list.index(min_dist)
            
            predicted_name = name_list[min_dist_idx] if min_dist < 0.93 else "Unknown"
            actual_name = test_dataset.classes[idx]
            
            if predicted_name == actual_name:
                correct_predictions += 1
                print(f"Correct prediction:{actual_name} {predicted_name}")
            else:
                print(f"Incorrect prediction:{actual_name} {predicted_name}")
            total_predictions += 1

# Calculate accuracy
print(correct_predictions, total_predictions)
accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
print(f'Accuracy: {accuracy:.4f}')
