#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Amir Yazdani

import os
import time
import shutil
import traceback
import json
import uuid
from pathlib import Path
from typing import Dict

from videotrans.configure import config
from videotrans.configure._base import BaseCon
from videotrans.util import tools
from videotrans.util import set_process


class BaseTask(BaseCon):

    def __init__(self, cfg: Dict = None, obj: Dict = None):
        # 任务id
        super().__init__()
        # 配置信息
        self.cfg=cfg
        if obj:
            self.cfg.update(obj)
        # 名字规范化处理后，应该删除的
        self.shound_del_name=None
        if "uuid" in self.cfg and self.cfg['uuid']:
            self.uuid = self.cfg['uuid']

        # 进度
        self.precent = 1
        self.status_text = config.transobj['ing']
        # 存储处理好待配音信息
        self.queue_tts = []
        # 本次任务结束标识
        self.hasend = False


        # 预处理，prepare 全部需要
        self.shound_del = False
        # 是否需要语音识别
        self.shoud_recogn = False
        # 是否需要字幕翻译
        self.shoud_trans = False
        # 是否需要配音
        self.shoud_dubbing = False
        # 是否需要人声分离
        self.shoud_separate = False
        # 是否需要嵌入配音或字幕
        self.shoud_hebing = False
        # 最后一步hebing move_emd 全部需要


    # 预先处理，例如从视频中拆分音频、人声背景分离、转码等
    def prepare(self):
        pass


    # 语音识别创建原始语言字幕
    def recogn(self):
        pass

    # 将原始语言字幕翻译到目标语言字幕
    def trans(self):
        pass

    # 根据 queue_tts 进行配音
    def dubbing(self):
        pass

    # AI自动对齐配音和字幕
    def audio_align(self):
        """AI自动对齐配音和字幕"""
        from videotrans.process.audio_align import AudioAligner
        
        if self._exit():
            return
        
        self._signal(text=config.transobj.get('AI自动对齐中', 'AI Auto Aligning...'), type='update_process')
        config.logger.info(f"开始执行任务{self.uuid}的AI自动对齐")
        
        try:
            # 获取必要的文件路径
            target_dir = self.cfg.get('target_dir')
            novideo_mp4 = self.cfg.get('novideo_mp4')
            target_mp3 = self.cfg.get('target_mp3')
            target_srt = self.cfg.get('target_srt')
            source_mp3 = self.cfg.get('source_mp3')
            source_srt = self.cfg.get('source_srt')
            target_language = config.params.get('target_language', 'en')
            
            config.logger.info(f"任务{self.uuid}的文件路径: target_mp3={target_mp3}, source_mp3={source_mp3}, target_srt={target_srt}, source_srt={source_srt}")
            
            # 检查必要文件是否存在
            if not target_mp3 or not Path(target_mp3).exists():
                error_msg = f"目标音频文件不存在: {target_mp3}"
                config.logger.error(error_msg)
                self._signal(text=error_msg, type='error')
                return
                
            # 创建音频对齐器
            aligner = AudioAligner()
            config.logger.info(f"任务{self.uuid}的AudioAligner实例已创建")
            
            # 构建任务信息
            task_info = {
                "uuid": self.uuid,
                "target_dir": target_dir,
                "novideo_mp4": novideo_mp4,
                "target_mp3": target_mp3,
                "target_srt": target_srt,
                "source_mp3": source_mp3,
                "source_srt": source_srt,
                "target_language": target_language
            }
            
            # 处理音频对齐
            config.logger.info(f"开始处理任务{self.uuid}的音频对齐")
            success = aligner.process_video_with_alignment(task_info)
            
            if not success:
                error_msg = config.transobj.get('AI自动对齐失败', 'AI Auto Align Failed')
                config.logger.error(f"任务{self.uuid}的AI自动对齐失败")
                self._signal(text=error_msg, type='error')
            else:
                config.logger.info(f"任务{self.uuid}的AI自动对齐成功完成")
                
            self._signal(text=config.transobj.get('AI自动对齐完成', 'AI Auto Align Complete'), type='update_process')
            
        except Exception as e:
            error_msg = f"AI自动对齐异常: {str(e)}"
            config.logger.exception(f"任务{self.uuid}的{error_msg}", exc_info=True)
            self._signal(text=error_msg, type='error')

    # 配音加速、视频慢速对齐
    def align(self):
        pass

    # 视频、音频、字幕合并生成结果文件
    def assembling(self):
        pass

    # 删除临时文件，移动或复制，发送成功消息
    def task_done(self):
        pass

    # 字幕是否存在并且有效
    def _srt_vail(self, file):
        if not file:
            return False
        if not tools.vail_file(file):
            return False
        try:
            tools.get_subtitle_from_srt(file)
        except Exception:
            Path(file).unlink(missing_ok=True)
            return False
        return True

    # 删掉尺寸为0的无效文件
    def _unlink_size0(self, file):
        if not file:
            return
        p = Path(file)
        if p.exists() and p.stat().st_size == 0:
            p.unlink(missing_ok=True)

    # 保存字幕文件 到目标文件夹
    def _save_srt_target(self, srtstr, file):
        # 是字幕列表形式，重新组装
        try:
            tools.save_srt(srtstr, file)
        except Exception as e:
            raise
        self._signal(text=Path(file).read_text(encoding='utf-8'), type='replace_subtitle')
        return True


    def _check_target_sub(self,source_srt_list,target_srt_list):
        import re,copy

        if len(source_srt_list)==1 or len(target_srt_list)==1:
            target_srt_list[0]['line']=1
            return target_srt_list[:1]
        source_len=len(source_srt_list)
        target_len=len(target_srt_list)
        config.logger.info(f'{source_srt_list=}')
        config.logger.info(f'{target_srt_list=}')
        for i,it in enumerate(source_srt_list):
            tmp=copy.deepcopy(it)
            if i>target_len-1:
                # 超出目标字幕长度
                tmp['text']='  '
                print(f'#1 {i=}')
            elif re.sub(r'\D','',it['time']) == re.sub(r'\D','',target_srt_list[i]['time']):
                # 正常时间码相等
                tmp['text']=target_srt_list[i]['text']
                print(f'#2 {i=}')
            elif i==0 and source_srt_list[1]['time']==target_srt_list[1]['time']:
                # 下一行时间码相同
                tmp['text']=target_srt_list[i]['text']
                print(f'#3 {i=}')
            elif i==source_len-1 and source_srt_list[i-1]['time']==target_srt_list[i-1]['time']:
                # 上一行时间码相同
                tmp['text']=target_srt_list[i]['text']
                print(f'#4 {i=}')
            elif i>0 and i<source_len-1 and target_len>i+1 and  source_srt_list[i-1]['time']==target_srt_list[i-1]['time'] and source_srt_list[i+1]['time']==target_srt_list[i+1]['time']:
                # 上下两行时间码相同
                tmp['text']=target_srt_list[i]['text']
                print(f'#5 {i=}')
            else:
                print(f'#6 {i=}')
                # 其他情况清空目标字幕文字
                tmp['text']='  '
            if i > len(target_srt_list)-1:
                target_srt_list.append(tmp)
            else:
                target_srt_list[i]=tmp
        config.logger.info(f'chulihou,{target_srt_list=}')
        return target_srt_list

    # 完整流程判断是否需退出，子功能需重写
    def _exit(self):
        if config.exit_soft or config.current_status != 'ing':
            return True
        return False
