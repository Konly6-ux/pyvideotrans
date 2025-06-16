import multiprocessing
import sys, os
import time

from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QTimer, QPoint, QSettings, QSize
from PySide6.QtGui import QPixmap, QIcon, QGuiApplication

from videotrans import VERSION

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["OMP_NUM_THREADS"] = str(os.cpu_count())

class StartWindow(QtWidgets.QWidget):
    def __init__(self):
        super(StartWindow, self).__init__()
        self.width = 1200
        self.height = 700
        self.resize(560, 350)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
       
        self.label = QtWidgets.QLabel(self)
        self.pixmap = QPixmap("./videotrans/styles/logo.png")
        self.label.setPixmap(self.pixmap)
        self.label.setScaledContents(True)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(self.rect()) #直接设置几何形状覆盖

        self.setWindowIcon(QIcon("./videotrans/styles/icon.ico"))
        
        v1 = QtWidgets.QVBoxLayout()
        v1.addStretch(1)
        h1 = QtWidgets.QHBoxLayout()
        v1.addLayout(h1)
        v1.addStretch(0)
        h1.addStretch(1)
        self.lab = QtWidgets.QLabel()
        self.lab.setStyleSheet("""font-size:16px;color:#fff;text-align:center;background-color:transparent""")
        self.lab.setText(f"pyVideoTrans {VERSION} Loading...")
        h1.addWidget(self.lab)
        h1.addStretch(0)
        self.setLayout(v1)
        
        self.show()
        self.center()
        QTimer.singleShot(100, self.run)

    def run(self):
        # 创建并显示窗口B
        print(time.time())
        import videotrans.ui.dark.darkstyle_rc
        
        # 加载配置
        from videotrans.configure import config
        
        # 设置样式表
        try:
            # 使用主题系统
            from videotrans.styles.themes.theme_manager import ThemeManager
            theme_manager = ThemeManager(config.ROOT_DIR)
            
            # 加载当前主题样式
            style_sheet = theme_manager.get_theme_style()
            app.setStyleSheet(style_sheet)
        except Exception as e:
            import traceback
            print(f"加载主题时出错: {e}")
            print(traceback.format_exc())
            # 出错时使用默认样式
            try:
                with open('./videotrans/styles/style.qss', 'r', encoding='utf-8') as f:
                    app.setStyleSheet(f.read())
            except:
                pass
        
        # 确保音频AI自动对齐队列已初始化
        if not hasattr(config, 'audio_align_queue'):
            config.audio_align_queue = []
        
        try:
            from videotrans.mainwin._main_win import MainWindow
            sets=QSettings("pyvideotrans", "settings")
            w,h=int(self.width*0.85), int(self.height*0.85)
            size = sets.value("windowSize", QSize(w,h))
            try:
                w=size.width()
                h=size.height()
            except:
                pass
            config.MAINWIN=MainWindow(width=w, height=h)
            config.MAINWIN.move(QPoint(int((self.width - w) / 2), int((self.height - h) / 2)))
            
            # 确保音频对齐功能已正确加载
            self._ensure_audio_align_feature()
            
        except Exception as e:
            import traceback
            from PySide6.QtWidgets import QMessageBox
            msg=traceback.format_exc()
            if msg.find('torch._C')>0:
                QtWidgets.QMessageBox.critical(startwin,"Error",'因底层torch升级，请重新下载完整包' if config.defaulelang=='zh' else 'Please download the full package again')
            else:
                QtWidgets.QMessageBox.critical(startwin,"Error",msg)

        print(time.time())
        QTimer.singleShot(500, lambda :self.close())
    
    def _ensure_audio_align_feature(self):
        """确保AI自动对齐功能被正确加载"""
        from videotrans.configure import config
        import logging
        
        try:
            # 检查必要的库
            try:
                import librosa
                import soundfile
                config.logger.info("librosa和soundfile库已成功加载")
            except ImportError as e:
                config.logger.error(f"加载音频处理库失败: {str(e)}")
                return
            
            # 确保音频对齐处理模块存在
            try:
                from videotrans.process.audio_align import AudioAligner
                config.logger.info("AudioAligner模块已成功加载")
            except ImportError as e:
                config.logger.error(f"加载AudioAligner模块失败: {str(e)}")
                return
            
            # 确保任务处理线程已启动
            try:
                from videotrans.task.job import WorkerAudioAlign
                import threading
                
                for thread in threading.enumerate():
                    if isinstance(thread, WorkerAudioAlign):
                        config.logger.info("音频对齐线程已启动")
                        return
                
                # 如果线程未启动，尝试启动
                try:
                    from videotrans.task.job import start_thread
                    config.logger.info("启动音频对齐线程")
                except Exception as e:
                    config.logger.error(f"启动音频对齐线程失败: {str(e)}")
            except Exception as e:
                config.logger.error(f"检查音频对齐线程失败: {str(e)}")
        except Exception as e:
            config.logger.error(f"确保音频对齐功能时发生错误: {str(e)}")

    def center(self):
        screen = QGuiApplication.primaryScreen()
        screen_resolution = screen.geometry()
        self.width, self.height = screen_resolution.width(), screen_resolution.height()
        self.move(QPoint(int((self.width - 560) / 2), int((self.height - 350) / 2)))

if __name__ == "__main__":
    multiprocessing.freeze_support()  # Windows 上需要这个来避免子进程的递归执行问题
    try:
        QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except:
        pass

    # 导入必要的库
    import threading
    
    app = QtWidgets.QApplication(sys.argv)
    startwin = None
    try:
        startwin = StartWindow()
    except Exception as e:
        import traceback
        msg=traceback.format_exc()
        QtWidgets.QMessageBox.critical(startwin,"Error",msg)
    sys.exit(app.exec())
