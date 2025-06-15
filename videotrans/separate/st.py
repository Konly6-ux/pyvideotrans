import hashlib
import os
import traceback
import requests
import py7zr
import shutil
from pathlib import Path

import librosa
import soundfile as sf
import torch
from pydub import AudioSegment

from videotrans.configure import config

from videotrans.separate.vr import AudioPre


def download_uvr5_model():
    """下载UVR5模型文件"""
    model_dir = Path(config.ROOT_DIR) / "uvr5_weights"
    model_file = model_dir / "HP2.pth"
    model_params = model_dir / "modelparams" / "2band_44100_lofi.json"
    
    # 如果模型文件已存在，则不需要下载
    if model_file.exists() and model_params.exists():
        return True
        
    # 创建必要的目录
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "modelparams").mkdir(parents=True, exist_ok=True)
    (model_dir / "models").mkdir(parents=True, exist_ok=True)
    
    # 下载模型文件
    url = "https://github.com/jianchang512/stt/releases/download/0.0/uvr5-model.7z"
    temp_file = Path(config.TEMP_DIR) / "uvr5-model.7z"
    temp_extract_dir = Path(config.TEMP_DIR) / "uvr5_extract"
    
    try:
        print(f"正在下载UVR5模型文件，请稍候...")
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(temp_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # 先解压到临时目录
        print(f"正在解压UVR5模型文件...")
        # 确保临时解压目录存在并为空
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir)
        temp_extract_dir.mkdir(parents=True, exist_ok=True)
        
        with py7zr.SevenZipFile(temp_file, mode='r') as z:
            z.extractall(path=temp_extract_dir)
        
        # 移动文件到正确的位置
        extracted_model_dir = temp_extract_dir / "uvr5_weights"
        if extracted_model_dir.exists():
            # 复制所有.pth文件到模型目录
            for pth_file in extracted_model_dir.glob("*.pth"):
                shutil.copy2(pth_file, model_dir)
            
            # 复制modelparams目录下的文件
            extracted_params_dir = extracted_model_dir / "modelparams"
            if extracted_params_dir.exists():
                for param_file in extracted_params_dir.glob("*"):
                    shutil.copy2(param_file, model_dir / "modelparams")
        
        # 删除临时文件和目录
        temp_file.unlink(missing_ok=True)
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir)
            
        return True
    except Exception as e:
        print(f"下载UVR5模型文件失败: {str(e)}")
        return False


def uvr(*, model_name=None, save_root=None, inp_path=None, source="logs", uuid=None, percent=[0, 1]):
    infos = []
    try:
        # 检查模型文件是否存在，如果不存在则下载
        model_file = Path(config.ROOT_DIR) / "uvr5_weights" / f"{model_name}.pth"
        if not model_file.exists():
            download_success = download_uvr5_model()
            if not download_success:
                infos.append("模型文件下载失败，请手动下载UVR5模型文件")
                yield "\n".join(infos)
                return
        
        func = AudioPre
        pre_fun = func(
            agg=10,
            model_path=config.ROOT_DIR + f"/uvr5_weights/{model_name}.pth",
            device="cuda" if torch.cuda.is_available() else "cpu",
            is_half=False,
            source=source
        )
        done = 0
        try:
            y, sr = librosa.load(inp_path, sr=None)
            info = sf.info(inp_path)
            channels = info.channels
            need_reformat = 0
            pre_fun._path_audio_(
                inp_path,
                ins_root=save_root,
                uuid=uuid,
                percent=percent
            )
            done = 1
        except  Exception:
            traceback.print_exc()
    except:
        infos.append(traceback.format_exc())
        yield "\n".join(infos)
    finally:
        try:
            del pre_fun.model
            del pre_fun
        except Exception:
            traceback.print_exc()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    yield "\n".join(infos)


def convert_to_pure_eng_num(string):
    encoded_string = string.encode('utf-8')
    hasher = hashlib.md5()
    hasher.update(encoded_string)
    hex_digest = hasher.hexdigest()
    return hex_digest


def split_audio(file_path):
    audio = AudioSegment.from_wav(file_path)
    segment_length = 300
    try:
        segment_length = int(config.settings['bgm_split_time'])
    except Exception:
        pass
    output_folder = Path(config.TEMP_DIR) / "separate"
    output_folder.mkdir(parents=True, exist_ok=True)
    output_folder = output_folder.as_posix()

    total_length = len(audio)  # Total length in milliseconds
    segment_length_ms = segment_length * 1000  # Convert segment length to milliseconds
    segments = []

    for i in range(0, total_length, segment_length_ms):
        start = i
        end = min(i + segment_length_ms, total_length)
        segment = audio[start:end]
        segment_filename = os.path.join(output_folder, f"segment_{i // 1000}.wav")
        # 如果音频不是2通道，16kHz，则进行转换
        if segment.channels != 2:
            segment = segment.set_channels(2)
        if segment.frame_rate != 44100:
            segment = segment.set_frame_rate(44100)
        segment.export(segment_filename, format="wav")
        segments.append(segment_filename)

    return segments


def concatenate_audio(input_wav_list, out_wav):
    combined = AudioSegment.empty()
    for wav_file in input_wav_list:
        audio = AudioSegment.from_wav(wav_file)
        if audio.channels != 2:
            audio = audio.set_channels(2)
        if audio.frame_rate != 44100:
            audio = audio.set_frame_rate(44100)
        combined += audio

    combined.export(out_wav, format="wav")


# path 是需要保存vocal.wav的目录
def start(audio, path, source="logs", uuid=None):
    Path(path).mkdir(parents=True, exist_ok=True)
    reslist = split_audio(audio)
    vocal_list = []
    instr_list = []
    grouplen = len(reslist)
    per = round(1 / grouplen, 2)
    for i, audio_seg in enumerate(reslist):
        if config.exit_soft or (uuid in config.stoped_uuid_set):
            return
        audio_path = Path(audio_seg)
        path_dir = audio_path.parent / audio_path.stem
        path_dir.mkdir(parents=True, exist_ok=True)
        try:
            gr = uvr(model_name="HP2", save_root=path_dir.as_posix(), inp_path=Path(audio_seg).as_posix(),
                     source=source, uuid=uuid, percent=[i * per, per])
            print(next(gr))
            print(next(gr))
        except StopIteration:
            vocal_list.append((path_dir / 'vocal.wav').as_posix())
            instr_list.append((path_dir / 'instrument.wav').as_posix())
        except Exception as e:
            raise

    if len(vocal_list) < 1 or len(instr_list) < 1:
        raise Exception('separate bgm error')
    concatenate_audio(instr_list, Path(f"{path}/instrument.wav").as_posix())
    concatenate_audio(vocal_list, Path(f"{path}/vocal.wav").as_posix())
