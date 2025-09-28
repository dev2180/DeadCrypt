import os
from PIL import Image
from tqdm import tqdm
import ffmpeg

def decode_video_to_file(video_path):
    # Ensure decoded folder exists
    os.makedirs("decoded", exist_ok=True)

    # Step 0: Extract metadata from filename
    base_name = os.path.basename(video_path).replace(".mkv", "")
    try:
        original_name, res_str, size_str = base_name.split("__")
        width, height = map(int, res_str.split("x"))
        file_size = int(size_str)
    except:
        print("Error: Video filename does not contain valid metadata!")
        return

    print(f"Decoding '{original_name}' with resolution {width}x{height}, file size {file_size} bytes")

    # Step 1: Extract frames from video
    print("Step 1: Extracting frames...")
    os.makedirs("temp_frames", exist_ok=True)
    (
        ffmpeg
        .input(video_path)
        .output("temp_frames/frame_%03d.png")
        .overwrite_output()
        .run()
    )
    frame_files = sorted(os.listdir("temp_frames"))
    print(f"{len(frame_files)} frames extracted.")

    # Step 2: Convert frames back to bytes
    print("Step 2: Reconstructing file from frames...")
    all_bytes = bytearray()
    for frame_file in tqdm(frame_files, desc="Decoding frames"):
        img = Image.open(os.path.join("temp_frames", frame_file))
        arr_bytes = img.tobytes()
        all_bytes.extend(arr_bytes)

    # Step 3: Trim to original file size to remove padding
    all_bytes = all_bytes[:file_size]

    # Step 4: Save recovered file
    recovered_path = os.path.join("decoded", original_name)
    with open(recovered_path, "wb") as f:
        f.write(all_bytes)
    print(f"Recovered file saved in 'decoded' folder as: {recovered_path}")

    # Step 5: Cleanup frames
    for frame_file in frame_files:
        os.remove(os.path.join("temp_frames", frame_file))
    os.rmdir("temp_frames")
    print("Decoding complete!\n")


if __name__ == "__main__":
    print("=== Video Decoder ===")

    # Ensure encoded folder exists
    os.makedirs("encoded", exist_ok=True)
    videos = [f for f in os.listdir("encoded") if f.endswith(".mkv")]
    if not videos:
        print("No videos found in 'encoded' folder!")
        exit(1)

    print("Available videos in 'encoded' folder:")
    for idx, v in enumerate(videos):
        print(f"{idx + 1}. {v}")

    choice = int(input("Select a video to decode (number): ")) - 1
    if choice < 0 or choice >= len(videos):
        print("Invalid selection!")
        exit(1)

    selected_video = os.path.join("encoded", videos[choice])
    decode_video_to_file(selected_video)
