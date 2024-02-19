import face_recognition
import os
import numpy as np
from PIL import Image, ImageDraw

# Load each student's image and create encoding for each
def create_student_encodings(student_images_folder):
    student_encodings = {}
    for filename in os.listdir(student_images_folder):
        # Ensure file is an image
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            student_name = os.path.splitext(filename)[0]
            image_path = os.path.join(student_images_folder, filename)
            student_image = face_recognition.load_image_file(image_path)
            student_encoding = face_recognition.face_encodings(student_image)[0]
            student_encodings[student_name] = student_encoding
    return student_encodings

# Function to recognize faces in an unseen test image
def recognize_faces_in_image(test_image_path, student_encodings):
    # Load test image
    test_image = face_recognition.load_image_file(test_image_path)
    face_locations = face_recognition.face_locations(test_image)
    face_encodings = face_recognition.face_encodings(test_image, face_locations)

    # Convert the image to a PIL-format image
    pil_image = Image.fromarray(test_image)
    draw = ImageDraw.Draw(pil_image)

    # Loop through faces in test image
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(list(student_encodings.values()), face_encoding)
        name = "Unknown"

        # Use the known face with the smallest distance to the new face
        face_distances = face_recognition.face_distance(list(student_encodings.values()), face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = list(student_encodings.keys())[best_match_index]

        # Draw box around face
        draw.rectangle(((left, top), (right, bottom)), outline=(0, 0, 255))

        # Draw label
        text_width, text_height = draw.textsize(name)
        draw.rectangle(((left, bottom - text_height - 10), (right, bottom)), fill=(0, 0, 255), outline=(0, 0, 255))
        draw.text((left + 6, bottom - text_height - 5), name, fill=(255, 255, 255, 255))

    # Remove the drawing library from memory as per the Pillow documentation
    del draw

    # Display the resulting image
    pil_image.show()

# Example usage
student_images_folder = 'dataset/data/anchor'
student_encodings = create_student_encodings(student_images_folder)
test_image_path = 'test_data/test/ahmed/ahmed.jpg'
recognize_faces_in_image(test_image_path, student_encodings)