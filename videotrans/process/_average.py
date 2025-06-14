import json
import os
import sys
import re
import tempfile
import time
from pathlib import Path

import torch
import zhconv
from faster_whisper import WhisperModel
from pydub import AudioSegment

from videotrans.util.tools import ms_to_time_string,  vail_file, cleartext


def run(raws, err,detect, *, model_name, is_cuda, detect_language, audio_file, q, settings,
        TEMP_DIR, ROOT_DIR, defaulelang,proxy=None):
    os.chdir(ROOT_DIR)

    def write_log(jsondata):
        try:
            q.put_nowait(jsondata)
        except:
            pass

    # 添加详细的调试信息
    write_log({"text": f"运行语音识别，平台: {os.name}, 系统: {sys.platform}", "type": "logs"})
    write_log({"text": f"音频文件: {audio_file}, 模型: {model_name}", "type": "logs"})
    
    # 检查音频文件是否存在
    if not Path(audio_file).exists():
        err_msg = f"错误: 音频文件不存在: {audio_file}"
        write_log({"text": err_msg, "type": "logs"})
        err['msg'] = err_msg
        return
    
    try:
        # 检查音频文件格式
        import wave
        try:
            with wave.open(audio_file, 'rb') as wf:
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                frame_rate = wf.getframerate()
                write_log({"text": f"音频信息: 通道数={channels}, 采样宽度={sample_width}, 采样率={frame_rate}", "type": "logs"})
        except Exception as e:
            write_log({"text": f"无法读取音频文件信息: {e}", "type": "logs"})
    except ImportError:
        write_log({"text": "wave模块导入失败", "type": "logs"})

    tmp_path = Path(tempfile.gettempdir()+f'/recogn_{time.time()}')
    tmp_path.mkdir(parents=True, exist_ok=True)
    tmp_path = tmp_path.as_posix()
    write_log({"text": f"临时目录: {tmp_path}", "type": "logs"})

    nonslient_file = f'{tmp_path}/detected_voice.json'
    try:
        normalized_sound = AudioSegment.from_wav(audio_file)
        write_log({"text": f"音频长度: {len(normalized_sound)}ms, 通道数: {normalized_sound.channels}, 采样率: {normalized_sound.frame_rate}", "type": "logs"})
    except Exception as e:
        err_msg = f"无法加载音频文件: {e}"
        write_log({"text": err_msg, "type": "logs"})
        err['msg'] = err_msg
        return
    
    if vail_file(nonslient_file):
        nonsilent_data = json.load(open(nonslient_file, 'r'))
    else:
        nonsilent_data = _shorten_voice_old(normalized_sound, settings)
        with open(nonslient_file, 'w') as f:
            f.write(json.dumps(nonsilent_data))
    
    write_log({"text": f"分段数量: {len(nonsilent_data)}", "type": "logs"})

    total_length = len(nonsilent_data)

    if model_name.startswith('distil-'):
        com_type = "default"
    elif is_cuda:
        com_type = settings['cuda_com_type']
    else:
        com_type = settings['cuda_com_type']
    # 如果不存在 / ，则是本地模型
    local_file_only = False #True if model_name.find('/') == -1 else False
    
    down_root = ROOT_DIR + "/models"
    msg = f'[{model_name}]若不存在将从 hf-mirror.com 下载到 models 目录内' if defaulelang == 'zh' else f'If [{model_name}] not exists, download model from huggingface'
    write_log({"text": msg, "type": "logs"})
    
    
    
    try:
        model = WhisperModel(
            model_name,
            device="cuda" if is_cuda else "cpu",
            compute_type=com_type,
            download_root=down_root,
            local_files_only=local_file_only)
    except Exception as e:
        if re.match(r'not support', str(e), re.I):
            model = WhisperModel(
                model_name,
                device="cuda" if is_cuda else "cpu",
                download_root=down_root,
                local_files_only=local_file_only)
        else:
            err['msg'] = str(e)
            return
    write_log({"text": model_name+" Loaded", "type": "logs"})
    prompt = settings.get(f'initial_prompt_{detect_language}') if detect_language!='auto' else None
    try:
        last_detect=detect_language
        for i, duration in enumerate(nonsilent_data):
            if not Path(TEMP_DIR + f'/{os.getpid()}.lock').exists():
                return
            start_time, end_time, buffered = duration
            chunk_filename = tmp_path + f"/c{i}_{start_time // 1000}_{end_time // 1000}.wav"
            audio_chunk = normalized_sound[start_time:end_time]
            audio_chunk.export(chunk_filename, format="wav")

            text = ""
            segments, info = model.transcribe(chunk_filename,
                                           beam_size=settings['beam_size'],
                                           best_of=settings['best_of'],
                                           condition_on_previous_text=settings[
                                               'condition_on_previous_text'],
                                           temperature=0.0 if settings['temperature'] == 0 else [0.0, 0.2,
                                                                                                 0.4,
                                                                                                 0.6, 0.8,
                                                                                                 1.0],
                                           vad_filter=False,
                                           language=detect_language[:2] if detect_language!='auto' else None,
                                           initial_prompt=prompt if prompt else None
                                           )
            if last_detect=='auto':
                detect['langcode']='zh-cn' if info.language[:2]=='zh' else info.language
                last_detect=detect['langcode']
            for t in segments:
                text += t.text + " "

            text = re.sub(r'&#\d+;', '', text.replace('&#39;', "'")).strip()

            if not text or re.match(r"^[^a-zA-Z]*$", text):
                continue

            if detect['langcode'][:2] == 'zh' and settings['zh_hant_s']:
                text = zhconv.convert(text, 'zh-hans')

            start = ms_to_time_string(ms=start_time)
            end = ms_to_time_string(ms=end_time)
            text=cleartext(text)
            srt_line = {
                "line": len(raws) + 1,
                "time": f"{start} --> {end}",
                "text": text,
                "start_time":start_time,
                "end_time":end_time,
                "startraw":start,
                "endraw":end
            }
            raws.append(srt_line)
            write_log({"text": f"{srt_line['line']}\n{srt_line['time']}\n{srt_line['text']}\n\n", "type": "subtitle"})
            write_log({"text": f" {srt_line['line']}/{total_length}", "type": "logs"})
    except (LookupError,ValueError,AttributeError,ArithmeticError) as e:
        err['msg']=f'{e}'
        if detect_language=='auto':
            err['msg']+='检测语言失败，请设置发声语言/Failed to detect language, please set the voice language'
    except BaseException as e:
        err['msg'] = str(e)
    finally:
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass


# split audio by silence
def _shorten_voice_old(normalized_sound, settings):
    max_interval = int(float(settings.get('interval_split',1))) * 1000
    nonsilent_data = []
    import math
    maxlen=math.ceil(len(normalized_sound)/max_interval)
    for i in range(maxlen):
        if i<maxlen-1:
            end_time=i*max_interval+max_interval
            start_time=i*max_interval
        else:
            end_time=len(normalized_sound)
            start_time=i*max_interval
        nonsilent_data.append((start_time, end_time, False))
    return nonsilent_data

