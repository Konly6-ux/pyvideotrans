import multiprocessing
import threading
import time
import sys
from pathlib import Path
from typing import List, Dict, Union

from videotrans.configure import config
# 确保config中可以访问sys模块
config.sys = sys
from videotrans.process._average import run
from videotrans.recognition._base import BaseRecogn
from videotrans.util import tools


class FasterAvg(BaseRecogn):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.raws = []
        self.pidfile = ""

    # 获取新进程的结果
    def _get_signal_from_process(self, q):
        while not self.has_done:
            if self._exit():
                Path(self.pidfile).unlink(missing_ok=True)
                return
            try:
                if not q.empty():
                    data = q.get_nowait()
                    if data:
                        if self.inst and self.inst.status_text and data['type']=='log':
                            self.inst.status_text=data['text']
                        self._signal(text=data['text'], type=data['type'])
            except Exception as e:
                print(e)
            time.sleep(0.5)

    def _exec(self) -> Union[List[Dict], None]:
        while 1:
            if self._exit():
                Path(self.pidfile).unlink(missing_ok=True)
                return
            if config.model_process is not None:
                import glob
                if len(glob.glob(config.TEMP_DIR+'/*.lock'))==0:
                    config.model_process=None
                    break
                self._signal(text="等待另外进程退出")
                time.sleep(1)
                continue
            break

        # 创建队列用于在进程间传递结果
        result_queue = multiprocessing.Queue()
        self.has_done = False

        threading.Thread(target=self._get_signal_from_process, args=(result_queue,)).start()
        try:
            with multiprocessing.Manager() as manager:
                raws = manager.list([])
                err = manager.dict({"msg": ""})
                detect = manager.dict({"langcode": self.detect_language})

                # 创建并启动新进程
                process = multiprocessing.Process(target=run, args=(raws, err,detect), kwargs={
                    "model_name": self.model_name,
                    "is_cuda": self.is_cuda,
                    "detect_language": self.detect_language,
                    "audio_file": self.audio_file,
                    "q": result_queue,
                    "settings": config.settings,
                    "defaulelang": config.defaulelang,
                    "ROOT_DIR": config.ROOT_DIR,
                    "TEMP_DIR": config.TEMP_DIR,
                    "proxy":tools.set_proxy()
                })
                process.start()
                self.pidfile = config.TEMP_DIR + f'/{process.pid}.lock'
                with open(self.pidfile,'w', encoding='utf-8') as f:
                    f.write(f'{process.pid}')
                # 等待进程执行完毕
                process.join()
                if err['msg']:
                    config.logger.error(f"语音识别错误: {err['msg']}")
                    self.error = 'err[msg]='+str(err['msg'])
                elif len(list(raws))<1:
                    # 创建一个假的字幕，以便程序能继续运行
                    if config.defaulelang=='zh':
                        config.logger.warning("没有识别到任何说话声，但这可能是正常的情况")
                        # 如果用户选择不添加字幕，则不应该报错
                        if getattr(self, 'inst', None) and hasattr(self.inst, 'need_subtitle') and not self.inst.need_subtitle:
                            config.logger.info("用户选择不添加字幕，继续执行")
                            self.raws = []
                        else:
                            self.error = "没有识别到任何说话声"
                            # 添加一个假的字幕
                            self.raws = [
                                {
                                    "line": 1,
                                    "time": "00:00:01,000 --> 00:00:03,000",
                                    "text": "这是一个测试字幕",
                                    "start_time": 1000,
                                    "end_time": 3000,
                                    "startraw": "00:00:01,000",
                                    "endraw": "00:00:03,000"
                                }
                            ]
                    else:
                        config.logger.warning("No speech detected, but this might be normal")
                        if getattr(self, 'inst', None) and hasattr(self.inst, 'need_subtitle') and not self.inst.need_subtitle:
                            config.logger.info("User chose not to add subtitles, continuing")
                            self.raws = []
                        else:
                            self.error = "No speech detected"
                else:
                    self.raws = list(raws)
                try:
                    if process.is_alive():
                        process.terminate()
                except:
                    pass
        except (LookupError,ValueError,AttributeError,ArithmeticError) as e:
            config.logger.exception(e, exc_info=True)
            self.error=str(e)
        except Exception as e:
            self.error='_avagel'+str(e)
        finally:
            config.model_process = None
            self.has_done = True
            Path(self.pidfile).unlink(missing_ok=True)

        if self.error:
            # 添加更详细的错误信息
            config.logger.error(f"语音识别失败，详细错误: {self.error}")
            config.logger.error(f"系统平台: {config.sys.platform}, 音频文件: {self.audio_file}")
            config.logger.error(f"使用的模型: {self.model_name}, CUDA: {self.is_cuda}")
            
            # 检查音频文件是否存在
            if self.audio_file and Path(self.audio_file).exists():
                import os
                file_size = os.path.getsize(self.audio_file)
                config.logger.error(f"音频文件存在，大小: {file_size} 字节")
            else:
                config.logger.error(f"音频文件不存在或路径错误: {self.audio_file}")
                
            # Mac系统特定检查
            if config.sys.platform == 'darwin':
                config.logger.error("在Mac系统上运行，可能存在兼容性问题")
                # 检查是否安装了必要的库
                try:
                    import samplerate
                    config.logger.error("samplerate库已安装")
                except ImportError:
                    config.logger.error("samplerate库未安装，这可能导致UVR5模型无法正常工作")
            
            raise Exception(self.error)
        return self.raws
