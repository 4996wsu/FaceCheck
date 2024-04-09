from database import download_file_combine, retrieve_class_embedding
import torch
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')



#this is the function that will be used in the webapp
#this function will be used to compare the face embeddings of the new photo to the existing embeddings
def duplicate_faces(embedding_list, known_embeddings, name_list,name, threshold=0.9):
    # Choose the device based on availability
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Ensure embedding_list is on the correct device
    embedding_list = [emb.to(device) for emb in embedding_list]

    # Ensure known_embeddings is on the correct device
    known_embeddings = [known_emb.to(device) for known_emb in known_embeddings]
    from database import update_photo_status_batch,check_picture_status
    recognized_names = []
    # Iterate through the embeddings of the new photo
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
        # Append the recognized name to the list
        recognized_names.append(recognized_name)
        

        #if the recognized name is not unknown and is not the same as the name of the photo then flag the photo
        if recognized_names[0] != "Unknown" and recognized_names[0] != name:
            if (check_picture_status(name)==False):
                return 'flagged_before'
            else:
                update_photo_status_batch(name,"Flagged")
                update_photo_status_batch(recognized_names[0],"Flagged")
                print(recognized_names[0])
                print("HERE")
                return 'flagged'
        #else put it as pending
        else:
            if (check_picture_status(name)==False):
                return 'flagged_before'
            #can be changed to pending only if the photo is not flagged
            elif (check_picture_status(name)==True):
                update_photo_status_batch(name,"Pending")
                return 'unknown'
           
            
