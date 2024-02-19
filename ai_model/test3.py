from facenet_pytorch import MTCNN
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os
import glob

# Initialize MTCNN for face detection
mtcnn = MTCNN(keep_all=True, device='cpu')

# Function Definitions
def load_model(model_path, embedding_dimension=128):
    model = models.resnet50(pretrained=False)
    model.fc = nn.Linear(model.fc.in_features, embedding_dimension)
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()
    return model

def get_transform():
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

def extract_face_encoding(model, image):
    transform = get_transform()
    image = transform(image).unsqueeze(0)  # Add batch dimension
    with torch.no_grad():
        encoding = model(image)
    return encoding

def load_reference_encodings(model, reference_dir):
    reference_encodings = {}
    for person_name in os.listdir(reference_dir):
        person_dir = os.path.join(reference_dir, person_name)
        file_list = glob.glob(os.path.join(person_dir, '*'))
        reference_image_paths = [file for file in file_list if file.endswith(('.jpg', '.jpeg', '.png'))]
        if reference_image_paths:
            reference_image_path = reference_image_paths[0]  # Consider using the first image as the reference
            reference_image = Image.open(reference_image_path).convert('RGB')
            reference_encoding = extract_face_encoding(model, reference_image)
            reference_encodings[person_name] = reference_encoding
    return reference_encodings

def predict_identity(model, test_image_path, reference_encodings, threshold=50):
    test_image = Image.open(test_image_path).convert('RGB')
    test_encoding = extract_face_encoding(model, test_image)
    
    closest_distance = float('inf')
    identity = None
    for person_name, reference_encoding in reference_encodings.items():
        distance = torch.norm(reference_encoding - test_encoding)
        if distance < closest_distance:
            closest_distance = distance
            identity = person_name
    
    if closest_distance < threshold:
        return identity
    else:
        return "Unknown"

# Main Execution
model_path = 'triplet_model_face_recognition.pth'
model = load_model(model_path)
reference_dir = 'dataset/data'  # Update this path to your reference images directory

# Load reference encodings
reference_encodings = load_reference_encodings(model, reference_dir)

# Predict Identity
test_image_path = 'dataset/exercise/face_1.png'  # Update this path to your test image
identity = predict_identity(model, test_image_path, reference_encodings)
print(f"Identity: {identity}")
