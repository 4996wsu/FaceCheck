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
    print(encoding)
    return encoding

def evaluate_accuracy(model, test_dir):
    correct_matches = 0
    total_images = 0

    for person_name in os.listdir(test_dir):
        person_dir = os.path.join(test_dir, person_name)
        print(person_dir)
        #reference_image_path = os.path.join('dataset/data', person_name, person_name + '.jpg')
        

# Get all files that ends with .jpg, .jpeg, .png
        file_list = glob.glob(os.path.join('dataset/data', person_name, person_name + '.*'))

# Filter out the list for files ending with the desired extensions
        reference_image_paths = [file for file in file_list if file.endswith(('.jpg', '.jpeg', '.png'))]
        #reference_image = Image.open(reference_image_paths).convert('RGB')
        #reference_encoding = extract_face_encoding(model, reference_image)
        # Get the first image from the list
        reference_image_path = reference_image_paths[0] if reference_image_paths else None

        if reference_image_path:
            reference_image = Image.open(reference_image_path).convert('RGB')
            reference_encoding = extract_face_encoding(model, reference_image)
        else:
            print(f"No reference image found for {person_name}")

        for image_name in os.listdir(person_dir):
            total_images += 1
            image_path = os.path.join(person_dir, image_name)
            test_image = Image.open(image_path).convert('RGB')
            test_encoding = extract_face_encoding(model, test_image)
            
            distance = torch.norm(reference_encoding - test_encoding)
            if distance < threshold:  # Assuming you have defined a threshold
                correct_matches += 1
    
    accuracy = correct_matches / total_images if total_images > 0 else 0
    return accuracy

# Main Execution
model_path = 'triplet_model_face_recognition.pth'
model = load_model(model_path)
threshold = 2 # Adjust this based on your validation set or prior experiments

test_dir = 'test_data'
accuracy = evaluate_accuracy(model, test_dir)
print(f"Model Accuracy: {accuracy:.2f}")
