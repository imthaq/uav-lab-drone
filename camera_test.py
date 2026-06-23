import subprocess
import time

def test_camera():
    filename = f"test_{int(time.time())}.jpg"
    print(f"Attempting to capture {filename}...")
    
    try:
        # '-t 1000' gives the sensor 1 second to warm up/focus
        result = subprocess.run(
            ["libcamera-jpeg", "-o", filename, "--nopreview", "-t", "1000"],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print(f"SUCCESS: Image saved as {filename}")
        else:
            print("CAMERA_ERROR: The command failed.")
            print("Error details:", result.stderr)
            
    except FileNotFoundError:
        print("CAMERA_ERROR: libcamera-jpeg command not found. Try replacing 'libcamera-jpeg' with 'rpicam-jpeg' in the script.")
    except Exception as e:
        print(f"CAMERA_ERROR: An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_camera()