import json
import time
import uuid as uuid_mod
from pathlib import Path

from videotrans.configure import config
from videotrans.process.audio_align import AudioAligner


def process_audio_align(uuid):
    """
    处理AI自动对齐任务
    
    Args:
        uuid: 任务ID
    """
    config.logger.info(f"开始处理音频对齐任务: {uuid}")
    
    try:
        # 获取任务信息
        task_info = None
        for task in config.audio_align_queue:
            if task.get('uuid') == uuid:
                task_info = task
                break
        
        if not task_info:
            config.logger.error(f"未找到对应的音频对齐任务: {uuid}")
            config.push_queue(uuid, json.dumps({
                "type": "audio_align_error",
                "msg": "未找到对应的音频对齐任务",
                "uuid": uuid
            }))
            return False
        
        # 创建音频对齐器
        aligner = AudioAligner()
        
        # 处理音频对齐
        success = aligner.process_video_with_alignment(task_info)
        
        if success:
            config.logger.info(f"音频对齐任务完成: {uuid}")
            config.push_queue(uuid, json.dumps({
                "type": "audio_align_complete",
                "msg": "音频对齐完成",
                "uuid": uuid
            }))
            return True
        else:
            config.logger.error(f"音频对齐任务失败: {uuid}")
            config.push_queue(uuid, json.dumps({
                "type": "audio_align_error",
                "msg": "音频对齐处理失败",
                "uuid": uuid
            }))
            return False
            
    except Exception as e:
        config.logger.error(f"音频对齐任务异常: {str(e)}")
        config.push_queue(uuid, json.dumps({
            "type": "audio_align_error",
            "msg": f"音频对齐处理异常: {str(e)}",
            "uuid": uuid
        }))
        return False


def start_audio_align_task(obj):
    """
    启动音频对齐任务
    
    Args:
        obj: 视频对象信息
    
    Returns:
        str: 任务ID
    """
    # 生成任务ID
    task_uuid = str(uuid_mod.uuid4())
    
    # 创建任务信息
    task_info = {
        "uuid": task_uuid,
        "target_dir": obj.get('target_dir'),
        "novideo_mp4": obj.get('novideo_mp4'),
        "target_mp3": obj.get('target_mp3'),
        "target_srt": obj.get('target_srt'),
        "source_mp3": obj.get('source_mp3'),
    }
    
    # 添加到任务队列
    config.audio_align_queue.append(task_info)
    
    # 推送任务开始消息
    config.push_queue(task_uuid, json.dumps({
        "type": "audio_align_start",
        "msg": "开始音频对齐处理",
        "uuid": task_uuid
    }))
    
    # 启动任务处理
    process_audio_align(task_uuid)
    
    return task_uuid 