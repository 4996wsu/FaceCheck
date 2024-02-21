from facenet_pytorch import MTCNN
import cv2

def detect_and_crop_faces(image_path, device='cpu', min_face_size=20, thresholds=[0.6, 0.7, 0.7], factor=0.709):
    # Initialize MTCNN for face detection
    mtcnn = MTCNN(keep_all=True, device=device, min_face_size=min_face_size, thresholds=thresholds, factor=factor)
    
    # Load the image
    frame = cv2.imread(image_path)
    
    # Convert the image from BGR (OpenCV format) to RGB (MTCNN format)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Detect faces in the image
    faces, _ = mtcnn.detect(frame_rgb)
    
    cropped_faces = []
    
    if faces is not None:
        # Crop faces from the image
        for face in faces:
            # Extract the coordinates of the face
            x1, y1, x2, y2 = [int(coord) for coord in face]
            # Crop the face from the original frame
            cropped_face = frame_rgb[y1:y2, x1:x2]
            # Convert the cropped face back to BGR color space for consistency with OpenCV
            cropped_face_bgr = cv2.cvtColor(cropped_face, cv2.COLOR_RGB2BGR)
            cropped_faces.append(cropped_face_bgr)
    
    return cropped_faces
