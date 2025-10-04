import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, Tuple, Dict, Any
import base64
from io import BytesIO
from PIL import Image

class ThumbGestureDetector:
    def __init__(self):
        """Initialize MediaPipe hands solution for thumb gesture detection"""
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,  # Lowered for easier detection
            min_tracking_confidence=0.5,  # Lowered for better tracking
            model_complexity=1
        )
        
    def detect_thumb_gesture(self, landmarks) -> Optional[str]:
        """
        Detect thumb up/down gesture from hand landmarks
        
        Args:
            landmarks: MediaPipe hand landmarks
            
        Returns:
            'positive' for thumbs up, 'negative' for thumbs down, None for no gesture
        """
        if not landmarks:
            return None
            
        # Get key landmarks
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        thumb_mcp = landmarks[2]
        
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        
        wrist = landmarks[0]
        
        # Simple thumb extension check
        thumb_extension = np.sqrt(
            (thumb_tip['x'] - thumb_mcp['x'])**2 + 
            (thumb_tip['y'] - thumb_mcp['y'])**2
        )
        
        # Check if thumb is extended enough
        is_thumb_extended = thumb_extension > 0.03
        
        if not is_thumb_extended:
            return None
            
        # Simple thumbs up/down detection
        avg_finger_tip_y = (index_tip['y'] + middle_tip['y'] + ring_tip['y'] + pinky_tip['y']) / 4
        thumb_to_fingers_y = thumb_tip['y'] - avg_finger_tip_y
        thumb_to_wrist_y = thumb_tip['y'] - wrist['y']
        
        # Thumbs up: thumb tip is above other fingers
        if thumb_to_fingers_y < -0.05 and thumb_to_wrist_y < -0.03:
            return 'positive'
        # Thumbs down: thumb tip is below other fingers
        elif thumb_to_fingers_y > 0.05 and thumb_to_wrist_y > 0.03:
            return 'negative'
            
        return None
    
    def process_frame(self, frame_data: str) -> Dict[str, Any]:
        """
        Process a base64 encoded image frame and detect thumb gestures
        
        Args:
            frame_data: Base64 encoded image data
            
        Returns:
            Dictionary with detection results
        """
        try:
            # Decode base64 image
            image_data = base64.b64decode(frame_data.split(',')[1])
            image = Image.open(BytesIO(image_data))
            
            # Convert PIL to OpenCV format
            frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Process with MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            detection_result = {
                'gesture': None,
                'landmarks': None,
                'debug_info': {},
                'error': None,
                'hands_detected': False
            }
            
            if results.multi_hand_landmarks:
                detection_result['hands_detected'] = True
                
                for landmarks in results.multi_hand_landmarks:
                    # Convert landmarks to list format
                    landmarks_list = []
                    for landmark in landmarks.landmark:
                        landmarks_list.append({
                            'x': landmark.x,
                            'y': landmark.y,
                            'z': landmark.z
                        })
                    
                    # Detect gesture
                    gesture = self.detect_thumb_gesture(landmarks_list)
                    
                    if gesture:
                        detection_result['gesture'] = gesture
                        detection_result['landmarks'] = landmarks_list
                        
                        # Add debug information
                        thumb_tip = landmarks_list[4]
                        thumb_mcp = landmarks_list[2]
                        index_tip = landmarks_list[8]
                        middle_tip = landmarks_list[12]
                        ring_tip = landmarks_list[16]
                        pinky_tip = landmarks_list[20]
                        wrist = landmarks_list[0]
                        
                        thumb_extension = np.sqrt(
                            (thumb_tip['x'] - thumb_mcp['x'])**2 + 
                            (thumb_tip['y'] - thumb_mcp['y'])**2
                        )
                        
                        avg_finger_tip_y = (index_tip['y'] + middle_tip['y'] + ring_tip['y'] + pinky_tip['y']) / 4
                        thumb_to_fingers_y = thumb_tip['y'] - avg_finger_tip_y
                        thumb_to_wrist_y = thumb_tip['y'] - wrist['y']
                        
                        detection_result['debug_info'] = {
                            'thumb_extension': float(thumb_extension),
                            'thumb_to_fingers_y': float(thumb_to_fingers_y),
                            'thumb_to_wrist_y': float(thumb_to_wrist_y),
                            'is_thumb_extended': bool(thumb_extension > 0.03)
                        }
                        break
            else:
                detection_result['error'] = 'No hands detected'
            
            return detection_result
            
        except Exception as e:
            return {
                'gesture': None,
                'landmarks': None,
                'debug_info': {},
                'error': str(e),
                'hands_detected': False
            }
    
    def close(self):
        """Close MediaPipe hands solution"""
        self.hands.close()

# Global detector instance
detector = ThumbGestureDetector()