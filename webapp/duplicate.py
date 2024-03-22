
def function():
    from database import get_doc

    student_doc= get_doc('student_doc') 
    classname= list(student_doc['students'].keys())
    print(classname)
class_id= 'CSC_4996_001_W_2024'
from database import download_file_combine, retrieve_class_embedding
if retrieve_class_embedding(class_id) == "NO ENCODING":
    print("NO ENCODING")

else:
    download_file_combine(retrieve_class_embedding(class_id), f'{class_id}.pt')

import torch
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
embedding_list, name_list = torch.load(f'{class_id}.pt', map_location=device)
def duplicate_faces(embedding_list, known_embeddings, name_list,name, threshold=1.2):
    # Choose the device based on availability
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Ensure embedding_list is on the correct device
    embedding_list = [emb.to(device) for emb in embedding_list]

    # Ensure known_embeddings is on the correct device
    known_embeddings = [known_emb.to(device) for known_emb in known_embeddings]
    from database import update_photo_status_batch
    recognized_names = []
    for emb in embedding_list:
        # Calculate distances to all known embeddings
        dist_list = [torch.dist(emb, known_emb).item() for known_emb in known_embeddings]

        # Find the closest known embedding
        min_dist = min(dist_list)
        min_dist_idx = dist_list.index(min_dist)

        # Check if the closest known embedding is within the threshold
        if min_dist < threshold:
            recognized_name = name_list[min_dist_idx]
        else:
            recognized_name = "Unknown"
        recognized_names.append(recognized_name)
        if recognized_name[0] != "Unknown":
            update_photo_status_batch(name,"Flagged")
            print("known")
        else:
            update_photo_status_batch(name,"Pending")
            print("Unknown")
    print(recognized_names)
