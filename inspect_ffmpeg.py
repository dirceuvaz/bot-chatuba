import sys
import os

try:
    import static_ffmpeg
    print("static_ffmpeg imported")
    print(f"Dir: {dir(static_ffmpeg)}")
    
    if hasattr(static_ffmpeg, 'run'):
        print(f"Run dir: {dir(static_ffmpeg.run)}")
    
    # Try to find where it is
    print(f"File: {static_ffmpeg.__file__}")
    
except ImportError:
    print("Could not import static_ffmpeg")
