# 视频翻译配音工具

这是一个视频翻译配音工具，可将一种语言的视频翻译为指定语言的视频，自动生成和添加该语言的字幕和配音。并支持API调用。

## 支持的功能

语音识别支持 `faster-whisper`和`openai-whisper`本地离线模型 及 `OpenAI SpeechToText API`  `GoogleSpeech` `阿里中文语音识别模型`和豆包模型，并支持自定义语音识别api。

文字翻译支持 `微软翻译|Google翻译|百度翻译|腾讯翻译|ChatGPT|AzureAI|Gemini|DeepL|DeepLX|字节火山|离线翻译OTT`

文字合成语音支持 `Microsoft Edge tts` `Google tts` `Azure AI TTS` `Openai TTS` `Elevenlabs TTS` `自定义TTS服务器api` `GPT-SoVITS` 等多种语音合成引擎

允许保留背景伴奏音乐等(基于uvr5)

支持的语言：中文简繁、英语、韩语、日语、俄语、法语、德语、意大利语、西班牙语、葡萄牙语、越南语、泰国语、阿拉伯语、土耳其语、匈牙利语、印度语、乌克兰语、哈萨克语、印尼语、马来语、捷克语、波兰语、荷兰语、瑞典语/其他语言可选自动检测

## 主要用途和功能

【自动翻译视频并配音】将视频中的声音翻译为另一种语言的配音，并嵌入该语言字幕

【语音识别/将音频视频转为字幕】可批量将音频、视频文件中的人类说话声，识别为文字并导出为srt字幕文件

【语音合成/字幕配音】根据本地已有的srt字幕文件创建配音，支持单个或批量字幕

【翻译字幕文件】将一个或多个srt字幕文件翻译为其他语言的字幕文件

【合并视频和音频】批量将视频文件和音频文件一一对应合并

【合并视频和srt字幕】批量将视频文件srt字幕文件一一对应合并

【为视频添加图片水印】批量将视频文件中嵌入图片水印

【从视频中提取音频】从视频中分离为音频文件和无声视频

【音频视频格式转换】批量将音频视频进行格式转换

【字幕编辑并导出多格式】支持导入srt、vtt、ass格式字幕，编辑后可设置字体样式、色彩等导出对应格式字幕

【字幕格式转换】批量将字幕文件进行 srt/ass/vtt 格式互转

【下载油管视频】可从youtube上下载视频

【人声背景乐分离】

【API调用】支持 语音合成、语言识别、字幕翻译、视频翻译接口调用

## MacOS源码部署

0. 打开终端窗口，分别执行如下命令
	
	> 执行前确保已安装 Homebrew，如果你没有安装 Homebrew,那么需要先安装
	>
	> 执行命令安装 Homebrew：  `/bin/bash -c "$(curl -fsSL https://brew.sh/install.sh)"`
	>
	> 安装完成后，执行： `eval $(brew --config)`
	>

    ```
    brew install libsndfile
    brew install ffmpeg
    brew install git
    brew install python@3.10
    ```

    继续执行

    ```
    export PATH="/usr/local/opt/python@3.10/bin:$PATH"
    source ~/.bash_profile 
    source ~/.zshrc
    ```

1. 创建不含空格和中文的文件夹，在终端中进入该文件夹。
2. 下载源码并解压到该文件夹
3. 执行命令 `cd 解压后的文件夹名称`
4. 继续执行 `python -m venv venv`
5. 继续执行命令 `source ./venv/bin/activate`，执行完毕查看确认终端命令提示符已变成已`(venv)`开头,以下命令必须确定终端提示符是以`(venv)`开头
6. 执行 `pip install -r requirements.txt `，如果提示失败，执行如下2条命令切换pip镜像到阿里镜像

    ```
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
    pip config set install.trusted-host mirrors.aliyun.com
    ```

    然后重新执行
    如果已切换到阿里镜像源，仍提示失败，请尝试执行 `pip install -r requirements.txt`

7. `python sp.py` 打开软件界面

## Linux 源码部署

0. CentOS/RHEL系依次执行如下命令安装 python3.10

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

1. Ubuntu/Debian系执行如下命令安装python3.10

```
apt update && apt upgrade -y
apt install software-properties-common -y
add-apt-repository ppa:deadsnakes/ppa
apt update
sudo apt-get install libxcb-cursor0
apt install python3.10
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
sudo update-alternatives --install /usr/bin/python python /usr/local/bin/python3.10  1
sudo update-alternatives --config python
apt-get install ffmpeg
```

**打开任意一个终端，执行 `python3 -V`，如果显示 "3.10.4"，说明安装成功，否则失败**

1. 创建个不含空格和中文的文件夹， 从终端打开该文件夹。
2. 下载源码并解压到该文件夹
3. 继续执行命令 `cd 解压后的文件夹名称`
4. 继续执行 `python -m venv venv`
5. 继续执行命令 `source ./venv/bin/activate`，执行完毕查看确认终端命令提示符已变成已`(venv)`开头,以下命令必须确定终端提示符是以`(venv)`开头
6. 执行 `pip install -r requirements.txt`，如果提示失败，执行如下2条命令切换pip镜像到阿里镜像

    ```
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/
    pip config set install.trusted-host mirrors.aliyun.com
    ```

    然后重新执行,如果已切换到阿里镜像源，仍提示失败，请尝试执行 `pip install -r requirements.txt`

7. 如果要使用CUDA加速，分别执行

    `pip uninstall -y torch torchaudio`
    `pip install torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu118`
    `pip install nvidia-cublas-cu11 nvidia-cudnn-cu11`

8. linux 如果要启用cuda加速，必须有英伟达显卡，并且配置好了CUDA11.8+环境

9. `python sp.py` 打开软件界面

## 主要依赖项

1. ffmpeg
2. PySide6
3. edge-tts
4. faster-whisper
5. openai-whisper
6. pydub
