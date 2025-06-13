# Video Translation and Voiceover Tool

This is a video translation and voiceover tool that can translate videos from one language into a specified language, automatically generating and adding subtitles and voiceovers in that language.

## Supported Features

Voice recognition supports `faster-whisper` model, `openai-whisper` model, `OpenAI SpeechToText API`, `GoogleSpeech`, and `Ali Chinese speech recognition model`.

Text translation supports `Microsoft Translator|Google Translate|Baidu Translate|Tencent Translate|ChatGPT|AzureAI|Gemini|DeepL|DeepLX|Offline Translation OTT`.

Text-to-speech synthesis supports `Microsoft Edge tts`, `Google tts`, `Azure AI TTS`, `Openai TTS`, `Elevenlabs TTS`, `Custom TTS server API`, `GPT-SoVITS`, and other voice synthesis engines.

Allows for the retention of background accompaniment music, etc. (based on uvr5).

Supported languages: Simplified and Traditional Chinese, English, Korean, Japanese, Russian, French, German, Italian, Spanish, Portuguese, Vietnamese, Thai, Arabic, Turkish, Hungarian, Hindi, Ukrainian, Kazakh, Indonesian, Malay, Czech, Polish, Dutch, Swedish, and other languages with automatic detection.

## Main Uses and Functions

**[Translate Video and Dubbing]** Translate the audio in a video into another language's dubbing and embed the subtitles in that language.

**[Audio or Video to Subtitles]** Convert human speech in audio or video files into text and export as srt subtitle files.

**[Subtitle Creation and Dubbing]** Create dubbing based on existing local srt subtitle files, supporting both single and batch subtitles.

**[Subtitle Translation]** Translate one or more srt subtitle files into subtitles in other languages.

**[Merge Video and Audio]** Batch merge video files and audio files.

**[Merge Video and Subtitles]** Batch merge video files and srt subtitle files.

**[Add Image Watermark to Video]** Batch embed image watermarks in video files.

**[Extract Audio from Video]** Separate a video into audio files and silent video.

**[Audio/Video Format Conversion]** Batch convert audio and video formats.

**[Edit Subtitles and Export Multiple Formats]** Support importing srt, vtt, ass format subtitles, editing and setting font styles, colors, etc., and exporting corresponding format subtitles.

**[Subtitle Format Conversion]** Batch convert subtitle files between srt/ass/vtt formats.

**[Download YouTube Videos]** Download videos from YouTube.

**[Voice and Background Music Separation]**

**[API Calls]** Support for voice synthesis, speech recognition, subtitle translation, and video translation interface calls.

## MacOS Source Code Deployment

0. Open a terminal window and execute the following commands one by one:

    > Make sure you have installed Homebrew before executing. If you have not installed Homebrew, you need to install it first.
    >
    > Execute the command to install Homebrew: `/bin/bash -c "$(curl -fsSL https://brew.sh/install.sh)"`
    >
    > After installation, execute: `eval $(brew --config)`
    >

    ```
    brew install libsndfile
    brew install ffmpeg
    brew install git
    brew install python@3.10
    ```

    Continue executing:

    ```
    export PATH="/usr/local/opt/python@3.10/bin:$PATH"
    source ~/.bash_profile 
    source ~/.zshrc
    ```

1. Create a folder without spaces or Chinese characters, then navigate to that folder in the terminal.
2. Download the source code and extract it to that folder.
3. Execute `cd extracted_folder_name`.
4. Continue with `python -m venv venv`.
5. Execute `source ./venv/bin/activate` and ensure the terminal prompt begins with `(venv)`. The following commands must ensure the terminal prompt starts with `(venv)`.
6. Execute `pip install -r requirements.txt`. If it fails, execute the following 2 commands to switch the pip mirror to Aliyun:

    ```
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
    pip config set install.trusted-host mirrors.aliyun.com
    ```

    Then re-execute. If failure still occurs after switching to the Aliyun source, try executing `pip install -r requirements.txt`.

7. Run `python sp.py` to open the software interface.

## Linux Source Code Deployment

0. For CentOS/RHEL series, execute the following commands in sequence to install python3.10:

```
sudo yum update
sudo yum groupinstall "Development Tools"
sudo yum install openssl-devel bzip2-devel libffi-devel
cd /tmp
wget https://www.python.org/ftp/python/3.10.4/Python-3.10.4.tgz
tar xzf Python-3.10.4.tgz
cd Python-3.10.4
./configure — enable-optimizations
sudo make && sudo make install
sudo alternatives — install /usr/bin/python3 python3 /usr/local/bin/python3.10 1
sudo yum install -y ffmpeg
```

1. For Ubuntu/Debian series, execute the following commands to install python3.10:

```
apt update && apt upgrade -y
apt install software-properties-common -y
add-apt-repository ppa:deadsnakes/ppa
apt update
sudo apt-get install libxcb-cursor0
apt install python3.10
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
sudo update-alternatives --install /usr/bin/python python /usr/local/bin/python3.10 1
sudo update-alternatives --config python
apt-get install ffmpeg
```

**Open any terminal and execute `python3 -V`. If the output is "3.10.4", it means the installation was successful; otherwise, it was not successful.**

2. Create a folder without spaces or Chinese characters, then navigate to that folder from the terminal.
3. Download the source code and extract it to that folder.
4. Execute `cd extracted_folder_name`.
5. Execute `python -m venv venv`.
6. Execute `source ./venv/bin/activate` and ensure the terminal prompt begins with `(venv)`. The following commands must ensure the terminal prompt starts with `(venv)`.
7. Execute `pip install -r requirements.txt`. If it fails, execute the following 2 commands to switch the pip mirror to Aliyun:

    ```
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
    pip config set install.trusted-host mirrors.aliyun.com
    ```

    Then re-execute. If failure still occurs after switching to the Aliyun source, try executing `pip install -r requirements.txt`.

8. To use CUDA acceleration, execute separately:

    ```
    pip uninstall -y torch torchaudio
    pip install torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu118
    pip install nvidia-cublas-cu11 nvidia-cudnn-cu11
    ```

9. To enable CUDA acceleration on Linux, an Nvidia graphics card must be available, and the CUDA11.8+ environment must be properly set up.

10. Run `python sp.py` to open the software interface.

## Main Dependencies

1. ffmpeg
2. PySide6
3. edge-tts
4. faster-whisper
5. openai-whisper
6. pydub
