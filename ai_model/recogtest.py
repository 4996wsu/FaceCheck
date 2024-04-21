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

# Initialize variables for calculating accuracy
correct_predictions = 0
total_predictions = 0

# Iterate over the test dataset
for img, idx in test_loader:
    # Convert image to RGB format
    img = img.convert('RGB')
    # Detect faces in the image
    #boxs has the coordinates of the faces in the image
    #prob is the probability of the face being a face
    boxes, probs = mtcnn.detect(img)

    faces = mtcnn(img)
    # If faces are detected, extract the face embeddings
    if faces is not None:
        # Iterate over the faces
        for face in faces:
            # Calculate the face embeddings
            emb = resnet(face.to(device).unsqueeze(0))
            # Calculate the distance between the face embeddings of the test image and the embeddings of the training images
            dist_list = [torch.dist(emb, ebd).item() for ebd in embedding_list]
            # Find the minimum distance
            min_dist = min(dist_list)
            # Find the index of the minimum distance
            min_dist_idx = dist_list.index(min_dist)

            # Predict the name of the person in the test image based on the minimum distance
            # If the minimum distance is less than 0.93, predict the name of the person
            predicted_name = name_list[min_dist_idx] if min_dist < 0.93 else "Unknown"
            # Get the actual name of the person in the test image
            actual_name = test_dataset.classes[idx]
            # Compare the predicted name with the actual name
            if predicted_name == actual_name:
                # Increment the number of correct predictions
                correct_predictions += 1
                # Print the prediction result
                print(f"Correct prediction:{actual_name} {predicted_name}")
            else:
                # Print the prediction result
                print(f"Incorrect prediction:{actual_name} {predicted_name}")
            # Increment the total number of predictions
            total_predictions += 1


# Calculate accuracy
print(correct_predictions, total_predictions)
#accuracy is the number of correct predictions divided by the total number of predictions
accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
# Print the accuracy
print(f'Accuracy: {accuracy:.4f}')
