import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import time

def main():
    # Load the pre-trained model
    model_path = 'improved_emotion_recognition_model.h5'
    model = load_model(model_path)
    print(f"Model loaded successfully from {model_path}")
    
    # Define emotion labels (in the same order as training)
    emotion_labels = ['Anxiety', 'Anxiety', 'Anxiety', 'No Anxiety', 'Anxiety', 'Anxiety', 'No Anxiety']
    
    # Initialize webcam
    print("Starting webcam feed...")
    cap = cv2.VideoCapture(0)  # Use 0 for default camera
    
    # Check if camera opened successfully
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    # Load face cascade for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Performance metrics
    frame_count = 0
    start_time = time.time()
    fps = 0
    
    print("Press 'q' to quit")
    
    # Main loop for processing video frames
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image")
            break
            
        # Mirror the frame (so it feels like looking in a mirror)
        frame = cv2.flip(frame, 1)
        
        # Create a copy for display
        display_frame = frame.copy()
        
        # Convert to grayscale (model was trained on grayscale images)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces in the grayscale frame
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # Process each detected face
        for (x, y, w, h) in faces:
            # Draw rectangle around the face
            cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Extract face region
            face_roi = gray[y:y+h, x:x+w]
            
            # Resize to 48x48 (what the model expects)
            face_roi = cv2.resize(face_roi, (48, 48))
            
            # Normalize pixel values to [0, 1]
            face_roi = face_roi / 255.0
            
            # Reshape for model input (add batch and channel dimensions)
            face_roi = np.expand_dims(face_roi, axis=0)
            face_roi = np.expand_dims(face_roi, axis=-1)
            
            # Make prediction
            prediction = model.predict(face_roi, verbose=0)
            emotion_idx = np.argmax(prediction)
            emotion = emotion_labels[emotion_idx]
            confidence = float(prediction[0][emotion_idx]) * 100
            
            # Display the emotion and confidence
            label = f"{emotion}: {confidence:.1f}%"
            cv2.putText(display_frame, label, (x, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # # Display all emotion probabilities on the side
            # for i, (emo, prob) in enumerate(zip(emotion_labels, prediction[0])):
            #     bar_width = int(prob * 100)
            #     text = f"{emo}: {prob*100:.1f}%"
                
            #     # Select color (highlight the predicted emotion)
            #     color = (0, 255, 0) if i == emotion_idx else (255, 255, 255)
                
            #     # Draw the probability bar and text
            #     cv2.rectangle(display_frame, (10, 50 + i*30), (10 + bar_width, 70 + i*30), color, -1)
            #     cv2.putText(display_frame, text, (15 + bar_width, 65 + i*30), 
            #                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Calculate and display FPS
        frame_count += 1
        elapsed_time = time.time() - start_time
        if elapsed_time > 1:  # Update FPS every second
            fps = frame_count / elapsed_time
            frame_count = 0
            start_time = time.time()
        
        cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Display the frame with detections
        cv2.imshow('Emotion Recognition', display_frame)
        
        # Check for key press (q to quit)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release resources
    cap.release()
    cv2.destroyAllWindows()
    print("Application closed")

def test_time_augmentation(model, face_roi, num_augmentations=5):
    """
    Perform test-time augmentation to improve prediction accuracy.
    Returns the ensemble predictions.
    """
    predictions = []
    
    # Original prediction
    predictions.append(model.predict(face_roi, verbose=0))
    
    # Create slight variations of the image
    for i in range(1, num_augmentations):
        # Apply different augmentations
        aug_face = face_roi.copy()
        
        # Shift horizontally
        if i % 2 == 0:
            M = np.float32([[1, 0, 1], [0, 1, 0]])
            aug_face = cv2.warpAffine(aug_face[0, :, :, 0], M, (48, 48))
            aug_face = np.expand_dims(aug_face, axis=0)
            aug_face = np.expand_dims(aug_face, axis=-1)
        
        # Slight rotation
        else:
            M = cv2.getRotationMatrix2D((24, 24), 5 * (i-1), 1)
            aug_face = cv2.warpAffine(aug_face[0, :, :, 0], M, (48, 48))
            aug_face = np.expand_dims(aug_face, axis=0)
            aug_face = np.expand_dims(aug_face, axis=-1)
        
        # Predict on augmented image
        pred = model.predict(aug_face, verbose=0)
        predictions.append(pred)
    
    # Average predictions
    ensemble_pred = np.mean(predictions, axis=0)
    return ensemble_pred

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")