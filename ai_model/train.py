import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms, models
import numpy as np
from PIL import Image
import os
import random
from torchvision import transforms
import torchvision.models as models
import torch.nn as nn
from torchvision.models.resnet import ResNet50_Weights
from tqdm import tqdm
class TripletFaceDataset(Dataset):
    def __init__(self, directory, transform=None):
        self.directory = directory
        self.transform = transform
        self.classes, self.class_to_idx = self._find_classes(directory)
        self.samples = self._make_dataset(directory, self.class_to_idx)
        self.triplets = self._generate_triplets()

    def _find_classes(self, dir):

        classes = [d.name for d in os.scandir(dir) if d.is_dir()]
        classes.sort()
        class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}
        return classes, class_to_idx
# make dataset code is partially from https://pytorch.org/vision/0.9/_modules/torchvision/datasets/folder.html
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
        anchor_img = Image.open(anchor_path).convert('RGB')
        positive_img = Image.open(positive_path).convert('RGB')
        negative_img = Image.open(negative_path).convert('RGB')

        if self.transform:
            anchor_img = self.transform(anchor_img)
            positive_img = self.transform(positive_img)
            negative_img = self.transform(negative_img)

        return anchor_img, positive_img, negative_img




def load_embedding_model(model_name='resnet50', embedding_dimension=128):
    if model_name == 'resnet50':
        weights = ResNet50_Weights.IMAGENET1K_V1
        model = models.resnet50(weights=weights)
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
    # Adjust the crop size and resize parameters for 112x112 images
    train_transforms = transforms.Compose([
        transforms.RandomResizedCrop(112),  # Crop randomly then resize to 112x112
        transforms.RandomHorizontalFlip(),  # Random horizontal flipping
        transforms.ToTensor(),  # Convert to tensor
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # Normalize
    ])

    validate_transforms = transforms.Compose([
        transforms.Resize(128),  # Resize to slightly larger than target to maintain aspect ratio
        transforms.CenterCrop(112),  # Center crop to 112x112
        transforms.ToTensor(),  # Convert to tensor
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # Normalize
    ])

    return {
        'train': train_transforms,
        'validate': validate_transforms
    }


def main_triplet():

    transforms = get_triplet_transforms()
    train_dataset = TripletFaceDataset(directory='/content/drive/MyDrive/dataset/train4', transform=transforms['train'])
    dataloader = DataLoader(train_dataset, batch_size=128, shuffle=True, num_workers=4, pin_memory=True)


    model = load_embedding_model(model_name='resnet50', embedding_dimension=128)

    model_path = 'triplet_model_1.0.pth'
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path))
        print("Loaded model weights from 'triplet_model_face_recognition_128.pth'.")


    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)

#https://pytorch.org/docs/stable/optim.html
    triplet_loss = nn.TripletMarginLoss(margin=1.0)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
    dataloaders = {'train': dataloader}

    # Train the model using triplet loss
    trained_model = train_with_triplet(model, dataloaders['train'], triplet_loss, optimizer, num_epochs=25, device=device)

    # Save the updated model
    torch.save(trained_model.state_dict(), model_path)
    print(f"Model updated and saved to '{model_path}'.")




if __name__ == '__main__':
    main_triplet()

