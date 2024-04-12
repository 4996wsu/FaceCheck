import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image
import os
import numpy as np

# Path to the saved model and dataset
model_path = 'trained_face_encoding_model_2.pt'
data_path = 'photos'

# Determine the device (CUDA if available)
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Initialize MTCNN and InceptionResnetV1 with the determined device
mtcnn = MTCNN(image_size=160, margin=0, keep_all=False, device=device)
resnet = InceptionResnetV1(pretrained=None).eval().to(device)

# Load the trained model
resnet.load_state_dict(torch.load(model_path, map_location=device))
resnet.classify = False  # Ensure the model is set to return embeddings

def extract_face_encodings(data_path):
    encodings = {}
    for person_name in os.listdir(data_path):
        person_path = os.path.join(data_path, person_name)
        if not os.path.isdir(person_path):
            continue
        for image_name in os.listdir(person_path):
            image_path = os.path.join(person_path, image_name)
            try:
                # Load image
                img = Image.open(image_path).convert('RGB')
                
                # Detect face
                face, prob = mtcnn(img, return_prob=True)
                if face is not None and prob > 0.9:
                    # Move the face tensor to the same device as the model
                    face = face.to(device)
                    
                    # Extract encoding
                    face_encoding = resnet(face.unsqueeze(0)).detach().cpu()
                    
                    # Save encoding
                    encodings[person_name] = face_encoding.numpy()
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
    return encodings

# Extract face encodings
face_encodings = extract_face_encodings(data_path)

# Example: Save the encodings to a file for later use
np.save('face_encodings.npy', face_encodings)

print("Face encodings extracted and saved.")
