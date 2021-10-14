import cv2
import mediapipe as mp
import time
import json
import sys
from operator import xor

class poseDetector():
    # Under: https://google.github.io/mediapipe/images/mobile/pose_tracking_full_body_landmarks.png
    BODY_PARTS = {
        # Head
        0: "Nose", 
        1: "LeftEyeInner", 2: "LeftEye", 3: "LeftEyeOuter", 4: "RightEyeInner", 5: "RightEye", 6: "RightEyeOuter",
        7: "LeftEar", 8: "RightEar", 
        9: "MouthLeft", 10: "MouthRight",

        # Left arm + hand
        11: "shoulder01.L", 13: "lowerarm01.L", 15: "wrist.L",
        17: "LeftPinky", 19: "LeftIndex", 21: "LeftThumb",
        # Right arm + hand
        12: "shoulder01.R", 14: "lowerarm01.R", 16: "wrist.R",
        18: "RightPinky",  20: "RightIndex",  22: "RightThumb",

        # Left foot
        23: "upperleg01.L", 25: "lowerleg01.L", 27: "foot.L", 29: "LeftHeel", 31: "LeftFootIndex",
        # Right foot
        24: "upperleg01.R", 26: "lowerleg01.R", 28: "foot.R", 30: "RightHeel", 32: "RightFootIndex" 
    }


    def __init__(self, static_image=False, complexity=1, smooth=True,
                 detection_conf=0.8, track_conf=0.2):
        self.static_image = static_image
        self.complexity = complexity
        self.smooth = smooth
        self.detection_conf = detection_conf
        self.track_conf = track_conf

        self.mpDraw = mp.solutions.drawing_utils
        self.mpPose = mp.solutions.pose
        self.pose = self.mpPose.Pose(self.static_image, self.complexity, self.smooth,
                                     self.detection_conf, self.track_conf)
        

        # White
        self.style_neutral = self.mpDraw.DrawingSpec()
        self.style_neutral.color = (255, 255, 255)
        self.style_neutral.thickness = 4
        self.style_neutral.circle_radius = 8
        self.connections_neutral = set(filter(lambda x: xor(x[0] % 2 == 0, x[1] % 2 == 0), self.mpPose.POSE_CONNECTIONS))

        # Yellowish
        self.style_right = self.mpDraw.DrawingSpec()
        self.style_right.color = (0, 255, 255)
        self.style_right.thickness = 4
        self.style_neutral.circle_radius = 0
        self.connections_right = set(filter(lambda x: x[0] % 2 == 0 and x[1] % 2 == 0, self.mpPose.POSE_CONNECTIONS))
        
        # Blueish
        self.style_left = self.mpDraw.DrawingSpec()
        self.style_left.color = (255, 127, 0)
        self.style_left.thickness = 4
        self.style_neutral.circle_radius = 0
        self.connections_left = set(filter(lambda x: x[0] % 2 == 1 and x[1] % 2 == 1, self.mpPose.POSE_CONNECTIONS))

    def process(self, img):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(imgRGB)
        return img


    def draw(self, img):
        if self.results.pose_landmarks:
            self.mpDraw.draw_landmarks(img, self.results.pose_landmarks,
                                        self.connections_right, self.style_right, self.style_right)
            self.mpDraw.draw_landmarks(img, self.results.pose_landmarks,
                                        self.connections_left, self.style_left, self.style_left)
            self.mpDraw.draw_landmarks(img, self.results.pose_landmarks,
                                        self.connections_neutral, self.style_neutral, self.style_neutral)
            
            for landmark in self.screenSpaceLmList: 
                cv2.circle(img, (landmark[0], landmark[1]), 5, (255, 0, 0), cv2.FILLED)
        return img


    def findPose(self, img):
        self.lmDict = dict()
        self.screenSpaceLmList = list()
        if self.results.pose_landmarks:
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                self.screenSpaceLmList.append((cx, cy))
                self.lmDict[self.BODY_PARTS[id]] = [lm.x, lm.y, lm.z]

        return self.lmDict
        

name = sys.argv[1]
source = sys.argv[2]
cap = cv2.VideoCapture(name)
pTime = 0
detector = poseDetector()

poses = []

while True:
    success, img = cap.read()
    if not success:
        cap.release()
        break
    
    img = detector.process(img)
    lmDict = detector.findPose(img)
    img = detector.draw(img)
    if len(lmDict) !=0:
        poses.append(lmDict)

    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime

    cv2.putText(img, str(int(fps)), (70, 50), cv2.FONT_HERSHEY_PLAIN, 3,
                (255, 0, 0), 3)
    cv2.namedWindow('Image', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Image', 800, 600)

    cv2.imshow("Image", img)
    cv2.waitKey(1)

bones = []
for key, value in poseDetector.BODY_PARTS.items():
    bones.append(value)


_dict = {
    "bones": bones,
    "poses": poses
}
with open(source, "w+") as f:
    json.dump(_dict, f)