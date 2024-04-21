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
#  Get the Firebase credentials from the file and initialize the Firebase app with them
cred_fp = str(Path.cwd()) + "\db_credentials.json"
cred = credentials.Certificate(cred_fp)
firebase_admin.initialize_app(cred, {'storageBucket': 'facecheck-93450.appspot.com'})

#  Assign Firebase client to a variable
db = firestore.client()
#  Save collection and document names to variables
collectionName = "infoCollection"
class_doc = "class_doc"
student_doc = "student_doc"
user_doc = "user_doc"
professor_doc = "professor_doc"


#  ------------------------------  MAIN FUNCTIONALITY  ------------------------------
#  Retrieve all docs in collection
def get_all_docs():
    #  Retrieve all documents
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
    # Assign a reference to the document and get its contents
    doc_ref = db.collection(collectionName).document(doc_id)
    doc = doc_ref.get()
    # Return as a dicionary
    if doc.exists:
        return doc.to_dict()
    else:
        print(f"Document {doc_id} not found in {collectionName}.")
        return None
    
    
#  Recursively search dictionary
#  "key" represents a key to search for in the dictionary, "data" is the data being searched for the key
def lookup(key, data):
    if key in data:
        return data[key]
    for value in data.values():
        # Is the object a dictionary?
        if isinstance(value, dict):
            # Successfully found item, return the value/definition associated with that key
            return lookup(key, value)
    return None


#  Get current date and time
def getDate():
    # Get the date right now
    now = datetime.now()
    return now.strftime("%m_%d_%Y")

def getTime():
    # Get the time right now
    now = datetime.now()
    return now.strftime("%H_%M_%S")
    
       
#  Update existing document
def update_doc(doc_id, key, value):
    # Get a reference to the specified document
    doc_ref = db.collection(collectionName).document(doc_id)
    # Update the document with the given key & value dictionary pair
    doc_ref.update({
        key: value
    })

#  Add new class section
def add_class(section, prof):
    # Get the class document from Firebase as a dictionary object
    class_dict = get_doc(class_doc)
    
    # If the class ID is found in the class, fail to add it since it already exists. Otherwise add it
    if lookup(section, class_dict) != None:
        print("Error: Cannot add class '" + section + "' because the class already exists.")
    else:
        # Update the doc using the path as the dictionary key, and prof as the dictionary value
        key = 'classes.' + section + '.professor'
        update_doc(class_doc, key, prof)
        print("Class '" + section + "' successfully added.")
    
#  Add new student to **DATABASE**
def add_student(accessid, fname, lname, role = "student"):
    # Get the user document from Firebase as a dictionary object
    user_dict = get_doc(user_doc)
    
    # If the user already exists, fail to add. Otherwise add successfully.
    if lookup(accessid, user_dict) != None:
        print("Error: Cannot add user '" + accessid + "' because the user already exists.")
    else:
        # Save the prof doc in Firebase as a dictionary objec
        prof_dict = get_doc(professor_doc)
        # Determine if the user should receive the professor role by checking the prof doc in Firebase
        if lookup(accessid, prof_dict) != None:
            role = "professor"
        
        # Assign the user a default first name, last name, picture, encoding, role, and audit log entry
        # key and value represent key/value pairs in a dictionary object to be added to the User doc in Firebase
        # Update the doc with the key/value pair after they are assigned
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
#  Section represents the class section/class ID
def add_student_to_class(section, accessid):
    # Save data from the student doc and user doc in Firebase as dictionary objects
    student_dict = get_doc(student_doc)
    user_dict = get_doc(user_doc)
    
    # Does the student already exist in this class?
    if lookup(accessid, student_dict['students'][section]) != None:
        print("Error: Cannot add user '" + accessid + "' because the user is already in " + section + ".")
    # Does the student exist at all?
    elif lookup(accessid, user_dict) == None:
        print("Error: Cannot add user '" + accessid + "' because the user does not exist.")
    # If above conditions are not the case, add the student to the class
    else:
        # Use dictionary key/value pairs to update the student and class documents with necessary information.
        # Initialize the attendance field for the student in Firebase by entering a zero date which will never be used.
        # This will make sure that the attendance path DOES exist in Firebase when checked for later.
        key = 'students.' + section + '.' + accessid + '.attendance.00_00_0000.00_00_00'
        update_doc(student_doc, key, True)
        # Force an update to the class encoding status so that a new encoding file is generated.
        classKey = 'classes.' + section + '.encoding_update'
        update_doc(class_doc, classKey, True)
        
        # Debug confirmation message
        print("Student '" + accessid + "' successfully added to " + section + ".")
   
    
#  ------------------------------  SHORTCUT FUNCTIONS  ------------------------------
#  Update student attendance
#  "section" represents the class section/class ID. "value" represents the attendance value (true/false)
#  If no date/time are entered by default, they are assigned to current time
def update_student_attendance(section, name, value, date = getDate(), time = getTime()):
    # Get the contents of the student doc in Firebase as a dictionary object.
    student_dict = get_doc(student_doc)
    
    # Does the user exist in this class? If so, update the attendance document with the appropriate dictionary 
    # key/value pair representing the student's attendance at that current date/time.
    if lookup(name, student_dict) == None:
        print("Error: Cannot update attendance for '" + name + "' because the user does not exist.")
    else:
        key = 'students.' + section + '.' + name + '.attendance.' + date + '.' + time
        update_doc(student_doc, key, value)
        print("Student '" + name + "' marked as present on " + date + " at " + time + ".")

#  Update student photo
def update_student_photo(name, file):
    # Use CUDA if available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Create a new Firebase Storage bucket
    bucket = storage.bucket()
    # Set a name for the blob that will be used to upload the photo
    imageBlob = bucket.blob(name + "_photo")
    # Store the user's name as a list, used for make_pt_file
    name_list = [name]
    
    # Import function to detect duplicate faces 
    # This is imported within this function to avoid a circular import
    from duplicate import duplicate_faces
    
    # Check for duplicates based on this class ID
    class_id= 'CSC_4996_001_W_2024'
    
    # Download or combine pt/encoding/embedding file
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
            # Upload to image blob
            imageBlob.upload_from_filename(temp_file.name)

        embedding_list = face_encode(cropped_image, device=device)
        # If face_encode returns a single tensor, make sure it's on the right device
        embedding_list = [emb.to(device) for emb in embedding_list]
            
        # Save encoding to temporary location and upload
        embedding_link = make_pt_file(face_encode(cropped_image,device=torch.device('cuda' if torch.cuda.is_available() else 'cpu')), name_list)
        
        # Upload photo and encoding using dictionary key/value pairs    
        userPhotoKey = 'users.' + name + '.picture'
        update_doc(user_doc, userPhotoKey, imageBlob.public_url)
        userEncodingKey = 'users.' + name + '.encoding'
        update_doc(user_doc, userEncodingKey, embedding_link)
        print("Face uploaded.")

        # Return based on results of duplicate face detection
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
# Arguments are class section/class ID, student name, and the desired value for the student's photo status  
def update_photo_status(section, name, value):
    # Store the contents of the user and student documents in Firebase as dictionary objects
    user_dict = get_doc(user_doc)
    student_dict = get_doc(student_doc)
    
    # Does this user exist?
    if lookup(name, user_dict) == None:
        print("Error: Cannot update photo status for '" + name + "' because the user does not exist.")
    # Is this user part of this class?
    elif lookup(name, student_dict['students'][section]) == None:
        print("Error: Cannot update photo status for '" + name + "' because the user is not in class '" + section + "'.")
    # If the above conditions are not the case, use dictionary key/value pairs to update the student's photo status to the given value
    else:
        key = 'students.' + section + '.' + name + '.picture_status'
        print("Updated photo status for '" + name + "' in class '" + section + "'.")
        update_doc(student_doc, key, value)

# Update photo status for professor to approve (AS A BATCH)   
# Arguments are student name, and the desired value for the student's photo status  
def update_photo_status_batch(name, value):
    # Store the contents of the user and student documents in Firebase as dictionary objects
    user_dict = get_doc(user_doc)
    student_dict = get_doc(student_doc)
    
    # Does this user exist?
    if lookup(name, user_dict) == None:
        print("Error: Cannot update photo status for '" + name + "' because the user does not exist.")
    # If the user exists, iterate through all class sections/class IDs the user is in and update the photo status to the given value.
    else:
        for section in student_dict['students']:
            # Checks if a user is part of that class
            if lookup(name, student_dict['students'][section]) == None:
                print("Error: Cannot update photo status for '" + name + "' because the user is not in class '" + section + "'.")
            else:
                # Update the student attendance document using dictionary key/value pairs
                key = 'students.' + section + '.' + name + '.picture_status'
                print("Updated photo status for '" + name + "' in class '" + section + "'.")
                update_doc(student_doc, key, value)
                
# This function was written by Ahmed Minhaj
def check_picture_status(student_name):
    # Store the contents of the student document in Firebase as a dictionary object
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
    # Get the Firebase Storage bucket and blob in which the student's photo is saved in
    bucket = storage.bucket()
    blob = bucket.blob(name + "_photo")
    # If the image blob exists, delete it
    if blob.exists():
        blob.delete()

        # Remove photo and encoding by updating the respective dictionary key/value pairs. Update the user doc with these changes.
        userKey = 'users.' + name + '.picture'
        update_doc(user_doc, userKey, "NO PHOTO")
        userKey = 'users.' + name + '.encoding'
        update_doc(user_doc, userKey, "NO ENCODING")
        print("Photo for '" + name + "' deleted successfully.")
    else:
        print("Error: Student '" + name + "', if they exist, has no photo in the database.")


# Retrieve file from Firebase storage (filetype is 'picture' or 'encoding')
def retrieve_file(name, filetype): 
    # Get the user doc from Firebase as a dictionary object
    doc = get_doc(user_doc)

    # Debug message if there is no file for the given filetype
    if (doc['users'][name][filetype] == 'NO ENCODING'):
        print("Error: Cannot retrieve filetype '" + filetype + "' for user '" + name + "'.")
    else:
        print("Retrieved filetype '" + filetype + "' for user '" + name + "'.")
        
    # Return link to the file
    return doc['users'][name][filetype]


# Retrieve array of names for all students in a class section
def retrieve_names_from_class(section): 
    # Get the student doc from Firebase as a dictionary object
    doc = get_doc(student_doc)    
    # Return the keys containing student names from the class
    return list(doc['students'][section].keys())
    
    
# Retrieve all encodings for a class section
def retrieve_encodings_from_class(section):
    # Get the list of names from the class with an approved photo
    names = retrieve_names_from_class(section)
    
    # For each name, get the list of encoding files from each student with approved photos.
    # If the student has no encoding, skip them.
    encoding_list = []
    for name in names:
        retrieved_encoding = retrieve_file(name, 'encoding')
        if retrieved_encoding != 'NO ENCODING':
            encoding_list.append(retrieved_encoding)
    
    # Return the resulting list of encodings
    return encoding_list 


# Set flag that class encoding needs update
# Arguments are class section/class ID and the status to update with
def update_class_encoding_status(section, status):
    # Update class encoding status in the database using the path as the dict key and the status as the dict value
    key = 'classes.' + section + '.class_encoding_update'
    update_doc(class_doc, key, status)

# Retrieve class embedding file from Firebase storage
def retrieve_class_embedding(section): 
    # Get the user doc from Firebase as a dictionary object
    doc = get_doc('class_doc')

    # Debug message if there is no class encoding/embedding file
    if (doc['classes'][section]['class_encoding'] == 'NO ENCODING'):
        print("Error: Cannot retrieve filetype class encoding for class '" + section + "'.")
    else:
        print("Retrieved class encoding for class '" + section + "'.")
    print(doc['classes'][section]['class_encoding'])
    # Return link to the encoding/embedding file
    return doc['classes'][section]['class_encoding']

# This function was written by Ahmed Minhaj
# Download the file from the url and save it as the section name
def download_file_combine(url, section):
    # Download the file from the URL
    with requests.get(url, stream=True) as response:
        # Open the contents and write the chunks into a file
        response.raise_for_status()
        with open(section, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
    
    print(f"File downloaded and saved as {section}")
    
# Retrieve array of names for all students in a class section
def retrieve_names_from_class(section): 
    # Get the student attendance doc from Firebase as a dictionary object
    doc = get_doc(student_doc)    
    # Get a list of names for that class section/class ID
    names = list(doc['students'][section].keys()) 
    
    # Remove class_photos from names since it is not an actual student
    if "class_photos" in names:
        names.remove("class_photos")
        
    return names

# Retrieve all encodings for a class section
def retrieve_encodings_from_class(section):
    # Get the list of names from the class with an approved photo
    names = retrieve_names_from_class(section)    
    
    # For each name, get the list of encoding files from each student with approved photos.
    # If the student has no encoding, skip them.
    encoding_list = []
    for name in names:
        retrieved_encoding = retrieve_file(name, 'encoding')
        if retrieved_encoding != 'NO ENCODING':
            encoding_list.append(retrieved_encoding)
    print(encoding_list)
    
    # Return the resulting list of encodings
    return encoding_list 

# Retrieve file from Firebase storage (filetype is 'picture' or 'encoding')
def retrieve_file(name, filetype): 
    # Get the user doc from Firebase as a dictionary object
    doc = get_doc(user_doc)

    # Debug message if there is no file for the given filetype
    if (doc['users'][name][filetype] == 'NO ENCODING'):
        print("Error: Cannot retrieve filetype '" + filetype + "' for user '" + name + "'.")
    else:
        print("Retrieved filetype '" + filetype + "' for user '" + name + "'.")
      
    # Return link to the file  
    return doc['users'][name][filetype]

# The following function was written by Ahmed Minhaj
# Download the emedding/pt file for the student
def download_pt_file_student(url):
    # Get the response for the URL containing the link to the file
    response = requests.get(url)
    response.raise_for_status()
    # Create a buffer and get the name & embedding
    buffer = BytesIO(response.content)
    embedding, name = torch.load(buffer, map_location='cpu')
    return embedding[0], name[0]


#  Update existing document
def update_doc(doc_id, key, value):
    # Get a reference to the specified document
    doc_ref = db.collection(collectionName).document(doc_id)
    # Update the document with the given key & value dictionary pair
    doc_ref.update({
        key: value
    })

# Set flag that class encoding needs update
def update_class_encoding_status(section, value):
    key = 'classes.' + section + '.class_encoding_update'
    update_doc(class_doc, key, value)

#  Update class encoding
#  Arguments are class section/class ID and a given class encoding/embedding file
def update_class_encoding(section, file):
    # Store the contents of the class document in Firebase as a dictionary object
    doc = get_doc(class_doc)
    
    # If the flag to update the class's encoding is set to true, upload the file
    if doc['classes'][section]['class_encoding_update'] == True:
        # Create a Firebase storage bucket and make a blob to store the file within it
        bucket = storage.bucket()
        blob = bucket.blob(section + ".pt")
        blob.upload_from_filename(file)
        # Make the blob public so that the URL is accessible
        blob.make_public()
        # Update encoding status to show encoding update is no longer needed
        update_class_encoding_status(section, False)

        # Update the class document with the link to the file using a dictionary key/value pair
        key = 'classes.' + section + '.class_encoding'
        update_doc(class_doc, key, blob.public_url)
    else:
        print("Error: Encoding update is not needed for '" + section + "'.")

# This function was written by Ahmed Minhaj
# Combine all the pt/encoding/embedding files of the students in the class and make a class pt file, then save it as the class name
# section represents the class section/class ID
def combine_pt_files(section):
    # Arrays for the lists of combined embeddings and names
    combined_embedding_list = []
    combined_name_list = []
    # Retrieve all encoding URLS for the class
    urls = retrieve_encodings_from_class(section)
    
    for url in urls:
        # get the embedding and name from the url
        embedding, name = download_pt_file_student(url)
        # append the embedding and name to the list
        combined_embedding_list.append(embedding)
        combined_name_list.append(name)
    # save the combined embedding and name list as a pt file
    combined_data = {'embedding_list': combined_embedding_list, 'name_list': combined_name_list}
    torch.save([combined_embedding_list,combined_name_list], f'{section}.pt')
    # upload the file to the firebase using section as the dict key and the pt file name as the dict value
    update_class_encoding(section, f'{section}.pt')