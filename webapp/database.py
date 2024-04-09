#   -------------------------------------------------------------------------------------------------
#
#   This file handles all the database functions involving Firebase for the WEB APP.
#
#   -------------------------------------------------------------------------------------------------

import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.cloud.firestore_v1.base_query import FieldFilter, Or
from pathlib import Path
import tempfile
import cv2
from datetime import datetime
from preprocess import detect_and_crop_face, face_encode, make_pt_file
import torch
import requests
from io import BytesIO
# from preprocess import encode_face


#  Connect to firebase db
cred_fp = str(Path.cwd()) + "\db_credentials.json"
cred = credentials.Certificate(cred_fp)
firebase_admin.initialize_app(cred, {'storageBucket': 'facecheck-93450.appspot.com'})

#  Other common variables
db = firestore.client()
collectionName = "infoCollection"
class_doc = "class_doc"
student_doc = "student_doc"
user_doc = "user_doc"
professor_doc = "professor_doc"


#  ------------------------------  MAIN FUNCTIONALITY  ------------------------------
#  Retrieve all docs in collection
def get_all_docs():
    docs = (
        db.collection(collectionName)
        .stream()
    )
    
    # Iterate over documents and store their IDs and data into a list
    doc_list = []
    for doc in docs:
        doc_data = doc.to_dict()
        doc_data['id'] = doc.id
        doc_data['data'] = doc._data
        doc_list.append(doc_data)
        
    # Print all documents in the list
    for doc_data in doc_list:
        print(f"Document ID: {doc_data['id']}")
        print(f"Document Data: {doc_data['data']}")
        print()

#  Retrieve document from database and return as a dictionary
def get_doc(doc_id):
    doc_ref = db.collection(collectionName).document(doc_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        print(f"Document {doc_id} not found in {collectionName}.")
        return None
    
    
#  Recursively search dictionary
def lookup(key, data):
    if key in data:
        return data[key]
    for value in data.values():
        if isinstance(value, dict):
            return lookup(key, value)
    return None


#  Get current date and time
def getDate():
    now = datetime.now()
    return now.strftime("%m_%d_%Y")

def getTime():
    now = datetime.now()
    return now.strftime("%H_%M_%S")
    
       
#  Update existing document
def update_doc(doc_id, key, value):
    doc_ref = db.collection(collectionName).document(doc_id)
    doc_ref.update({
        key: value
    })

#  Add new class section
def add_class(section, prof):
    class_dict = get_doc(class_doc)
    
    if lookup(section, class_dict) != None:
        print("Error: Cannot add class '" + section + "' because the class already exists.")
    else:
        key = 'classes.' + section + '.professor'
        update_doc(class_doc, key, prof)
        print("Class '" + section + "' successfully added.")
    
#  Add new student to **DATABASE**
def add_student(accessid, fname, lname, role = "student"):
    user_dict = get_doc(user_doc)
    
    if lookup(accessid, user_dict) != None:
        print("Error: Cannot add user '" + accessid + "' because the user already exists.")
    else:
        # Determine if the user should receive the professor role
        prof_dict = get_doc(professor_doc)
        if lookup(accessid, prof_dict) != None:
            role = "professor"
        
        # Add student to database
        key = 'users.' + accessid + '.fname'
        update_doc(user_doc, key, fname)
        key = 'users.' + accessid + '.lname'
        update_doc(user_doc, key, lname)
        key = 'users.' + accessid + '.picture'
        update_doc(user_doc, key, "NO PHOTO")
        key = 'users.' + accessid + '.encoding'
        update_doc(user_doc, key, "NO ENCODING")        
        key = 'users.' + accessid + '.role'
        update_doc(user_doc, key, role)
        log_arr = [getTime(), "Created account"]
        key = 'users.' + accessid + '.audit_log.' + getDate()
        update_doc(user_doc, key, log_arr)
        
        print("Student '" + accessid + "' successfully added.")
        
#  Add new student to **CLASS**
def add_student_to_class(section, accessid):
    student_dict = get_doc(student_doc)
    user_dict = get_doc(user_doc)
    
    if lookup(accessid, student_dict['students'][section]) != None:
        print("Error: Cannot add user '" + accessid + "' because the user is already in " + section + ".")
    elif lookup(accessid, user_dict) == None:
        print("Error: Cannot add user '" + accessid + "' because the user does not exist.")
    else:
        key = 'students.' + section + '.' + accessid + '.attendance.00_00_0000.00_00_00'
        update_doc(student_doc, key, True)
        classKey = 'classes.' + section + '.encoding_update'
        update_doc(class_doc, classKey, True)
        
        print("Student '" + accessid + "' successfully added to " + section + ".")
   
    
#  ------------------------------  SHORTCUT FUNCTIONS  ------------------------------
#  Update student attendance
def update_student_attendance(section, name, value, date = getDate(), time = getTime()):
    student_dict = get_doc(student_doc)
    
    if lookup(name, student_dict) == None:
        print("Error: Cannot update attendance for '" + name + "' because the user does not exist.")
    else:
        key = 'students.' + section + '.' + name + '.attendance.' + date + '.' + time
        update_doc(student_doc, key, value)
        print("Student '" + name + "' marked as present on " + date + " at " + time + ".")

#  Update student photo
def update_student_photo(name, file):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    bucket = storage.bucket()
    imageBlob = bucket.blob(name + "_photo")
    name_list = [name]
    from duplicate import duplicate_faces
    class_id= 'CSC_4996_001_W_2024'
    if retrieve_class_embedding(class_id) != "NO ENCODING":
        download_file_combine(retrieve_class_embedding(class_id), f'{class_id}.pt')
    else:
        combine_pt_files(class_id)
    emb, names = torch.load(f'{class_id}.pt', map_location='cpu')
# Move loaded embeddings to the same device as your current embeddings
    emb = [e.to(device) for e in emb]
    # Crop student photo & upload encoding
    cropped_image = detect_and_crop_face(file)
    if cropped_image is not None:
        # Save cropped photo to temporary location and upload
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            cv2.imwrite(temp_file.name, cropped_image)
            imageBlob.upload_from_filename(temp_file.name)

        embedding_list = face_encode(cropped_image, device=device)
# If face_encode returns a single tensor, make sure it's on the right device
        embedding_list = [emb.to(device) for emb in embedding_list]
        
            
        embedding_link = make_pt_file(face_encode(cropped_image,device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')), name_list)
        
        # Upload photo and encoding      
        userPhotoKey = 'users.' + name + '.picture'
        update_doc(user_doc, userPhotoKey, imageBlob.public_url)
        userEncodingKey = 'users.' + name + '.encoding'
        update_doc(user_doc, userEncodingKey, embedding_link)
        print("Face uploaded.")

        if duplicate_faces(embedding_list,emb, names,name)== 'flagged':
            print("Error: Duplicate face detected.")
            return "flagged"
        elif duplicate_faces(embedding_list,emb, names,name)== 'flagged_before':
            print("Error: Duplicate face detected.")
            return "flagged_before"
        elif duplicate_faces(embedding_list,emb, names,name)== 'unknown':
            print("Error: Unknown face detected.")
            return "unknown"
    else:
        print("Error: No face detected, or there was an error processing the image.")
        return "error"
        

# Update photo status for professor to approve        
def update_photo_status(section, name, value):
    user_dict = get_doc(user_doc)
    student_dict = get_doc(student_doc)
    
    if lookup(name, user_dict) == None:
        print("Error: Cannot update photo status for '" + name + "' because the user does not exist.")
    elif lookup(name, student_dict['students'][section]) == None:
        print("Error: Cannot update photo status for '" + name + "' because the user is not in class '" + section + "'.")
    else:
        key = 'students.' + section + '.' + name + '.picture_status'
        print("Updated photo status for '" + name + "' in class '" + section + "'.")
        update_doc(student_doc, key, value)

# Update photo status for professor to approve (AS A BATCH)   
def update_photo_status_batch(name, value):
    user_dict = get_doc(user_doc)
    student_dict = get_doc(student_doc)
    
    if lookup(name, user_dict) == None:
        print("Error: Cannot update photo status for '" + name + "' because the user does not exist.")
    else:
        for section in student_dict['students']:
            if lookup(name, student_dict['students'][section]) == None:
                print("Error: Cannot update photo status for '" + name + "' because the user is not in class '" + section + "'.")
            else:
                key = 'students.' + section + '.' + name + '.picture_status'
                print("Updated photo status for '" + name + "' in class '" + section + "'.")
                update_doc(student_doc, key, value)
def check_picture_status(student_name):
    student_dict = get_doc(student_doc)

    # Iterate through each course
    for course_id, course_info in student_dict['students'].items():
        # Skip class_photos entries
        if course_id == 'class_photos':
            continue
        
        # Check if the student exists in this course
        if student_name in course_info:
            # Get the picture status for the student
            picture_status = course_info[student_name]['picture_status']
            # If the picture status is 'Flagged', return False
            if picture_status == 'Flagged':
                return False
    
    # If none of the picture statuses are 'Flagged', return True
    return True
print(check_picture_status('hi4718'))

    
#  Remove student photo
def remove_student_photo(name):
    bucket = storage.bucket()
    blob = bucket.blob(name + "_photo")
    if blob.exists():
        blob.delete()

        # Remove photo and encoding
        userKey = 'users.' + name + '.picture'
        update_doc(user_doc, userKey, "NO PHOTO")
        userKey = 'users.' + name + '.encoding'
        update_doc(user_doc, userKey, "NO ENCODING")
        print("Photo for '" + name + "' deleted successfully.")
        
        # Add encoding removal here
    else:
        print("Error: Student '" + name + "', if they exist, has no photo in the database.")


# Retrieve file from Firebase storage (filetype is 'picture' or 'encoding')
def retrieve_file(name, filetype): 
    doc = get_doc(user_doc)

    # Debug message
    if (doc['users'][name][filetype] == 'NO ENCODING'):
        print("Error: Cannot retrieve filetype '" + filetype + "' for user '" + name + "'.")
    else:
        print("Retrieved filetype '" + filetype + "' for user '" + name + "'.")
        
    return doc['users'][name][filetype]


# Retrieve array of names for all students in a class section
def retrieve_names_from_class(section): 
    doc = get_doc(student_doc)    
    return list(doc['students'][section].keys())
    
    
# Retrieve all encodings for a class section
def retrieve_encodings_from_class(section):
    names = retrieve_names_from_class(section)
    encoding_list = []
    for name in names:
        retrieved_encoding = retrieve_file(name, 'encoding')
        if retrieved_encoding != 'NO ENCODING':
            encoding_list.append(retrieved_encoding)
    
    return encoding_list 


# Set flag that class encoding needs update
def update_class_encoding_status(section, status):
    key = 'classes.' + section + '.class_encoding_update'
    update_doc(class_doc, key, status)


def retrieve_class_embedding(section): 
    doc = get_doc('class_doc')

    # Debug message
    if (doc['classes'][section]['class_encoding'] == 'NO ENCODING'):
        print("Error: Cannot retrieve filetype class encoding for class '" + section + "'.")
    else:
        print("Retrieved class encoding for class '" + section + "'.")
    print(doc['classes'][section]['class_encoding'])
    return doc['classes'][section]['class_encoding']

def download_file_combine(url, section):
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        with open(section, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    
    print(f"File downloaded and saved as {section}")
def retrieve_names_from_class(section): 
    doc = get_doc(student_doc)    
    names = list(doc['students'][section].keys()) 
    
    # Remove class_photos from names since it is not an actual student
    if "class_photos" in names:
        names.remove("class_photos")
        
    return names

def retrieve_encodings_from_class(section):
    names = retrieve_names_from_class(section)    
    encoding_list = []
    for name in names:
        retrieved_encoding = retrieve_file(name, 'encoding')
        if retrieved_encoding != 'NO ENCODING':
            encoding_list.append(retrieved_encoding)
    print(encoding_list)
    return encoding_list 
def retrieve_file(name, filetype): 
    doc = get_doc(user_doc)

    # Debug message
    if (doc['users'][name][filetype] == 'NO ENCODING'):
        print("Error: Cannot retrieve filetype '" + filetype + "' for user '" + name + "'.")
    else:
        print("Retrieved filetype '" + filetype + "' for user '" + name + "'.")
        
    return doc['users'][name][filetype]
def download_pt_file_student(url):
    response = requests.get(url)
    response.raise_for_status()
    buffer = BytesIO(response.content)
    embedding, name = torch.load(buffer, map_location='cpu')
    return embedding[0], name[0]

def update_doc(doc_id, key, value):
    doc_ref = db.collection(collectionName).document(doc_id)
    doc_ref.update({
        key: value
    })

def update_class_encoding_status(section, value):
    key = 'classes.' + section + '.class_encoding_update'
    update_doc(class_doc, key, value)

def update_class_encoding(section, file):
    doc = get_doc(class_doc)
    if doc['classes'][section]['class_encoding_update'] == True:
        bucket = storage.bucket()
        blob = bucket.blob(section + ".pt")
        blob.upload_from_filename(file)
        blob.make_public()
        # Update encoding status to show encoding update is no longer needed
        update_class_encoding_status(section, False)

        # Upload
        key = 'classes.' + section + '.class_encoding'
        update_doc(class_doc, key, blob.public_url)
    else:
        print("Error: Encoding update is not needed for '" + section + "'.")

def combine_pt_files(section):
    combined_embedding_list = []
    combined_name_list = []

    urls = retrieve_encodings_from_class(section)
    for url in urls:
        embedding, name = download_pt_file_student(url)
        combined_embedding_list.append(embedding)
        combined_name_list.append(name)
    #print(combined_embedding_list)
    combined_data = {'embedding_list': combined_embedding_list, 'name_list': combined_name_list}
    torch.save([combined_embedding_list,combined_name_list], f'{section}.pt')
    update_class_encoding(section, f'{section}.pt')