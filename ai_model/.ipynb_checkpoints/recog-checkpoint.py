import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms, models
import numpy as np
from PIL import Image
import os
import random


# 1. Dataset Preparation for Triplet Loss

class TripletFaceDataset(Dataset):
    def __init__(self, directory, transform=None):
        
        #Initialize dataset for triplet loss.
        #directory: Dataset directory 'dataset/train'
        #transform: Transforms for data augmentation and preprocessing
        self.directory = directory
        self.transform = transform
        self.classes, self.class_to_idx = self._find_classes(directory)
        self.samples = self._make_dataset(directory, self.class_to_idx)
        self.triplets = self._generate_triplets()

    def _find_classes(self, dir):
        
        #Finds class folders in a dataset and assigns indices.
        # dir is targeting classes inside the dataset   
        classes = [d.name for d in os.scandir(dir) if d.is_dir()]
        classes.sort()  # Ensuring consistent order
        class_to_idx = {cls_name: i for i, cls_name in enumerate(classes)}
        return classes, class_to_idx
# make dataset code is partially from https://pytorch.org/vision/0.9/_modules/torchvision/datasets/folder.html 
    def _make_dataset(self, directory, class_to_idx):
        samples = []
        for class_name in class_to_idx.keys():
            class_index = class_to_idx[class_name]
            class_dir = os.path.join(directory, class_name)
            for root, _, fnames in os.walk(class_dir):
                for fname in fnames:
                    if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                        path = os.path.join(root, fname)
                        item = (path, class_index)
                        samples.append(item)
        return samples

    def _generate_triplets(self):
        """
        Generates a list of triplets for training.
        Each triplet contains paths to an anchor, a positive, and a negative image.
        """
        triplets = []
        for class_index, class_name in enumerate(self.classes):
            class_samples = [s for s in self.samples if s[1] == class_index]
            negative_samples = [s for s in self.samples if s[1] != class_index]
            for anchor in class_samples:
                if len(class_samples) < 2 or len(negative_samples) == 0:
                    continue  # Not enough samples for triplet
                positive = random.choice([s for s in class_samples if s != anchor])
                negative = random.choice(negative_samples)
                triplets.append((anchor[0], positive[0], negative[0]))
        return triplets

    def __len__(self):
        """
        Returns the total number of triplets.
        """
        return len(self.triplets)

    def __getitem__(self, idx):
        """
        Fetches a triplet (anchor, positive, negative) by idx.
        Each image is opened, optionally transformed, and returned.
        """
        anchor_path, positive_path, negative_path = self.triplets[idx]
        anchor_img = Image.open(anchor_path).convert('RGB')
        positive_img = Image.open(positive_path).convert('RGB')
        negative_img = Image.open(negative_path).convert('RGB')

        if self.transform:
            anchor_img = self.transform(anchor_img)
            positive_img = self.transform(positive_img)
            negative_img = self.transform(negative_img)

        return anchor_img, positive_img, negative_img


# 2. Model Preparation for Embedding
import torchvision.models as models
import torch.nn as nn

import torchvision.models as models
import torch.nn as nn
from torchvision.models.resnet import ResNet50_Weights  # Import the Weights enum for ResNet50

def load_embedding_model(model_name='resnet50', embedding_dimension=128):
    """
    Load and modify a pre-trained model for embedding extraction.
    - model_name: Pre-trained model name.
    - embedding_dimension: Size of the output embedding vector.
    """
    if model_name == 'resnet50':
        # Use the weights enum to specify pre-trained weights
        weights = ResNet50_Weights.IMAGENET1K_V1  # or use ResNet50_Weights.DEFAULT for the most up-to-date
        model = models.resnet50(weights=weights)
        # Replace the last fully connected layer with an embedding layer
        model.fc = nn.Linear(model.fc.in_features, embedding_dimension)
    else:
        raise ValueError("Model not supported. Please use 'resnet50'.")

    return model



# 3. Training with Triplet Loss
from tqdm import tqdm

def train_with_triplet_loss(model, dataloader, triplet_loss, optimizer, num_epochs=25, device=None):
    """
    Train the model using triplet loss.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model.to(device)

    for epoch in range(num_epochs):
        model.train()  # Ensure the model is in training mode

        running_loss = 0.0
        progress_bar = tqdm(dataloader, total=len(dataloader), desc=f"Epoch {epoch+1}/{num_epochs}")

        for batch in progress_bar:
            # Adjusted unpacking step here
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

            # Update the progress bar with the current loss
            progress_bar.set_postfix({'loss': loss.item()})

        epoch_loss = running_loss / len(dataloader)
        print(f"Training Loss: {epoch_loss:.4f}")

    # Return the model after training
    return model


# 4. Data Augmentation and Normalization for Triplet Loss
from torchvision import transforms

def get_triplet_transforms():
    """
    Returns the transformations to apply for triplet training.
    """
    train_transforms = transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    validate_transforms = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    return {
        'train': train_transforms,
        'validate': validate_transforms
    }


def main_triplet():
    # Setup transformations, dataset, and DataLoader for triplets
    transforms = get_triplet_transforms()
    train_dataset = TripletFaceDataset(directory='/content/drive/MyDrive/dataset/train', transform=transforms['train'])
    dataloader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=4, pin_memory=True)

    # Load the model prepared for embedding
    model = load_embedding_model(model_name='resnet50', embedding_dimension=128)

    # Load model state from .pth file if it exists
    model_path = 'triplet_model_face_recognition.pth'
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path))
        print("Loaded model weights from 'triplet_model_face_recognition.pth'.")

    # Move the model to GPU if available
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)

    # Define triplet loss and optimizer
    triplet_loss = nn.TripletMarginLoss(margin=1.0)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.001, momentum=0.9)

    # Dictionary to hold dataloaders for training
    dataloaders = {'train': dataloader}

    # Train the model using triplet loss
    trained_model = train_with_triplet_loss(model, dataloaders['train'], triplet_loss, optimizer, num_epochs=25, device=device)

    # Save the updated model
    torch.save(trained_model.state_dict(), model_path)
    print(f"Model updated and saved to '{model_path}'.")




if __name__ == '__main__':
    main_triplet()

