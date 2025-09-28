import os
import math
import numpy as np
from PIL import Image
from tqdm import tqdm
import ffmpeg

# Supported YouTube resolutions
RESOLUTIONS = {
    "1": ("426x240", 426, 240),
    "2": ("640x360", 640, 360),
    "3": ("854x480", 854, 480),
    "4": ("1280x720", 1280, 720),
    "5": ("1920x1080", 1920, 1080),
    "6": ("2560x1440", 2560, 1440),
    "7": ("3840x2160", 3840, 2160)
}

def encode_file_to_video(file_path):
    # Step 0: Ask user to select resolution
    print("Select video resolution (YouTube supported):")
    for k, (name, w, h) in RESOLUTIONS.items():
        bytes_per_frame = w*h*3
        mb_per_frame = bytes_per_frame / (1024*1024)
        print(f"{k}. {name} - approx {mb_per_frame:.2f} MB per frame")
    choice = input("Enter option number: ").strip()
    if choice not in RESOLUTIONS:
        print("Invalid choice, defaulting to 720p")
        choice = "4"
    res_name, frame_width, frame_height = RESOLUTIONS[choice]

    # Show capacity per frame
    bytes_per_frame = frame_width*frame_height*3
    mb_per_frame = bytes_per_frame / (1024*1024)
    gb_per_frame = mb_per_frame / 1024
    print(f"\nResolution {res_name} selected. Each frame can store ~{mb_per_frame:.2f} MB ({gb_per_frame:.4f} GB)")

    fps = 24  # YouTube standard maximum for normal videos
    print(f"Video FPS set to {fps}")

    # Ensure encoded folder exists
    os.makedirs("encoded", exist_ok=True)
    filename = os.path.basename(file_path)

    # Step 1: Read file
    print("\nStep 1: Reading file...")
    with open(file_path, "rb") as f:
        data = f.read()
    file_size = len(data)
    print(f"File size: {file_size} bytes ({file_size/1024/1024:.2f} MB)")

    # Step 2: Calculate number of frames
    num_frames = math.ceil(file_size / bytes_per_frame)
    print(f"Step 2: Frames needed: {num_frames}")

    # Step 3: Create frames
    print("Step 3: Creating frames...")
    frames = []
    for i in tqdm(range(num_frames), desc="Packing frames"):
        frame_data = data[i*bytes_per_frame:(i+1)*bytes_per_frame]
        if len(frame_data) < bytes_per_frame:
            frame_data += bytes([0]*(bytes_per_frame - len(frame_data)))  # padding
        arr = np.frombuffer(frame_data, dtype=np.uint8).reshape((frame_height, frame_width, 3))
        img = Image.fromarray(arr)
        frame_file = f"frame_{i:03d}.png"
        img.save(frame_file)
        frames.append(frame_file)

    # Step 4: Encode frames into video using FFV1 (lossless)
    output_video = os.path.join(
        "encoded",
        f"{filename}__{frame_width}x{frame_height}__{file_size}.mkv"
    )
    print(f"Step 4: Encoding frames into video at {fps} FPS...")
    (
        ffmpeg
        .input("frame_%03d.png", framerate=fps)
        .output(output_video, vcodec="ffv1")
        .overwrite_output()
        .run()
    )
    print(f"Video saved in 'encoded' folder as {output_video}")

    # Step 5: Cleanup temporary frames
    print("Step 5: Cleaning up temporary frames...")
    for frame_file in frames:
        os.remove(frame_file)
    print("Encoding complete!\n")


if __name__ == "__main__":
    print("=== File to Video Encoder ===")
    file_path = input("Enter path to the file to encode: ").strip()
    if not os.path.exists(file_path):
        print("Error: File does not exist!")
        exit(1)
    encode_file_to_video(file_path)
