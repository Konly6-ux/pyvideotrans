import time
from threading import Thread

from videotrans.configure import config
from videotrans.task._base import BaseTask
from videotrans.util.tools import set_process


# 当前 uuid 是否已停止
def task_is_stop(uuid) -> bool:
    if uuid in config.stoped_uuid_set:
        return True
    return False


# 预处理线程，所有任务均需要执行，也是入口
"""
prepare_queue
regcon_queue
trans_queue
dubb_queue
audio_align_queue  # 新增AI自动对齐队列
align_queue
assemb_queue
"""


class WorkerPrepare(Thread):
    def __init__(self, *, parent=None):
        super().__init__()

    def run(self) -> None:
        while 1:
            if config.exit_soft:
                return
            if len(config.prepare_queue) < 1:
                time.sleep(0.5)
                continue
            try:
                trk: BaseTask = config.prepare_queue.pop(0)
            except:
                continue
            if task_is_stop(trk.uuid):
                continue
            try:

                trk.prepare()
                # 如果需要识别，则插入 recogn_queue队列，否则继续判断翻译队列、配音队列，都不吻合则插入最终队列
                if trk.shoud_recogn:
                    config.regcon_queue.append(trk)
                elif trk.shoud_trans:
                    config.trans_queue.append(trk)
                elif trk.shoud_dubbing:
                    config.dubb_queue.append(trk)
                else:
                    config.assemb_queue.append(trk)
            except Exception as e:
                config.logger.exception(e, exc_info=True)
                set_process(text=f'{config.transobj["yuchulichucuo"]}:' + str(e), type='error', uuid=trk.uuid)


class WorkerRegcon(Thread):
    def __init__(self, *, parent=None):
        super().__init__()

    def run(self) -> None:
        while 1:
            if config.exit_soft:
                return

            if len(config.regcon_queue) < 1:
                time.sleep(0.5)
                continue
            trk = config.regcon_queue.pop(0)
            if task_is_stop(trk.uuid):
                continue
            try:
                trk.recogn()
                # 如果需要识翻译,则插入翻译队列，否则就行判断配音队列，都不吻合则插入最终队列
                if trk.shoud_trans:
                    config.trans_queue.append(trk)
                elif trk.shoud_dubbing:
                    config.dubb_queue.append(trk)
                else:
                    config.assemb_queue.append(trk)
            except Exception as e:
                config.logger.exception(e, exc_info=True)
                set_process(text=f'{config.transobj["shibiechucuo"]}:' + str(e), type='error', uuid=trk.uuid)


class WorkerTrans(Thread):
    def __init__(self, *, parent=None):
        super().__init__()

    def run(self) -> None:
        while 1:
            if config.exit_soft:
                return
            if len(config.trans_queue) < 1:
                time.sleep(0.5)
                continue
            trk = config.trans_queue.pop(0)
            if task_is_stop(trk.uuid):
                continue
            try:
                trk.trans()
                # 如果需要配音，则插入 dubb_queue 队列，否则插入最终队列
                if trk.shoud_dubbing:
                    config.dubb_queue.append(trk)
                else:
                    config.assemb_queue.append(trk)
            except Exception as e:
                msg = f'{config.transobj["fanyichucuo"]}:' + str(e)
                config.logger.exception(e, exc_info=True)
                set_process(text=msg, type='error', uuid=trk.uuid)


class WorkerDubb(Thread):
    def __init__(self, *, parent=None):
        super().__init__()
        self.name = "配音处理线程"  # 设置线程名称

    def run(self) -> None:
        while 1:
            if config.exit_soft:
                return
            if len(config.dubb_queue) < 1:
                time.sleep(0.5)
                continue
            trk = config.dubb_queue.pop(0)
            if task_is_stop(trk.uuid):
                continue
            try:
                trk.dubbing()
                # 如果启用了AI自动对齐，则先进行音频对齐
                is_auto_align = config.params.get('auto_align', False)
                config.logger.info(f"任务{trk.uuid}配音完成，auto_align参数值: {is_auto_align}")
                
                if is_auto_align:
                    config.logger.info(f"任务{trk.uuid}将进入AI自动对齐队列")
                    # 确保audio_align_queue已初始化
                    if not hasattr(config, 'audio_align_queue'):
                        config.audio_align_queue = []
                    config.audio_align_queue.append(trk)
                else:
                    config.logger.info(f"任务{trk.uuid}将跳过AI自动对齐，直接进入对齐队列")
                    config.align_queue.append(trk)
            except Exception as e:
                msg = f'{config.transobj["peiyinchucuo"]}: {str(e)}'
                config.logger.exception(e, exc_info=True)
                set_process(text=msg, type='error', uuid=trk.uuid)


class WorkerAudioAlign(Thread):
    """AI自动对齐线程"""
    def __init__(self, *, parent=None):
        super().__init__()
        config.logger.info("AI自动对齐线程已初始化")
        self.name = "AI自动对齐线程"  # 设置线程名称

    def run(self) -> None:
        config.logger.info("AI自动对齐线程已启动")
        while 1:
            if config.exit_soft:
                config.logger.info("AI自动对齐线程退出")
                return
            if len(config.audio_align_queue) < 1:
                time.sleep(0.5)
                continue
                
            config.logger.info(f"AI自动对齐队列中有{len(config.audio_align_queue)}个任务")
            trk = config.audio_align_queue.pop(0)
            
            if task_is_stop(trk.uuid):
                config.logger.info(f"任务{trk.uuid}已停止，跳过AI自动对齐")
                continue
                
            try:
                config.logger.info(f"开始处理任务{trk.uuid}的AI自动对齐")
                # 检查auto_align参数是否已设置
                is_auto_align = config.params.get('auto_align', False)
                config.logger.info(f"auto_align参数值: {is_auto_align}")
                
                # 执行音频对齐
                trk.audio_align()
                
                config.logger.info(f"任务{trk.uuid}的AI自动对齐处理完成")
                config.align_queue.append(trk)
            except Exception as e:
                msg = f'AI自动对齐失败: {str(e)}'
                config.logger.exception(e, exc_info=True)
                set_process(text=msg, type='error', uuid=trk.uuid)


class WorkerAlign(Thread):
    def __init__(self, *, parent=None):
        super().__init__()

    def run(self) -> None:
        while 1:
            if config.exit_soft:
                return
            if len(config.align_queue) < 1:
                time.sleep(0.5)
                continue
            trk = config.align_queue.pop(0)
            if task_is_stop(trk.uuid):
                continue
            try:
                trk.align()
            except Exception as e:
                msg = f'{config.transobj["peiyinchucuo"]}:' + str(e)
                config.logger.exception(e, exc_info=True)
                set_process(text=msg, type='error', uuid=trk.uuid)
            else:
                config.assemb_queue.append(trk)


class WorkerAssemb(Thread):
    def __init__(self, *, parent=None):
        super().__init__()

    def run(self) -> None:
        while 1:
            if config.exit_soft:
                return
            if len(config.assemb_queue) < 1:
                time.sleep(0.5)
                continue
            trk = config.assemb_queue.pop(0)
            if task_is_stop(trk.uuid):
                continue
            try:
                trk.assembling()
                trk.task_done()
            except Exception as e:
                msg = f'{config.transobj["hebingchucuo"]}:' + str(e)
                config.logger.exception(e, exc_info=True)
                set_process(text=msg, type='error', uuid=trk.uuid)


def start_thread(parent=None):
    WorkerPrepare(parent=parent).start()
    WorkerRegcon(parent=parent).start()
    WorkerTrans(parent=parent).start()
    WorkerDubb(parent=parent).start()
    WorkerAudioAlign(parent=parent).start()  # 新增AI自动对齐线程
    WorkerAlign(parent=parent).start()
    WorkerAssemb(parent=parent).start()
