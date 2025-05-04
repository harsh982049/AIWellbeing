import pandas as pd
import numpy as np
from datetime import datetime
import os
import re

# Function to read CSV files
def read_csv_file(file_path):
    return pd.read_csv(file_path)

# ================= PROCESSING USER CONDITION DATA =================
def process_user_condition_data(condition_data):
    print("Processing user condition data...")
    
    # Create binary stress label based on Stress_Val
    def create_stress_label(stress_val):
        high_stress = ['V_Stressed', 'S_Stressed']
        if stress_val in high_stress:
            return 1  # Stressed
        else:
            return 0  # Not stressed
    
    # Apply the function to create binary labels
    condition_data['stress_binary'] = condition_data['Stress_Val'].apply(create_stress_label)
    
    # Create datetime objects
    condition_data['datetime'] = pd.to_datetime(condition_data['Time'])
    
    # Group by SessionID
    condition_features = []
    
    for session_id, session_data in condition_data.groupby('SessionID'):
        # Calculate average values per session
        avg_pam = session_data['PAM_Val'].mean()
        
        # Calculate percentage of high stress reports
        stress_percentage = session_data['stress_binary'].mean() * 100
        
        # Calculate features related to energy and pleasantness
        energy_mapping = {
            'V_Low_Energy': 1, 
            'S_Low_Energy': 2, 
            'Neutral': 3, 
            'S_Energetic': 4, 
            'V_Energetic': 5
        }
        
        pleasant_mapping = {
            'V_Unpleasant': 1,
            'S_Unpleasant': 2,
            'Neutral': 3,
            'S_Pleasant': 4,
            'V_Pleasant': 5
        }
        
        fatigue_mapping = {
            'Low': 1,
            'Below_Avg': 2, 
            'Avg': 3,
            'Above_Avg': 4,
            'V_High': 5,
            'No': 0  # Assuming 'No' means no fatigue
        }
        
        # Convert categorical values to numerical
        session_data['energy_num'] = session_data['Energy_Val'].map(energy_mapping)
        session_data['pleasant_num'] = session_data['Pleasant_Val'].map(pleasant_mapping)
        session_data['fatigue_num'] = session_data['Fatigue_Val'].map(fatigue_mapping)
        
        # Calculate averages
        avg_energy = session_data['energy_num'].mean()
        avg_pleasant = session_data['pleasant_num'].mean()
        avg_fatigue = session_data['fatigue_num'].mean()
        
        # Calculate variability metrics
        energy_std = session_data['energy_num'].std()
        pleasant_std = session_data['pleasant_num'].std()
        fatigue_std = session_data['fatigue_num'].std()
        
        # Count time periods
        morning_count = sum(session_data['Daylight'] == 'Morning')
        afternoon_count = sum(session_data['Daylight'] == 'Afternoon')
        evening_count = sum(session_data['Daylight'] == 'Evening')
        
        # Determine overall session stress label (majority voting)
        overall_stress = 1 if stress_percentage >= 50 else 0
        
        # Create features dictionary
        session_features = {
            'session_id': session_id,
            'avg_pam': avg_pam,
            'stress_percentage': stress_percentage,
            'avg_energy': avg_energy,
            'avg_pleasant': avg_pleasant,
            'avg_fatigue': avg_fatigue,
            'energy_std': energy_std,
            'pleasant_std': pleasant_std,
            'fatigue_std': fatigue_std,
            'morning_count': morning_count,
            'afternoon_count': afternoon_count,
            'evening_count': evening_count,
            'stress_label': overall_stress
        }
        
        condition_features.append(session_features)
        if condition_features:
            print("User condition features extracted successfully.")
    
    return pd.DataFrame(condition_features)

# ================= PROCESSING KEYSTROKES DATA =================
def process_keystrokes_data(keystrokes_data):
    print("Processing keystrokes data...")
    
    # Create datetime objects for both press and release times
    keystrokes_data['press_datetime'] = pd.to_datetime(keystrokes_data['Press_Time'])
    keystrokes_data['release_datetime'] = pd.to_datetime(keystrokes_data['Relase_Time'])
    
    # Calculate key hold time (dwell time) in milliseconds
    keystrokes_data['dwell_time'] = (keystrokes_data['release_datetime'] - 
                                    keystrokes_data['press_datetime']).dt.total_seconds() * 1000
    
    # Filter out potential outliers in dwell time
    keystrokes_data = keystrokes_data[(keystrokes_data['dwell_time'] > 0) & 
                                     (keystrokes_data['dwell_time'] < 1000)]  # Max 1 second
    
    # Calculate flight time (time between releasing one key and pressing the next)
    keystrokes_data = keystrokes_data.sort_values(['SessionID', 'press_datetime'])
    keystrokes_data['next_press'] = keystrokes_data.groupby('SessionID')['press_datetime'].shift(-1)
    keystrokes_data['flight_time'] = (keystrokes_data['next_press'] - 
                                     keystrokes_data['release_datetime']).dt.total_seconds() * 1000
    
    # Filter out potential outliers in flight time
    keystrokes_data = keystrokes_data[(keystrokes_data['flight_time'] > 0) & 
                                     (keystrokes_data['flight_time'] < 5000)]  # Max 5 seconds
    
    # Group by SessionID
    keystroke_features = []
    
    for session_id, session_data in keystrokes_data.groupby('SessionID'):
        # Calculate features
        
        # Dwell time features
        avg_dwell = session_data['dwell_time'].mean()
        std_dwell = session_data['dwell_time'].std()
        min_dwell = session_data['dwell_time'].min()
        max_dwell = session_data['dwell_time'].max()
        median_dwell = session_data['dwell_time'].median()
        
        # Flight time features
        avg_flight = session_data['flight_time'].mean()
        std_flight = session_data['flight_time'].std()
        min_flight = session_data['flight_time'].min()
        max_flight = session_data['flight_time'].max()
        median_flight = session_data['flight_time'].median()
        
        # Key type analysis - counts of different key types
        total_keys = len(session_data)
        backspace_count = sum(session_data['Key'] == 'backspace')
        backspace_ratio = backspace_count / total_keys if total_keys > 0 else 0
        
        arrow_count = sum(session_data['Key'] == 'arrow_key')
        arrow_ratio = arrow_count / total_keys if total_keys > 0 else 0
        
        enter_count = sum(session_data['Key'] == 'enter')
        enter_ratio = enter_count / total_keys if total_keys > 0 else 0
        
        # Typing rhythm consistency
        dwell_time_consistency = session_data['dwell_time'].median() / session_data['dwell_time'].mean() if session_data['dwell_time'].mean() > 0 else 0
        
        # Typing speed volatility (coefficient of variation)
        typing_speed_volatility = session_data['flight_time'].std() / session_data['flight_time'].mean() if session_data['flight_time'].mean() > 0 else 0
        
        # Calculate typing rate (keystrokes per minute)
        if len(session_data) >= 2:
            session_duration = (session_data['press_datetime'].max() - 
                               session_data['press_datetime'].min()).total_seconds() / 60
            typing_rate = len(session_data) / session_duration if session_duration > 0 else 0
        else:
            typing_rate = 0
        
        # Create features dictionary
        session_features = {
            'session_id': session_id,
            'avg_dwell_time': avg_dwell,
            'std_dwell_time': std_dwell,
            'min_dwell_time': min_dwell,
            'max_dwell_time': max_dwell,
            'median_dwell_time': median_dwell,
            'avg_flight_time': avg_flight,
            'std_flight_time': std_flight,
            'min_flight_time': min_flight,
            'max_flight_time': max_flight,
            'median_flight_time': median_flight,
            'backspace_ratio': backspace_ratio,
            'arrow_key_ratio': arrow_ratio,
            'enter_key_ratio': enter_ratio,
            'dwell_time_consistency': dwell_time_consistency,
            'typing_speed_volatility': typing_speed_volatility,
            'typing_rate': typing_rate,
            'total_keystrokes': total_keys
        }
        
        if keystroke_features:
            print("Keystroke features extracted successfully.")
        
        keystroke_features.append(session_features)
    
    return pd.DataFrame(keystroke_features)

# ================= PROCESSING MOUSE MOVEMENT DATA =================
def process_mouse_data(mouse_data):
    print("Processing mouse movement data...")
    
    # Create datetime objects
    mouse_data['datetime'] = pd.to_datetime(mouse_data['Time'])
    
    mouse_data.rename(columns={"Speed(ms)": "Speed"}, inplace=True)

    # Convert Speed to float (in case it's a string)
    mouse_data['Speed'] = pd.to_numeric(mouse_data['Speed'], errors='coerce')
    
    # Group by SessionID
    mouse_features = []
    
    for session_id, session_data in mouse_data.groupby('SessionID'):
        # Basic speed statistics
        avg_speed = session_data['Speed'].mean()
        std_speed = session_data['Speed'].std()
        min_speed = session_data['Speed'].min()
        max_speed = session_data['Speed'].max()
        median_speed = session_data['Speed'].median()
        
        # Calculate acceleration (change in speed over time)
        session_data = session_data.sort_values('datetime')
        session_data['speed_diff'] = session_data['Speed'].diff()
        session_data['time_diff'] = session_data['datetime'].diff().dt.total_seconds()
        session_data['acceleration'] = session_data['speed_diff'] / session_data['time_diff']
        
        # Remove infinity and NaN values
        session_data = session_data[~session_data['acceleration'].isin([float('inf'), -float('inf'), float('nan')])]
        
        # Acceleration statistics
        if len(session_data) > 0:
            avg_acceleration = session_data['acceleration'].mean()
            std_acceleration = session_data['acceleration'].std()
            max_acceleration = session_data['acceleration'].max()
            min_acceleration = session_data['acceleration'].min()
        else:
            avg_acceleration = std_acceleration = max_acceleration = min_acceleration = 0
        
        # Calculate jerk (change in acceleration over time)
        session_data['acceleration_diff'] = session_data['acceleration'].diff()
        session_data['jerk'] = session_data['acceleration_diff'] / session_data['time_diff']
        
        # Remove infinity and NaN values for jerk
        session_data = session_data[~session_data['jerk'].isin([float('inf'), -float('inf'), float('nan')])]
        
        # Jerk statistics
        if len(session_data) > 0:
            avg_jerk = session_data['jerk'].mean()
            std_jerk = session_data['jerk'].std()
        else:
            avg_jerk = std_jerk = 0
            
        # Abrupt movements - count instances of high acceleration
        if std_acceleration > 0:
            high_accel_threshold = avg_acceleration + 2 * std_acceleration
            abrupt_movements = sum(session_data['acceleration'] > high_accel_threshold)
            abrupt_movement_ratio = abrupt_movements / len(session_data) if len(session_data) > 0 else 0
        else:
            abrupt_movements = 0
            abrupt_movement_ratio = 0
            
        # Movement consistency
        speed_consistency = median_speed / avg_speed if avg_speed > 0 else 0
        
        # Calculate mouse activity duration
        if len(session_data) >= 2:
            activity_duration = (session_data['datetime'].max() - 
                                session_data['datetime'].min()).total_seconds()
        else:
            activity_duration = 0
            
        # Movement density (movements per second)
        movement_density = len(session_data) / activity_duration if activity_duration > 0 else 0
        
        # Create features dictionary
        session_features = {
            'session_id': session_id,
            'avg_mouse_speed': avg_speed,
            'std_mouse_speed': std_speed,
            'min_mouse_speed': min_speed,
            'max_mouse_speed': max_speed,
            'median_mouse_speed': median_speed,
            'avg_mouse_acceleration': avg_acceleration,
            'std_mouse_acceleration': std_acceleration,
            'max_mouse_acceleration': max_acceleration,
            'min_mouse_acceleration': min_acceleration,
            'avg_mouse_jerk': avg_jerk,
            'std_mouse_jerk': std_jerk,
            'abrupt_movements': abrupt_movements,
            'abrupt_movement_ratio': abrupt_movement_ratio,
            'mouse_speed_consistency': speed_consistency,
            'mouse_activity_duration': activity_duration,
            'mouse_movement_density': movement_density
        }
        
        mouse_features.append(session_features)
    
    return pd.DataFrame(mouse_features)

# ================= COMBINING ALL FEATURES =================
def combine_features(condition_features, keystroke_features, mouse_features):
    print("Combining all features...")
    
    # Merge all features based on SessionID
    merged_df = condition_features.merge(
        keystroke_features, 
        how='left', 
        left_on='session_id', 
        right_on='session_id'
    )
    
    merged_df = merged_df.merge(
        mouse_features, 
        how='left', 
        left_on='session_id', 
        right_on='session_id'
    )
    
    # Fill NaN values with 0 (for sessions without keystroke or mouse data)
    merged_df = merged_df.fillna(0)
    
    # Drop session_id column
    final_dataset = merged_df.drop(columns=['session_id'])
    
    return final_dataset

# ================= MAIN FUNCTION =================
def main():
    try:
        # Read input files
        base_path = 'C:\\Users\\harsh\\OneDrive\\Desktop\\MajorProject'
        condition_data = read_csv_file(f'{base_path}\\usercondition_combined.csv')
        
        keystrokes_data = read_csv_file(f'{base_path}\\keystrokes_combined.csv')
            
        mouse_data = read_csv_file(f'{base_path}\\mouse_mov_speeds_combined.csv')
        
        # Process each dataset to extract features
        condition_features = process_user_condition_data(condition_data)
        keystroke_features = process_keystrokes_data(keystrokes_data)
        mouse_features = process_mouse_data(mouse_data)
        
        # Combine all features
        final_dataset = combine_features(condition_features, keystroke_features, mouse_features)
        
        # Save final dataset
        final_dataset.to_csv("stress_detection_features.csv", index=False)
        
        print("Processing complete. Final dataset saved as 'stress_detection_features.csv'")
        print(f"Dataset shape: {final_dataset.shape}")
        print("\nFeature columns:")
        for col in final_dataset.columns:
            print(f"- {col}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    main()