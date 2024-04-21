import cv2
from facenet_pytorch import MTCNN
import torch

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(keep_all=True, device=device)

#not using this function beacuse it is not needed
def detect_faces(frame):
    # Convert the frame from BGR to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Detect faces in the frame
    faces, _ = mtcnn.detect(frame_rgb)
    # If faces are detected, draw bounding boxes
    if faces is not None:
        # Get the number of faces detected
        count = len(faces)
        # Draw bounding boxes around the faces
        #faces is a list of coordinates of the faces in the image
        for face in faces:
            # Draw a rectangle around the face
            cv2.rectangle(frame,
                          (int(face[0]), int(face[1])),
                          (int(face[2]), int(face[3])),
                          (0, 0, 0), 2)
        # Display the number of faces detected
        cv2.putText(frame, f"Number of faces detected: {count}", (130, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 255, 255), 1)
    else:
        # If no faces are detected, display a message
        cv2.putText(frame, "No faces detected", (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    # Return the frame with bounding boxes
    return frame

# Function to check for external cameras
def find_external_camera():
    for index in range(10):
        camera = cv2.VideoCapture(index)
        if camera.isOpened():
            _, _ = camera.read()  # Grab a frame to check if camera is working
            if _ is not None:
                return index
            camera.release()
    return None

external_camera_index = find_external_camera()
if external_camera_index is not None:
    print(f"External camera found at index {external_camera_index}")
    camera = cv2.VideoCapture(external_camera_index)
else:
    print("External camera not found. Using default camera.")
    camera = cv2.VideoCapture(0)

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

while True:
    ret, frame = camera.read()

    processed = detect_faces(frame)
    cv2.imshow("Face detector", processed)

    if cv2.waitKey(1) & 0xFF == ord('c'):
        break

camera.release()
cv2.destroyAllWindows()