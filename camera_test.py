import subprocess
import time

def test_camera():
    filename = f"test_{int(time.time())}.jpg"
    print(f"Attempting to capture {filename} (with vertical flip)...")
    
    try:
        # Using rpicam-still directly with the vertical flip flag
        result = subprocess.run(
            ["rpicam-still", "-o", filename, "--nopreview", "-t", "1000", "--vflip"],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print(f"SUCCESS: Image saved as {filename}")
        else:
            print("CAMERA_ERROR: The rpicam-still command failed.")
            print("Error details:", result.stderr)
            
    except FileNotFoundError:
        print("CAMERA_ERROR: 'rpicam-still' command not found. Ensure rpicam-apps is installed.")
    except Exception as e:
        print(f"CAMERA_ERROR: An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_camera()
