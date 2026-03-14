import sys
import os
import subprocess
try:
    from PIL import Image
except ImportError:
    print("Installing Pillow...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

def convert_webp_to_mp4(input_path, output_path):
    print(f"[*] Extracting pristine frames from {input_path} using Pillow...")
    temp_dir = "promo_frames_tmp"
    os.makedirs(temp_dir, exist_ok=True)
    
    img = Image.open(input_path)
    frame_count = getattr(img, "n_frames", 1)
    print(f"[*] Found {frame_count} frames to process...")
    
    # We must explicitly define a solid RGB background (black) to composite transparency against.
    # Otherwise, WebP alpha accumulation causes the "glitching" effect between frames.
    for i in range(frame_count):
        img.seek(i)
        frame = img.copy()
        
        # Create a solid black background
        bg = Image.new("RGB", frame.size, (0, 0, 0))
        # Composite the frame (which may have alpha) onto the background
        if frame.mode in ('RGBA', 'LA') or (frame.mode == 'P' and 'transparency' in frame.info):
            bg.paste(frame, (0, 0), frame.convert('RGBA'))
        else:
            bg.paste(frame)
            
        bg.save(os.path.join(temp_dir, f"f_{i:04d}.png"), "PNG")
        
        if (i+1) % 50 == 0:
            print(f"    -> Extracted {i+1}/{frame_count}")
            
    print("[*] Frame extraction complete. Stitching MP4 with FFmpeg...")
    
    # Run FFmpeg to stitch
    cmd = [
        "ffmpeg", "-y", "-framerate", "25", 
        "-i", f"{temp_dir}/f_%04d.png", 
        "-c:v", "libx264", 
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", 
        "-pix_fmt", "yuv420p", 
        "-crf", "18", 
        "-preset", "slow", 
        output_path
    ]
    
    subprocess.run(cmd, check=True)
    print(f"[+] SUCCESS! pristine video generated at {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_promo.py <input.webp>")
        sys.exit(1)
    convert_webp_to_mp4(sys.argv[1], "neo_hack_promo_trailer.mp4")
