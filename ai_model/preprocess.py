from facenet_pytorch import MTCNN
import cv2

def detect_and_crop_face(image_path, device='cpu', min_face_size=20, thresholds=[0.6, 0.7, 0.7], factor=0.709):
    mtcnn = MTCNN(keep_all=True, device=device, min_face_size=min_face_size, thresholds=thresholds, factor=factor)
    frame = cv2.imread(image_path)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces, _ = mtcnn.detect(frame_rgb)
    
    if  len(faces) == 1:
        face = faces[0]
        x1, y1, x2, y2 = [int(coord) for coord in face]
        cropped_face = frame_rgb[y1:y2, x1:x2]
        cropped_face_bgr = cv2.cvtColor(cropped_face, cv2.COLOR_RGB2BGR)
        return cropped_face_bgr
    else:
        return None

cropped_face = detect_and_crop_face('photos/hc9082/hc9082.jpg')
if cropped_face is not None:

    cv2.imwrite('cropped_face.jpg', cropped_face)
else:
    print("No face detected.")
