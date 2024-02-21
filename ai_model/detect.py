import cv2
from facenet_pytorch import MTCNN
import torch

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Adjust these parameters to fine-tune your face detection
min_face_size = 40 # example value, adjust as needed
thresholds = [0.8, 0.8, 0.8]  # example values, adjust as needed
factor = 0.8  # example value, adjust as needed

mtcnn = MTCNN(keep_all=True, device=device, min_face_size=min_face_size, thresholds=thresholds, factor=factor)

def detect_faces(frame):
    mtcnn = MTCNN(keep_all=True, device=device, min_face_size=min_face_size, thresholds=thresholds, factor=factor)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces, _ = mtcnn.detect(frame_rgb)

    if faces is not None:
        count = len(faces)
        for face in faces:
            cv2.rectangle(frame,
                          (int(face[0]), int(face[1])),
                          (int(face[2]), int(face[3])),
                          (0, 0, 0), 2)
        cv2.putText(frame, f"Number of faces detected: {count}", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    else:
        cv2.putText(frame, "No faces detected", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    return frame

camera = cv2.VideoCapture(0) # Use 1 for external camera
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

try:
    while True:
        ret, frame = camera.read()
        if not ret:
            break  # Break the loop if the frame is not captured properly

        processed = detect_faces(frame)
        cv2.imshow("Face Detector", processed)

        if cv2.waitKey(1) & 0xFF == ord('c'):
            break
finally:
    camera.release()
    cv2.destroyAllWindows()
