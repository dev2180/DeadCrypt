# DeadCrypt 🎞️

DeadCrypt is a Python-based tool that converts any file into a video of static-like RGB pixels, inspired by the classic TV "no signal" static. The project also allows you to decode the video back into the original file, effectively creating a simple **file-to-video encoder-decoder system**.

---

## Features
- Encode any file into a video with static-like frames.
- Decode videos back to the original file to ensure data integrity.
- Supports multiple YouTube-standard resolutions.
- Lossless encoding using **FFmpeg (FFV1 codec)**.
- Automatic creation of `encoded` and `decoded` folders for organized file storage.

---

## Installation

1. **Clone the repository:**
```bash
git clone https://github.com/<your-username>/DeadCrypt.git
cd DeadCrypt

2. Install Python dependencies:
pip install -r requirements.txt
3. Install FFmpeg (required for video encoding/decoding):
Windows:
Download from https://ffmpeg.org/download.html
 and add it to your system PATH.



Usage
Step 1: Prepare folders

Make sure the following folders exist in the project directory:

encoded/   # Output folder for encoded videos
decoded/   # Output folder for decoded files
Step 2: Encode a file

Run the encoder:

python encoder.py


Enter the path of the file you want to encode.

Select the desired video resolution from the given options.

The encoded video will be saved in the encoded folder.

Step 3: Decode a file

Run the decoder:

python decoder.py


Choose the encoded video file from the encoded folder by selecting the number option.

The original file will be restored and saved in the decoded folder.
