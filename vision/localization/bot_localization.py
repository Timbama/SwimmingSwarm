import cv2
from matplotlib.pyplot import contour
import numpy as np
from numpy.lib.type_check import imag

def draw_arrow(image, x, y, yaw):
    length = 40
    vX = np.cos(yaw)
    vY = np.sin(yaw)
    cX = x + vX * length
    cY = y + vY * length
    dX = x - vX * length
    dY = y - vY * length
    cv2.arrowedLine(image, (int(cX),int(cY)), (int(dX),int(dY)),(0,255,0), 10 , tipLength=.4)

def draw_text(image, x, y, text):
  cv2.putText(image, text, (x+ 20, y-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

class Bot:
  def __init__(self, x, y, id):
    self.x = x
    self.y = y
    self.yaw = 0
    self.id = id
    self.toggle = False
  def set_yaw(self, yaw):
    self.yaw = yaw
  def set_position(self,x,y):
    self.x = x
    self.y = y

class BotDetector:
  # NOTE this bot detector is  only setup for a single bot currently it will return the contrours around the bots
  def __init__(self, num_bots, camera_height, img_dim):
    self.num_bots = num_bots
    self.camera_height = camera_height
    self.img_dim = img_dim
    self.min_bot_area = 10000
    self.lower_color = np.array([0,130,50])
    self.upper_color = np.array([30,255,255])
  def segment_image(self, image):
    '''
    Segments a single color rang and applies morphological closing and opening to clean up the image
    '''
    img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(img_hsv, self.lower_color, self.upper_color)
    kernel = np.ones((21,21),np.uint8)
    open = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    return cv2.morphologyEx(open, cv2.MORPH_CLOSE, kernel)
  def generate_contours(self, image):
    '''
    simple wrapper for cv find contours (could be used to change the method of finding contours)
    '''
    contours,_= cv2.findContours(image,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    return contours
  def split_bots(self, contours):
    # TODO: split the bots appropriatly instead of taking the largest
    if contours != None:
      detections = []
      max_contour = contours[0]
      for contour in contours:
        if cv2.contourArea(contour)>cv2.contourArea(max_contour):
          max_contour = contour
      detections.append(max_contour)
      return detections
  def run(self, image):
    mask = self.segment_image(image)
    contours = self.generate_contours(mask)
    detections = self.split_bots(contours)
    return detections

class BotTracker:
  def __init__(self, num_bots, camera_height, img_dim):
    self.num_bots = num_bots
    self.camera_height = camera_height
    self.img_dim = img_dim
    self.current_tracks = []
    self.count = 0
  def initilize_tracking(self, detections):
    for detection in detections:
      M=cv2.moments(detection)
      cx=int(M['m10']//M['m00'])
      cy=int(M['m01']//M['m00'])
      bot = self.process_contour(detection, Bot(cx,cy,self.count))
      self.current_tracks.append(bot)
      self.count = self.count + 1 
  def process_contour(self, contour, bot):
    [vX,vY,x,y] = cv2.fitLine(contour, cv2.DIST_L2,0,0.01,0.01)
    if bot.toggle:
      temp = vX
      vx = -vY
      vy = temp   
      curr_angle  = np.arctan2(vy, vx)
    else:
      temp = -vX
      vx = vY
      vy = temp
      curr_angle  = np.arctan2(vy, vx)
    if ( np.abs(curr_angle - bot.yaw) <1.54):
      pass      
    else:
      bot.toggle = ~bot.toggle
      if bot.toggle:
        temp = vX
        vx = -vY
        vy = temp 
        curr_angle  = np.arctan2(vy, vx)
      else:
        temp = -vX
        vx = vY
        vy = temp
        curr_angle  = np.arctan2(vy, vx)
    bot.set_yaw(curr_angle)
    return bot
  def update_tracks(self, detections):
    for detection in detections:
      M=cv2.moments(detection)
      cx=int(M['m10']//M['m00'])
      cy=int(M['m01']//M['m00'])
      found = False
      i =0
      for track in self.current_tracks:
        if np.hypot((track.x - cx), (track.y- cy)) < 100:
            track = self.process_contour(detection, track)
            track.set_position(cx, cy)
            found = True
            self.current_tracks[i] = track
            break
        i = i + 1
      if(not found):
        print("append")
        bot = self.process_contour(detection, Bot(cx,cy,self.count))
        self.current_tracks.append(bot)
        self.count = self.count + 1 
  def compare_to_current_tracks(potential_tracks):
    pass
  def prune_tracks():
    pass

if __name__ == "__main__":
  cap = cv2.VideoCapture("/mnt/c/Users/tgallion.TIMS-XPS/Data/20211108_175325.mp4")
  if (cap.isOpened()== False): 
    print("Error opening video stream or file")
  first = True
  detector = BotDetector(10, 1.72, 10)
  tracker = BotTracker(10, 1.72, 10)

  while(cap.isOpened()):

    ret, frame = cap.read()
    if ret == True:
      frame  = frame[650:1550, 100:1080]
      if first:
        detections = detector.run(frame)
        tracker.initilize_tracking(detections)
        first = False
      else:
        detections = detector.run(frame)
        tracker.update_tracks(detections)
      for track in tracker.current_tracks:
        draw_arrow(frame, track.x, track.y,track.yaw)
        draw_text(frame, track.x, track.y, "ID:" + str(track.id))
        print("ID:" + str(track.id) + "\tX:" + str(track.x) + "\tY:" + str(track.y) + "\tYaw:" + str(track.yaw))
      cv2.imshow("frame",frame)
      if cv2.waitKey(25) & 0xFF == ord('q'):
        break
    else:
      break

  cap.release()

  cv2.destroyAllWindows()