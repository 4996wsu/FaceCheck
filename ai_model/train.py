import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms, models
import numpy as np
from PIL import Image
import os
import random
from facenet_pytorch import MTCNN
from tqdm import tqdm

class TripletFaceDataset(Dataset):
    def __init__(self, directory, transform=None):
        self.directory = directory
        self.transform = transform
        self.classes, self.class_to_idx = self._find_classes(directory)
        self.samples = self._make_dataset(directory, self.class_to_idx)
        self.mtcnn = MTCNN(keep_all=True, device='cuda' if torch.cuda.is_available() else 'cpu')
        self.triplets = self._generate_triplets()

    def _find_classes(self, dir):
        classes = [d.name for d in os.scandir(dir) if d.is_dir()]
        classes.sort()
        class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}
        return classes, class_to_idx

    def _make_dataset(self, directory, class_to_idx):
        samples = []
        for class_name in class_to_idx.keys():
            class_idx = class_to_idx[class_name]
            class_dir = os.path.join(directory, class_name)
            for root, _, fnames in os.walk(class_dir):
                for fname in fnames:
                    if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                        path = os.path.join(root, fname)
                        item = (path, class_idx)
                        samples.append(item)
        return samples

    def _generate_triplets(self):
        triplets = []
        for class_idx, class_name in enumerate(self.classes):
            class_samples = [s for s in self.samples if s[1] == class_idx]
            negative_samples = [s for s in self.samples if s[1] != class_idx]
            for anchor in class_samples:
                if len(class_samples) < 2 or len(negative_samples) == 0:
                    continue
                positive = random.choice([s for s in class_samples if s != anchor])
                negative = random.choice(negative_samples)
                triplets.append((anchor[0], positive[0], negative[0]))
        return triplets

    def __len__(self):
        return len(self.triplets)

    def __getitem__(self, idx):
        anchor_path, positive_path, negative_path = self.triplets[idx]
        anchor_img = self._load_image(anchor_path)
        positive_img = self._load_image(positive_path)
        negative_img = self._load_image(negative_path)

        return anchor_img, positive_img, negative_img

    def _load_image(self, path):
        img = Image.open(path).convert('RGB')
        # Detect face, extract ROI, and apply transformations if necessary
        img_cropped = self._extract_face(img)
        if self.transform:
            img_cropped = self.transform(img_cropped)
        return img_cropped

    def _extract_face(self, img):
        # Detect faces in the image
        boxes, _ = self.mtcnn.detect(img)
        if boxes is not None:
            # Assuming the first detected face is the subject
            box = boxes[0]
            img_cropped = img.crop(box)
            return img_cropped
        else:
            # If no face is detected, return the original image
            return img

def load_embedding_model(model_name='resnet50', embedding_dimension=128):
    if model_name == 'resnet50':
        model = models.resnet50(pretrained=True)
        model.fc = nn.Linear(model.fc.in_features, embedding_dimension)
    else:
        raise ValueError("Model not supported. Please use 'resnet50'.")
    return model

def train_with_triplet(model, dataloader, triplet_loss, optimizer, num_epochs=25, device=None):
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        progress_bar = tqdm(dataloader, total=len(dataloader), desc=f"Epoch {epoch+1}/{num_epochs}")

        for batch in progress_bar:
            (anchors, positives, negatives) = batch
            anchors, positives, negatives = anchors.to(device), positives.to(device), negatives.to(device)

            optimizer.zero_grad()

            anchor_embeddings = model(anchors)
            positive_embeddings = model(positives)
            negative_embeddings = model(negatives)

            loss = triplet_loss(anchor_embeddings, positive_embeddings, negative_embeddings)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            progress_bar.set_postfix({'loss': loss.item()})

        epoch_loss = running_loss / len(dataloader)
        print(f"Training Loss: {epoch_loss:.4f}")
    return model

def get_triplet_transforms():
    # No need for resizing or cropping as images are already 112x112 and faces are detected by MTCNN
    train_transforms = transforms.Compose([
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    validate_transforms = train_transforms  # Same transforms for both training and validation

    return {
        'train': train_transforms,
        'validate': validate_transforms
    }

def main_triplet():
    transforms = get_triplet_transforms()
    train_dataset = TripletFaceDataset(directory='dataset/train4', transform=transforms['train'])
    dataloader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=4, pin_memory=True)

    model = load_embedding_model(model_name='resnet50', embedding_dimension=128)
    model_path = 'triplet_model_1.0.pth'
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path))
        print("Loaded model weights.")

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)

    triplet_loss = nn.TripletMarginLoss(margin=1.0)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
    dataloaders = {'train': dataloader}

    trained_model = train_with_triplet(model, dataloaders['train'], triplet_loss, optimizer, num_epochs=25, device=device)

    torch.save(trained_model.state_dict(), model_path)
    print(f"Model updated and saved to '{model_path}'.")

if __name__ == '__main__':
    main_triplet()
