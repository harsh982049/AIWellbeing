import time
import csv
import threading
import os
import signal
import psutil
import sys
from pynput import keyboard, mouse
from plyer import notification
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw

# -----------------------
# Global State Variables
# -----------------------
keystrokes = []
backspace_count = 0
mouse_movements = []
running = True
paused = False

# Process management
pid_file = "tracker_tray.pid"

# -----------------------
# Logging Setup
# -----------------------
log_file_path = "stress_log.csv"

# Create the log file if it doesn't exist
if not os.path.exists(log_file_path):
    with open(log_file_path, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "typing_speed", "backspace_rate", "mouse_jitter", "stress_status"])

# -----------------------
# Process Management
# -----------------------
def check_existing_process():
    """Check if another instance is running and terminate it if found"""
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Check if the process still exists
            if psutil.pid_exists(old_pid):
                try:
                    process = psutil.Process(old_pid)
                    if "python" in process.name().lower():
                        print(f"Terminating existing process with PID {old_pid}")
                        process.terminate()
                        process.wait(timeout=3)
                except Exception as e:
                    print(f"Error terminating existing process: {e}")
        except Exception as e:
            print(f"Error reading PID file: {e}")
    
    # Write current PID
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))

def cleanup():
    """Clean up resources before exiting"""
    if os.path.exists(pid_file):
        try:
            os.remove(pid_file)
        except:
            pass

# -----------------------
# Helper Functions
# -----------------------
def calculate_typing_speed():
    if len(keystrokes) < 2:
        return 0
    intervals = [t2 - t1 for t1, t2 in zip(keystrokes, keystrokes[1:]) if t2 - t1 < 5]
    return round(len(intervals) / (sum(intervals) + 1e-5), 2) if intervals else 0

def calculate_backspace_rate():
    total_keys = len(keystrokes)
    return round(backspace_count / total_keys, 2) if total_keys else 0

def calculate_mouse_jitter():
    if len(mouse_movements) < 2:
        return 0
    dist = 0
    for (x1, y1), (x2, y2) in zip(mouse_movements, mouse_movements[1:]):
        dist += ((x2 - x1)**2 + (y2 - y1)**2) ** 0.5
    return round(dist / len(mouse_movements), 2)

def detect_stress(typing_speed, backspace_rate, mouse_jitter):
    stressed = False
    reasons = []

    if typing_speed < 1.5:
        stressed = True
        reasons.append("low typing speed")
    if backspace_rate > 0.2:
        stressed = True
        reasons.append("high backspace rate")
    if mouse_jitter > 800:
        stressed = True
        reasons.append("mouse jittery movements")

    return ("STRESSED", ", ".join(reasons)) if stressed else ("CALM", "")

def show_popup(status, reason):
    message = "You're doing fine. Keep going!" if status == "CALM" else f"Stress detected: {reason}"
    try:
        notification.notify(
            title=f"Stress Status: {status}",
            message=message,
            timeout=5
        )
    except Exception as e:
        print(f"Notification error: {e}")

# -----------------------
# Event Handlers
# -----------------------
def on_press(key):
    if paused or not running:
        return
    global backspace_count
    keystrokes.append(time.time())
    if key == keyboard.Key.backspace:
        backspace_count += 1

def on_move(x, y):
    if paused or not running:
        return
    mouse_movements.append((x, y))
    if len(mouse_movements) > 100:
        mouse_movements.pop(0)

# -----------------------
# Main Tracking Logic
# -----------------------
def monitor_behavior():
    while running:
        if not paused and running:
            try:
                ts = calculate_typing_speed()
                br = calculate_backspace_rate()
                mj = calculate_mouse_jitter()
                status, reason = detect_stress(ts, br, mj)
                show_popup(status, reason)

                with open(log_file_path, mode='a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([time.time(), ts, br, mj, status])

                keystrokes.clear()
                mouse_movements.clear()
                global backspace_count
                backspace_count = 0
            except Exception as e:
                print(f"Error in monitor thread: {e}")

        time.sleep(30)
        
        # Break the loop if not running
        if not running:
            break

# -----------------------
# Tray Icon UI
# -----------------------
def create_image():
    image = Image.new('RGB', (64, 64), color='navy')
    draw = ImageDraw.Draw(image)
    draw.ellipse((16, 16, 48, 48), fill='gold')
    return image

def exit_application(icon):
    global running
    running = False
    icon.stop()
    
    # Stop listeners and other threads
    if keyboard_listener.is_alive():
        keyboard_listener.stop()
    if mouse_listener.is_alive():
        mouse_listener.stop()
    
    # Cleanup and exit the application
    cleanup()
    os._exit(0)  # Force exit to ensure all threads terminate

def on_quit(icon, item):
    exit_application(icon)

def on_pause(icon, item):
    global paused
    paused = True
    show_popup("Paused", "Tracking paused from tray")

def on_resume(icon, item):
    global paused
    paused = False
    show_popup("Resumed", "Tracking resumed")

# -----------------------
# Program Entrypoint
# -----------------------
if __name__ == '__main__':
    # Check for existing instances and terminate them
    check_existing_process()
    
    # Set up signal handlers for clean shutdown
    signal.signal(signal.SIGINT, lambda sig, frame: cleanup())
    signal.signal(signal.SIGTERM, lambda sig, frame: cleanup())
    
    # Start listeners
    keyboard_listener = keyboard.Listener(on_press=on_press)
    mouse_listener = mouse.Listener(on_move=on_move)
    keyboard_listener.start()
    mouse_listener.start()

    # Start tracking thread
    tracking_thread = threading.Thread(target=monitor_behavior, daemon=True)
    tracking_thread.start()

    # Create and run tray icon
    tray_icon = Icon("StressTracker")
    tray_icon.icon = create_image()
    tray_icon.menu = Menu(
        MenuItem("Pause Tracking", on_pause),
        MenuItem("Resume Tracking", on_resume),
        MenuItem("Quit", on_quit)
    )
    
    # Set handler to cleanup on exit
    tray_icon.run()
    
    # If we get here, the icon has stopped running
    running = False
    
    # Wait for threads to finish
    if tracking_thread.is_alive():
        tracking_thread.join(timeout=1)
    
    cleanup()