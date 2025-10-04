#!/usr/bin/env python3
"""
Test script to verify MediaPipe installation and basic hand detection
Run this to check if MediaPipe is working correctly
"""

import cv2
import mediapipe as mp
import numpy as np
import sys

def test_mediapipe():
    """Test basic MediaPipe hand detection"""
    print("Testing MediaPipe installation...")
    
    try:
        # Initialize MediaPipe
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        print("✅ MediaPipe initialized successfully")
        
        # Test with webcam
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Cannot open webcam")
            return False
            
        print("✅ Webcam opened successfully")
        print("Press 'q' to quit, 's' to test with current frame")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to read frame")
                break
                
            # Flip frame horizontally for selfie view
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process with MediaPipe
            results = hands.process(rgb_frame)
            
            # Draw results
            if results.multi_hand_landmarks:
                for landmarks in results.multi_hand_landmarks:
                    # Draw hand landmarks
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame, landmarks, mp_hands.HAND_CONNECTIONS
                    )
                
                cv2.putText(frame, "Hand Detected!", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "No Hand Detected", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            cv2.imshow('MediaPipe Test', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                print("Testing current frame...")
                if results.multi_hand_landmarks:
                    print("✅ Hand detected in current frame!")
                    landmarks = results.multi_hand_landmarks[0]
                    print(f"Number of landmarks: {len(landmarks.landmark)}")
                else:
                    print("❌ No hand detected in current frame")
        
        cap.release()
        cv2.destroyAllWindows()
        hands.close()
        
        print("✅ MediaPipe test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ MediaPipe test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("MediaPipe Hand Detection Test")
    print("=" * 40)
    
    success = test_mediapipe()
    
    if success:
        print("\n🎉 MediaPipe is working correctly!")
        print("You can now run the main application.")
    else:
        print("\n💥 MediaPipe test failed!")
        print("Please check your installation:")
        print("1. pip install mediapipe")
        print("2. pip install opencv-python")
        print("3. Make sure your camera is working")
    
    sys.exit(0 if success else 1)
