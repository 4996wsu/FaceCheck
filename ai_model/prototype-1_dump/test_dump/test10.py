import cv2
import torch
from torch.utils.data import DataLoader
from torchvision import datasets
from facenet_pytorch import MTCNN, InceptionResnetV1
from firebase_admin import storage
import io

import firebase_admin
from firebase_admin import credentials
import torch
import torchvision.transforms as transforms

from recognition import prepare_data,setup_device
#   -------------------------------------------------------------------------------------------------
import torch
import requests

if not firebase_admin._apps:
    cred_path = 'db_credentials.json'  # Ensure the credential file path is correct
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {'storageBucket': 'facecheck-93450.appspot.com'})

device=setup_device()
embedding_list1, name_list1 = torch.load('data.pt', map_location=device)
#print(embedding_list1)


embedding_list, name_list = torch.load('hi4718.pt', map_location=device)

print(embedding_list)


def download_file_combine(url, section):
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(section, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    
    print(f"File downloaded and saved as {section}")

download_file_combine('https://storage.googleapis.com/facecheck-93450.appspot.com/minhajAMjj.pt','hi4718.pt')