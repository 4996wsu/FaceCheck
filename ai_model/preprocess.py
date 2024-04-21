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
# Path to your Firebase service account JSON file
cred_path = 'db_credentials.json'

# Initialize the Firebase Admin SDK
#cred = credentials.Certificate(cred_path)
#firebase_admin.initialize_app(cred, {'storageBucket': 'facecheck-93450.appspot.com'})


# Function to detect and crop the face from an image to get a better face embedding
def detect_and_crop_face(image_path, device='cpu', min_face_size=20, thresholds=[0.6, 0.7, 0.7], factor=0.709):
    # Load the MTCNN face detector
    mtcnn = MTCNN(keep_all=True, device=device, min_face_size=min_face_size, thresholds=thresholds, factor=factor)
    #this will read the image from the path. adn the path will be the link of the image in the firebase
    frame = cv2.imread(image_path)
    # Check if the frame is empty
    if frame is None:
        raise FileNotFoundError(f"The specified image_path does not exist or is not accessible: {image_path}")
    # Convert the frame from BGR to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Detect faces in the frame
    faces, _ = mtcnn.detect(frame_rgb)
    
    # If a face is detected and only one face is in the frame, then crop the face
    if faces is not None and len(faces) == 1:
        # Get the coordinates of the face
        face = faces[0]
        # Convert the coordinates to integers, x1, y1, x2, y2 are the coordinates of the bounding box
        x1, y1, x2, y2 = [int(coord) for coord in face]
        # Ensure coordinates are within image bounds
        # Ensure that x1 and y1 are not less than 0. If they are, set them to 0.
        x1, y1 = max(0, x1), max(0, y1)

        # Ensure that x2 does not exceed the width of the frame (frame_rgb.shape[1]) and y2 does not exceed the height of the frame (frame_rgb.shape[0]).
        # If they do, set x2 to the frame width and y2 to the frame height.
        x2, y2 = min(frame_rgb.shape[1], x2), min(frame_rgb.shape[0], y2)
        # Ensure the crop dimensions are valid
        if x2 <= x1 or y2 <= y1:
            return None  # Invalid crop dimensions
        # Crop the face from the frame
        cropped_face = frame_rgb[y1:y2, x1:x2]
    
        # Check if the cropped face is empty
        if cropped_face.size == 0:
            return None  # Cropped face is empty
        # Convert the cropped face from RGB to BGR
        cropped_face_bgr = cv2.cvtColor(cropped_face, cv2.COLOR_RGB2BGR)
        # Return the cropped face
        return cropped_face_bgr
    else:
        # No face detected or multiple faces detected
        return None

device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')


# Function to extract the face embeddings of the cropped face
def face_encode(cropped_face, device):
    # Initialize the list to store the embeddings
    embedding_list = [] 
    # Load the InceptionResnetV1 model
    resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

    # Define transformations For the face image to be compatible with the model
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
    # Append the embedding to the list of embeddings
    embedding_list.append(emb.detach())
    # Return the list of embeddings
    return embedding_list


def make_pt_file(embedding_list, name_list):
    # Save the file to an in-memory file-like object
    file_name = f'{name_list[0]}.pt'
    
    #Create a buffer in memory using BytesIO
    buffer = io.BytesIO()
    # Save the embeddings and names to the buffer
    torch.save([embedding_list, name_list], buffer)
    # Reset the buffer position to the start of the buffer
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
    ## Return the URL
    return url


########################################################################################
#####################################TESTING############################################
########################################################################################

#cropped_face = detect_and_crop_face('photos/hc9082/hc9082.jpg')
#name_list=['hc9082']

#if cropped_face is not None:
    #embedding_list=face_encode(cropped_face, device)
    #make_pt_file(embedding_list, name_list)
    cv2.imwrite('cropped_face.jpg', cropped_face)
#else:
    print("No face detected.")
