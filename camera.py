import cv2
import sqlite3

facedetect = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("recognizer/trainingdata.yml")

# Set the threshold for confidence (higher values require more confidence)
CONFIDENCE_THRESHOLD = 50  # You can adjust this value

def getprofile(id):
    conn = sqlite3.connect("database.db")
    cursor = conn.execute("SELECT * FROM STUDENTS WHERE ID=?", (id,))
    profile = None
    for row in cursor:
        profile = row
    conn.close()
    return profile

class Video(object):
    def __init__(self):
        # Initialize webcam (default index is 0)
        self.video = cv2.VideoCapture(0)
        if not self.video.isOpened():
            raise Exception("Could not open webcam. Please check your camera.")

    def __del__(self):
        # Release the webcam when the object is destroyed
        if self.video.isOpened():
            self.video.release()

    def get_frame(self):
        # Read a frame from the webcam
        ret, img = self.video.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = facedetect.detectMultiScale(img, 1.3, 5)
        for (x, y, w, h) in faces:
            # Draw a rectangle around the face
            face_roi = gray[y:y + h, x:x + w]
            id, conf = recognizer.predict(face_roi)

            if conf < CONFIDENCE_THRESHOLD:  # Face recognized with high confidence
                profile = getprofile(id)
                profile = list(profile)
                profile[0] = str(profile[0])
                profile[0] = profile[0][:3] + 'u' + profile[0][3:]
                if profile is not None:
                    # If recognized, draw green box and display name
                    cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 1)

                    # top left
                    cv2.line(img, (x, y), (x + 30, y), (255, 0, 255), 6)
                    cv2.line(img, (x, y), (x, y + 30), (255, 0, 255), 6)

                    # top right
                    cv2.line(img, (x + w, y), ((x + w) - 30, y), (255, 0, 255), 6)
                    cv2.line(img, (x + w, y), ((x + w), y + 30), (255, 0, 255), 6)

                    # bottom left
                    cv2.line(img, (x, y + h), (x + 30, y + h), (255, 0, 255), 6)
                    cv2.line(img, (x, y + h), (x, (y + h) - 30), (255, 0, 255), 6)

                    # bottom right
                    cv2.line(img, (x + w, y + h), ((x + w) - 30, (y + h)), (255, 0, 255), 6)
                    cv2.line(img, (x + w, y + h), ((x + w), (y + h) - 30), (255, 0, 255), 6)

                    cv2.putText(img, 'UID: ' + str(profile[0]), (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 1,
                                (0, 255, 127), 2)
            else:  # Low confidence, display as Unknown
                # Draw red box for unknown face
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(img, 'Unknown', (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        if not ret:
            raise Exception("Failed to capture image from webcam.")
        # Encode the frame as JPEG
        ret, jpg = cv2.imencode('.jpg', img)
        if not ret:
            raise Exception("Failed to encode image to JPEG.")
        # Convert the encoded image to bytes
        return jpg.tobytes()
