import cv2
import torch
from torch.utils.data import DataLoader
from torchvision import datasets
from facenet_pytorch import MTCNN, InceptionResnetV1
from firebase_admin import storage
import io

import firebase_admin
from firebase_admin import credentials

# Path to your Firebase service account JSON file
cred_path = 'db_credentials.json'

# Initialize the Firebase Admin SDK
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred, {'storageBucket': 'facecheck-93450.appspot.com'})

def detect_and_crop_face(image_path, device='cpu', min_face_size=20, thresholds=[0.6, 0.7, 0.7], factor=0.709):
    mtcnn = MTCNN(keep_all=True, device=device, min_face_size=min_face_size, thresholds=thresholds, factor=factor)
    frame = cv2.imread(image_path)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces, _ = mtcnn.detect(frame_rgb)
    
    if  len(faces) == 1:
        face = faces[0]
        x1, y1, x2, y2 = [int(coord) for coord in face]
        cropped_face = frame_rgb[y1:y2, x1:x2]
        cropped_face_bgr = cv2.cvtColor(cropped_face, cv2.COLOR_RGB2BGR)
        return cropped_face_bgr
    else:
        return None
    

device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')

import torch
import torchvision.transforms as transforms

def face_encode(cropped_face, device):
    embedding_list = [] 
    resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

    # Define transformations
    preprocess = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(160),  # Resize the image to the size expected by the model
        transforms.ToTensor(),  # Convert the image to a PyTorch tensor
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])  # Normalize
    ])

    # Apply the transformations
    cropped_face_tensor = preprocess(cropped_face).unsqueeze(0)  # Add batch dimension

    # Get the embedding
    emb = resnet(cropped_face_tensor.to(device))
    embedding_list.append(emb.detach())

    return embedding_list


def make_pt_file(embedding_list, name_list):
    # Save the file to an in-memory file-like object
    file_name = f'{name_list[0]}.pt'
    buffer = io.BytesIO()
    torch.save([embedding_list, name_list], buffer)
    buffer.seek(0)

    # Get a reference to the storage service
    bucket = storage.bucket()

    # Create a new blob and upload the file's content.
    blob = bucket.blob(file_name)
    blob.upload_from_file(buffer)

    # Make the blob publicly viewable.
    blob.make_public()

    # Get the URL of the blob
    url = blob.public_url
    print(url)
    return url
    
cropped_face = detect_and_crop_face('photos/hc9082/hc9082.jpg')
name_list=['hc9082']

if cropped_face is not None:
    embedding_list=face_encode(cropped_face, device)
    make_pt_file(embedding_list, name_list)
    cv2.imwrite('cropped_face.jpg', cropped_face)
else:
    print("No face detected.")
