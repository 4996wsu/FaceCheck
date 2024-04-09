import torch
import torch.nn as nn
import timm
from facenet_pytorch import MTCNN
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import cv2
import os
import time
from PIL import Image

class CustomEfficientNet(nn.Module):
    def __init__(self, num_output_features=512):
        super(CustomEfficientNet, self).__init__()
        self.base_model = timm.create_model('tf_efficientnet_b7_ns', pretrained=True)  # If warning, adjust model name
        self.base_model.classifier = nn.Identity()
        self.classifier = nn.Linear(self.base_model.num_features, num_output_features)

    def forward(self, x):
        x = self.base_model(x)
        x = self.classifier(x)
        return x

def load_models(device):
    mtcnn = MTCNN(keep_all=True, device=device)
    efficientnet = CustomEfficientNet().to(device).eval()
    return mtcnn, efficientnet

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mtcnn, efficientnet = load_models(device)

dataset = datasets.ImageFolder('photos')
idx_to_class = {i: c for c, i in dataset.class_to_idx.items()}
loader = DataLoader(dataset, collate_fn=lambda x: x[0])

name_list = []
embedding_list = []

for img, idx in loader:
    img_cropped, prob = mtcnn(img, return_prob=True)
    if img_cropped is not None and prob > 0.92:
        img_cropped = img_cropped.squeeze()  # Adjust tensor shape if needed
        img_cropped_pil = transforms.ToPILImage()(img_cropped)  # Convert to PIL Image
        img_cropped_pil = transforms.Resize((224, 224), antialias=True)(img_cropped_pil)
        img_cropped_tensor = transforms.ToTensor()(img_cropped_pil)
        img_cropped_tensor = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])(img_cropped_tensor)
        img_cropped_tensor = img_cropped_tensor.to(device)
        emb = efficientnet(img_cropped_tensor.unsqueeze(0))
        embedding_list.append(emb.detach().cpu().flatten())
        name_list.append(idx_to_class[idx])

data = [embedding_list, name_list]
torch.save(data, 'data.pt')  # Save embeddings and names

# Webcam face recognition code remains unchanged
# Ensure to use the fixed approach for image preprocessing after face detection


# Webcam face recognition
cam = cv2.VideoCapture(0)

while True:
    ret, frame = cam.read()
    if not ret:
        print("Failed to grab frame, try again")
        break

    img = Image.fromarray(frame)
    img_cropped_list, prob_list = mtcnn(img, return_prob=True)

    if img_cropped_list is not None:
        boxes, _ = mtcnn.detect(img)

        for i, prob in enumerate(prob_list):
            if prob > 0.90:
                img_cropped = img_cropped_list[i].to(device)
                emb = efficientnet(img_cropped.unsqueeze(0)).detach().cpu().flatten()

                dist_list = []
                for emb_db in embedding_list:
                    dist = torch.dist(emb, emb_db).item()
                    dist_list.append(dist)

                min_dist = min(dist_list)
                min_dist_idx = dist_list.index(min_dist)
                name = name_list[min_dist_idx]

                box = boxes[i]
                frame = cv2.putText(frame, name + ' ' + str(min_dist), (int(box[0]), int(box[1])), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1, cv2.LINE_AA)
                frame = cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (255, 0, 0), 2)

    cv2.imshow("IMG", frame)

    k = cv2.waitKey(1)
    if k % 256 == 27:  # ESC key
        print('Esc pressed, closing...')
        break
    elif k % 256 == 32:  # Space key to save image
        print('Enter your name:')
        name = input()

        # Create directory if not exists
        if not os.path.exists('photos/' + name):
            os.makedirs('photos/' + name)

        img_name = "photos/{}/{}.jpg".format(name, int(time.time()))
        cv2.imwrite(img_name, frame)
        print("Saved: {}".format(img_name))

cam.release()
cv2.destroyAllWindows()
