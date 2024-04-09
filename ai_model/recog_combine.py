import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from PIL import Image
import os
import glob
from torchvision.transforms import ToTensor

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Load the model and data
load_data = torch.load('CSC_4996_001_W_2024.pt', map_location=device)
embedding_list, name_list = load_data
embedding_list = [i.to(device) for i in embedding_list]

# Initialize the face detection and recognition models
mtcnn = MTCNN(keep_all=True, min_face_size=40, device=device)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

# Define the directory containing the images
test_dir = 'test_combine'

# Function to predict the face names from an image
def predict_face_names(img):
    # Detect faces
    boxes, _ = mtcnn.detect(img)
    recognized_names = []

    if boxes is not None:
        for box in boxes:
            # Crop the detected face
            face = img.crop(box)
            # Convert face to tensor
            face_tensor = ToTensor()(face).to(device)
            # Get the embedding of the face
            emb = resnet(face_tensor.unsqueeze(0))
            # Calculate distances
            dist_list = [torch.dist(emb, ebd).item() for ebd in embedding_list]
            # Find the minimum distance
            min_dist = min(dist_list)
            # Check if distance is less than threshold, it's a match
            if min_dist < 0.95:
                # Get the index of the minimum distance
                min_dist_idx = dist_list.index(min_dist)
                # Get the corresponding name
                recognized_name = name_list[min_dist_idx]
                print(f"Recognized {recognized_name} with distance {min_dist:.2f}")
                recognized_names.append(recognized_name)
            else:
                print(f"Unknown face with distance {min_dist:.2f}")
                recognized_names.append("Unknown")

    return recognized_names

# Iterate through the images in the directory and predict the face names
for image_path in glob.glob(os.path.join(test_dir, '*')):
    img = Image.open(image_path).convert('RGB')
    names = predict_face_names(img)
    if names:
        print(f"Recognized face names in {os.path.basename(image_path)}: {', '.join(names)}")
    else:
        print(f"No faces recognized in {os.path.basename(image_path)}.")

