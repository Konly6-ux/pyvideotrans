import os
import subprocess
import json
import numpy as np
import re
from pathlib import Path
import torch
import librosa
import soundfile as sf
from datetime import datetime
from videotrans.configure import config
from videotrans.util import tools

class AudioAligner:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() and config.params.get('cuda', False) else "cpu"
        
    def estimate_speech_duration(self, text, language="en", words_per_minute=150):
        """
        估算文本朗读时长（秒）
        
        Args:
            text: 文本内容
            language: 语言代码
            words_per_minute: 每分钟单词数（英语）或字符数（中文等）
        
        Returns:
            float: 估计的朗读时长（秒）
        """
        if language.startswith("zh"):
            # 中文按字符数计算
            char_count = len(re.sub(r'[^\u4e00-\u9fff]', '', text))
            # 中文每分钟约300字
            return char_count / 300 * 60
        elif language.startswith("en"):
            # 英文按单词数计算
            word_count = len(text.split())
            return word_count / words_per_minute * 60
        else:
            # 其他语言简单按字符数估算
            char_count = len(text)
            return char_count / 15
    
    def simplify_text(self, text, target_duration, current_estimated_duration, language="en"):
        """
        简化文本以缩短朗读时间
        
        Args:
            text: 原始文本
            target_duration: 目标时长（秒）
            current_estimated_duration: 当前估计时长（秒）
            language: 语言代码
        
        Returns:
            str: 简化后的文本
        """
        # 如果时长差异不大，直接返回原文
        if current_estimated_duration <= target_duration * 1.1:
            return text
            
        # 计算需要缩减的比例
        reduction_ratio = target_duration / current_estimated_duration
        
        # 简化策略
        simplified_text = text
        
        # 1. 移除冗余词汇和修饰语
        filler_words = {
            "en": [" very ", " really ", " actually ", " basically ", " literally ", " definitely ", 
                  " certainly ", " probably ", " honestly ", " truly ", " just ", " simply ", 
                  " in my opinion ", " I think ", " I believe ", " you know ", " I mean ", 
                  " kind of ", " sort of ", " like ", " well ", " so ", " then ", " anyway ", 
                  " in fact ", " as a matter of fact ", " for what it's worth ", " needless to say "],
            "zh": ["非常", "真的", "实际上", "基本上", "确实", "肯定", "当然", "可能", "老实说", 
                  "真正", "就是", "简单地说", "我认为", "我相信", "你知道", "我是说", 
                  "有点", "有些", "嗯", "那么", "然后", "总之", "事实上", "不用说"]
        }
        
        lang_key = "zh" if language.startswith("zh") else "en"
        for word in filler_words.get(lang_key, []):
            simplified_text = simplified_text.replace(word, " ")
        
        # 2. 使用更简洁的表达
        if lang_key == "en":
            # 英文简化替换
            replacements = {
                "in order to": "to",
                "due to the fact that": "because",
                "for the purpose of": "for",
                "in the event that": "if",
                "in spite of the fact that": "although",
                "with regard to": "about",
                "in reference to": "about",
                "with respect to": "about",
                "in relation to": "about",
                "concerning the matter of": "about",
                "it is important to note that": "",
                "it should be noted that": "",
                "it is worth noting that": "",
                "as a consequence of": "because",
                "as a result of": "from",
                "in the near future": "soon",
                "at this point in time": "now",
                "at the present time": "now",
                "in today's modern world": "today",
                "in today's society": "today"
            }
            
            for old, new in replacements.items():
                simplified_text = simplified_text.replace(old, new)
        
        elif lang_key == "zh":
            # 中文简化替换
            replacements = {
                "由于这个原因": "因为",
                "考虑到这一点": "因此",
                "在这种情况下": "此时",
                "从这个角度来看": "",
                "有鉴于此": "因此",
                "不言而喻": "",
                "毋庸置疑": "",
                "众所周知": "",
                "总而言之": "",
                "归根结底": "",
                "换句话说": "",
                "简而言之": "",
                "实事求是地讲": "",
                "客观来说": "",
                "坦率地说": "",
                "老实说": "",
                "说实话": "",
                "讲真的": "",
                "说白了": "",
                "我个人认为": "",
                "依我看来": "",
                "在我看来": ""
            }
            
            for old, new in replacements.items():
                simplified_text = simplified_text.replace(old, new)
        
        # 3. 如果仍然需要进一步简化，尝试缩短句子
        if self.estimate_speech_duration(simplified_text, language) > target_duration:
            # 分割成句子
            if lang_key == "en":
                sentences = re.split(r'(?<=[.!?])\s+', simplified_text)
            else:
                sentences = re.split(r'[。！？]', simplified_text)
            
            # 保留核心句子，去掉一些次要句子
            if len(sentences) > 2:
                # 保留大约70%的句子
                keep_count = max(1, int(len(sentences) * 0.7))
                simplified_text = " ".join(sentences[:keep_count])
                
                # 如果是英文，确保句尾有标点
                if lang_key == "en" and not simplified_text[-1] in ".!?":
                    simplified_text += "."
        
        return simplified_text.strip()
    
    def adjust_audio_speed(self, source_audio, target_duration, output_audio):
        """
        调整音频速度以匹配目标时长
        
        Args:
            source_audio: 需要调整的音频文件路径
            target_duration: 目标时长（秒）
            output_audio: 输出音频文件路径
        
        Returns:
            bool: 是否成功
        """
        try:
            # 加载源音频
            y_source, sr_source = librosa.load(source_audio, sr=None)
            source_duration = librosa.get_duration(y=y_source, sr=sr_source)
            
            if not target_duration or target_duration <= 0:
                config.logger.error("无效的目标时长")
                return False
                
            # 计算速度比例
            speed_ratio = source_duration / target_duration
            
            # 使用librosa进行时间拉伸
            if abs(speed_ratio - 1.0) > 0.01:  # 只有当比例差异大于1%时才调整
                config.logger.info(f"调整音频速度，原始时长: {source_duration:.2f}秒，目标时长: {target_duration:.2f}秒，比例: {speed_ratio:.2f}")
                
                # 限制最大加速比例，防止语音不自然
                if speed_ratio > 1.5:
                    speed_ratio = 1.5
                    config.logger.info(f"速度比例过大，限制为1.5倍速")
                
                y_adjusted = librosa.effects.time_stretch(y_source, rate=speed_ratio)
                sf.write(output_audio, y_adjusted, sr_source)
            else:
                # 如果几乎没有变化，直接复制
                sf.write(output_audio, y_source, sr_source)
                
            return True
            
        except Exception as e:
            config.logger.error(f"调整音频速度失败: {str(e)}")
            return False
    
    def parse_srt_time(self, time_str):
        """解析SRT时间字符串为秒数"""
        time_format = "%H:%M:%S,%f"
        time_obj = datetime.strptime(time_str, time_format)
        return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second + time_obj.microsecond / 1000000
    
    def get_subtitle_duration(self, subtitle_file):
        """获取字幕文件的总时长"""
        try:
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                subtitle_content = f.read()
            
            # 解析字幕文件，找出最后一个字幕的结束时间
            time_pattern = re.compile(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})')
            matches = time_pattern.findall(subtitle_content)
            
            if not matches:
                config.logger.error("无法解析字幕时间")
                return 0
                
            # 获取最后一个字幕的结束时间
            last_end_time_str = matches[-1][1]
            return self.parse_srt_time(last_end_time_str)
            
        except Exception as e:
            config.logger.error(f"获取字幕时长失败: {str(e)}")
            return 0
    
    def get_subtitle_text_map(self, subtitle_file):
        """获取字幕文件中的时间和文本映射"""
        try:
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                subtitle_content = f.read()
            
            # 解析字幕
            subtitle_blocks = re.split(r'\n\s*\n', subtitle_content.strip())
            subtitle_map = []
            
            for block in subtitle_blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    # 第一行是序号，第二行是时间，后面的是文本
                    time_line = lines[1]
                    text = '\n'.join(lines[2:])
                    
                    # 解析时间
                    time_match = re.match(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', time_line)
                    if time_match:
                        start_time = self.parse_srt_time(time_match.group(1))
                        end_time = self.parse_srt_time(time_match.group(2))
                        duration = end_time - start_time
                        
                        subtitle_map.append({
                            'start_time': start_time,
                            'end_time': end_time,
                            'duration': duration,
                            'text': text
                        })
            
            return subtitle_map
            
        except Exception as e:
            config.logger.error(f"解析字幕失败: {str(e)}")
            return []
    
    def simplify_subtitle(self, source_srt, target_srt, output_srt, target_language="en"):
        """简化字幕内容，使其更适合配音时长"""
        try:
            # 获取原始字幕和目标字幕的时间映射
            source_map = self.get_subtitle_text_map(source_srt)
            target_map = self.get_subtitle_text_map(target_srt)
            
            if not source_map or not target_map:
                config.logger.error("无法获取字幕映射")
                return False
            
            # 读取目标字幕文件
            with open(target_srt, 'r', encoding='utf-8') as f:
                target_content = f.read()
            
            # 对每个字幕块进行处理
            modified_content = target_content
            
            for i, target_item in enumerate(target_map):
                if i >= len(source_map):
                    break
                    
                source_item = source_map[i]
                target_text = target_item['text']
                
                # 估算当前文本的朗读时长
                estimated_duration = self.estimate_speech_duration(target_text, target_language)
                
                # 如果估算时长超过原字幕时长的1.2倍，则简化文本
                if estimated_duration > source_item['duration'] * 1.2:
                    simplified_text = self.simplify_text(
                        target_text, 
                        source_item['duration'],
                        estimated_duration,
                        target_language
                    )
                    
                    # 在字幕文件中替换文本
                    pattern = re.escape(target_text)
                    modified_content = re.sub(pattern, simplified_text, modified_content)
            
            # 写入简化后的字幕
            with open(output_srt, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            return True
            
        except Exception as e:
            config.logger.error(f"简化字幕失败: {str(e)}")
            return False
    
    def align_subtitles_with_audio(self, subtitle_file, audio_file, output_subtitle):
        """
        根据音频调整字幕时间
        
        Args:
            subtitle_file: 字幕文件路径
            audio_file: 音频文件路径
            output_subtitle: 输出字幕文件路径
            
        Returns:
            bool: 是否成功
        """
        try:
            # 获取音频时长
            y, sr = librosa.load(audio_file, sr=None)
            audio_duration = librosa.get_duration(y=y, sr=sr)
            
            # 读取字幕文件
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                subtitle_content = f.read()
            
            # 解析字幕文件，找出最后一个字幕的结束时间
            time_pattern = re.compile(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})')
            matches = time_pattern.findall(subtitle_content)
            
            if not matches:
                config.logger.error("无法解析字幕时间")
                return False
                
            # 获取最后一个字幕的结束时间
            last_end_time_str = matches[-1][1]
            time_format = "%H:%M:%S,%f"
            last_end_time = datetime.strptime(last_end_time_str, time_format)
            
            # 计算字幕总时长（秒）
            subtitle_duration = last_end_time.hour * 3600 + last_end_time.minute * 60 + last_end_time.second + last_end_time.microsecond / 1000000
            
            # 计算调整比例
            if subtitle_duration > 0:
                ratio = audio_duration / subtitle_duration
                
                # 如果比例接近1，不需要调整
                if 0.95 <= ratio <= 1.05:
                    import shutil
                    shutil.copy(subtitle_file, output_subtitle)
                    return True
                
                # 调整所有时间戳
                def adjust_time(time_str, ratio):
                    time_obj = datetime.strptime(time_str, time_format)
                    total_seconds = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second + time_obj.microsecond / 1000000
                    new_seconds = total_seconds * ratio
                    
                    hours = int(new_seconds // 3600)
                    minutes = int((new_seconds % 3600) // 60)
                    seconds = int(new_seconds % 60)
                    milliseconds = int((new_seconds - int(new_seconds)) * 1000)
                    
                    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
                
                # 替换所有时间戳
                adjusted_content = subtitle_content
                for start_time, end_time in matches:
                    new_start = adjust_time(start_time, ratio)
                    new_end = adjust_time(end_time, ratio)
                    adjusted_content = adjusted_content.replace(f"{start_time} --> {end_time}", f"{new_start} --> {new_end}")
                
                # 写入调整后的字幕
                with open(output_subtitle, 'w', encoding='utf-8') as f:
                    f.write(adjusted_content)
                
                return True
            else:
                config.logger.error("字幕时长为0")
                return False
                
        except Exception as e:
            config.logger.error(f"字幕对齐失败: {str(e)}")
            return False
    
    def process_video_with_alignment(self, video_obj):
        """
        处理视频，进行音频对齐
        
        Args:
            video_obj: 视频对象，包含处理信息
            
        Returns:
            bool: 是否成功
        """
        try:
            uuid = video_obj.get('uuid', '')
            target_dir = video_obj.get('target_dir', '')
            novideo_mp4 = video_obj.get('novideo_mp4', '')
            target_mp3 = video_obj.get('target_mp3', '')
            target_srt = video_obj.get('target_srt', '')
            source_mp3 = video_obj.get('source_mp3', '')
            source_srt = video_obj.get('source_srt', '')
            target_language = video_obj.get('target_language', 'en')
            
            if not all([uuid, target_dir, target_mp3]):
                config.logger.error(f"缺少必要的处理信息")
                return False
            
            # 创建临时文件路径
            temp_dir = Path(target_dir) / "temp_align"
            temp_dir.mkdir(exist_ok=True)
            
            simplified_subtitle = temp_dir / "simplified_subtitle.srt"
            aligned_audio = temp_dir / "aligned_audio.wav"
            aligned_subtitle = temp_dir / "aligned_subtitle.srt"
            
            # 1. 如果有原始字幕和目标字幕，先简化目标字幕内容
            if source_srt and Path(source_srt).exists() and target_srt and Path(target_srt).exists():
                config.logger.info(f"开始简化字幕: {target_srt}")
                success = self.simplify_subtitle(source_srt, target_srt, simplified_subtitle, target_language)
                if success:
                    # 备份原始字幕并替换
                    original_backup = Path(target_srt).with_suffix('.srt.original')
                    if not original_backup.exists():  # 只在第一次备份
                        Path(target_srt).rename(original_backup)
                    Path(simplified_subtitle).rename(target_srt)
                    config.logger.info(f"字幕简化完成: {target_srt}")
            
            # 2. 获取目标时长（原始音频或视频的时长）
            target_duration = 0
            if source_srt and Path(source_srt).exists():
                # 从原始字幕获取时长
                target_duration = self.get_subtitle_duration(source_srt)
                config.logger.info(f"从原始字幕获取的目标时长: {target_duration}秒")
            
            if target_duration <= 0 and source_mp3 and Path(source_mp3).exists():
                # 从原始音频获取时长
                y, sr = librosa.load(source_mp3, sr=None)
                target_duration = librosa.get_duration(y=y, sr=sr)
                config.logger.info(f"从原始音频获取的目标时长: {target_duration}秒")
            
            if target_duration <= 0 and novideo_mp4 and Path(novideo_mp4).exists():
                # 从视频获取时长
                target_duration = tools.get_video_duration(novideo_mp4)
                config.logger.info(f"从视频获取的目标时长: {target_duration}秒")
            
            if target_duration <= 0:
                config.logger.error("无法确定目标时长")
                return False
            
            # 3. 调整配音音频速度以匹配目标时长
            config.logger.info(f"开始对齐音频: {target_mp3}")
            success = self.adjust_audio_speed(target_mp3, target_duration, aligned_audio)
            
            if not success:
                config.logger.error(f"音频对齐失败")
                return False
            
            # 4. 如果有字幕，也对齐字幕
            if target_srt and Path(target_srt).exists():
                config.logger.info(f"开始对齐字幕: {target_srt}")
                success = self.align_subtitles_with_audio(target_srt, aligned_audio, aligned_subtitle)
                if success:
                    # 备份原始字幕并替换
                    original_backup = Path(target_srt).with_suffix('.srt.bak')
                    Path(target_srt).rename(original_backup)
                    Path(aligned_subtitle).rename(target_srt)
            
            # 5. 替换原始配音文件
            original_backup = Path(target_mp3).with_suffix('.mp3.bak')
            Path(target_mp3).rename(original_backup)
            Path(aligned_audio).rename(target_mp3)
            
            config.logger.info(f"音频对齐完成: {target_mp3}")
            return True
            
        except Exception as e:
            config.logger.error(f"处理视频对齐失败: {str(e)}")
            return False 