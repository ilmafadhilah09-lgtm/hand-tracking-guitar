import cv2
import mediapipe as mp
import pygame
import os

pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.mixer.init()
pygame.mixer.set_num_channels(32) 

chord_sounds = {}
chords_list = ["C", "Dm", "Am", "F", "G"]

print("Memuat file audio...")
for chord in chords_list:
    file_name = f"{chord}.wav"
    if os.path.exists(file_name):
        chord_sounds[chord] = pygame.mixer.Sound(file_name)
    else:
        print(f"WARNING: Fail {file_name} belum ada dalam folder ini.")

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
current_chord = "Ndiak ada"
right_hand_prev_y = None
strum_line_y = 0 
is_strumming = False

print("Menyalakan kamera...")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    strum_line_y = int(h / 2)
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            
            wrist_x = hand_landmarks.landmark[0].x

            if wrist_x < 0.5: 
                fingers_up = 0
                
                thumb_tip = hand_landmarks.landmark[4] 
                index_base = hand_landmarks.landmark[5] 
                pinky_base = hand_landmarks.landmark[17] 
                
                is_thumb_open = False
                
                if index_base.x > pinky_base.x:
                    if thumb_tip.x > index_base.x:
                        is_thumb_open = True
                else:
                    if thumb_tip.x < index_base.x:
                        is_thumb_open = True

                if is_thumb_open:
                    fingers_up += 1
                    cv2.circle(frame, (int(thumb_tip.x * w), int(thumb_tip.y * h)), 10, (0, 255, 0), cv2.FILLED)

                tips_other = [8, 12, 16, 20]   
                bases_other = [6, 10, 14, 18] 
                
                for i in range(4):
                    if hand_landmarks.landmark[tips_other[i]].y < hand_landmarks.landmark[bases_other[i]].y:
                        fingers_up += 1
                        cv2.circle(frame, (int(hand_landmarks.landmark[tips_other[i]].x * w), int(hand_landmarks.landmark[tips_other[i]].y * h)), 10, (0, 255, 0), cv2.FILLED)

                cv2.putText(frame, f"Jumlah Jari: {fingers_up}", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                if fingers_up == 0: current_chord = "Ndiak ada"
                elif fingers_up == 1: current_chord = "C"
                elif fingers_up == 2: current_chord = "Dm"
                elif fingers_up == 3: current_chord = "Am"
                elif fingers_up == 4: current_chord = "F"
                elif fingers_up == 5: current_chord = "G"
            
            else: 
                index_finger_y = int(hand_landmarks.landmark[8].y * h)
                cv2.circle(frame, (int(hand_landmarks.landmark[8].x * w), index_finger_y), 15, (0, 255, 255), cv2.FILLED)

                if right_hand_prev_y is not None:
                    if (right_hand_prev_y < strum_line_y and index_finger_y >= strum_line_y) or \
                       (right_hand_prev_y > strum_line_y and index_finger_y <= strum_line_y):
                        
                        is_strumming = True
                        if current_chord in chord_sounds:
                            channel = pygame.mixer.find_channel(True)
                            if channel:
                                channel.play(chord_sounds[current_chord])
                    else:
                        is_strumming = False
                
                right_hand_prev_y = index_finger_y

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    line_color = (0, 255, 0) if is_strumming else (0, 0, 255)
    cv2.line(frame, (0, strum_line_y), (w, strum_line_y), line_color, 3)
    
    cv2.putText(frame, f"CHORD: {current_chord}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 0), 3)
    cv2.putText(frame, "(1=C, 2=Dm, 3=Am, 4=F, 5=G)", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

    cv2.imshow("Hand Guitar Boloku", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pygame.quit()
