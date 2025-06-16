import platform

import threading
import time,os


from PySide6.QtCore import Qt, QTimer, QSettings, QEvent
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QMainWindow, QPushButton, QToolBar, QMenu, QWidget


from videotrans.configure import config


from videotrans.ui.en import Ui_MainWindow
from videotrans.ui.three_column_layout import ThreeColumnLayout
from videotrans.ui.theme_selector import ThemeSelector
from videotrans.styles.themes.theme_manager import ThemeManager
from videotrans.util import tools
from videotrans.mainwin._actions import WinAction
from videotrans import VERSION, recognition
from videotrans  import tts
from pathlib import Path



class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None, width=1200, height=650):
        super(MainWindow, self).__init__(parent)
        self.width = width
        self.height = height
        self.resize(width, height)
        self.win_action = None
        self.moshis = None
        self.target_dir=None
        self.app_mode = "biaozhun"
        # 当前所有可用角色列表
        self.current_rolelist = []

        self.setWindowIcon(QIcon(f"{config.ROOT_DIR}/videotrans/styles/icon.ico"))

        self.languagename = config.langnamelist
        
        # 初始化主题管理器
        self.theme_manager = ThemeManager(config.ROOT_DIR)
        
        # 设置原始UI
        self.setupUi(self)
        
        # 初始化UI数据
        self.initUI()
        
        # 应用当前主题
        self.apply_current_theme()
        
        # 应用三栏布局
        QTimer.singleShot(100, self.apply_three_column_layout)
        
        self.show()
        QTimer.singleShot(200, self._set_cache_set)
        QTimer.singleShot(300, self._start_subform)
        QTimer.singleShot(500, self._bindsignal)

    def apply_three_column_layout(self):
        """应用三栏布局"""
        try:
            self.three_column_layout = ThreeColumnLayout()
            self.three_column_layout.setupUi(self, self)
            
            # 连接主题选择动作信号
            self.three_column_layout.action_theme.triggered.connect(self.show_theme_selector)
        except Exception as e:
            import traceback
            print(f"应用三栏布局时出错: {e}")
            print(traceback.format_exc())
            
            # 出错时添加主题菜单到原始UI
            self.add_theme_menu_to_original_ui()
        
    def add_theme_menu_to_original_ui(self):
        """在原始UI上添加主题菜单"""
        try:
            # 创建主题菜单
            self.menu_theme = QMenu(self.menubar)
            self.menu_theme.setObjectName("menu_theme")
            self.menu_theme.setTitle("主题 / Theme")
            
            # 添加主题菜单到菜单栏
            self.menubar.addAction(self.menu_theme.menuAction())
            
            # 创建主题选择动作
            self.action_theme = QAction(self)
            self.action_theme.setObjectName("action_theme")
            self.action_theme.setText("选择主题 / Select Theme")
            self.action_theme.triggered.connect(self.show_theme_selector)
            
            # 添加主题选择动作到主题菜单
            self.menu_theme.addAction(self.action_theme)
        except Exception as e:
            print(f"添加主题菜单时出错: {e}")
        
    def apply_current_theme(self):
        """应用当前主题"""
        try:
            style_sheet = self.theme_manager.get_theme_style()
            self.setStyleSheet(style_sheet)
        except Exception as e:
            print(f"应用主题时出错: {e}")
        
    def show_theme_selector(self):
        """显示主题选择器对话框"""
        try:
            theme_selector = ThemeSelector(self.theme_manager, self)
            theme_selector.themeChanged.connect(self.on_theme_changed)
            theme_selector.exec()
        except Exception as e:
            print(f"显示主题选择器时出错: {e}")
        
    def on_theme_changed(self, theme_id):
        """当主题改变时的处理函数
        
        Args:
            theme_id: 主题ID
        """
        try:
            style_sheet = self.theme_manager.get_theme_style(theme_id)
            self.setStyleSheet(style_sheet)
        except Exception as e:
            print(f"更改主题时出错: {e}")

    def initUI(self):
        from videotrans.translator import TRANSLASTE_NAME_LIST
        self.toolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.source_language.addItems(self.languagename)
        self.target_language.addItems(["-"] + self.languagename[:-1])
        self.translate_type.addItems(TRANSLASTE_NAME_LIST)

        
        self.rawtitle = f"{config.transobj['softname']} {VERSION}  {'视频翻译工具' if config.defaulelang == 'zh' else 'Video Translation Tool'}"
        self.setWindowTitle(self.rawtitle)

        self.win_action = WinAction(self)
        self.win_action.tts_type_change(config.params['tts_type'])
        try:
            config.params['translate_type'] = int(config.params['translate_type'])
        except Exception:
            config.params['translate_type'] = 0
        self.translate_type.setCurrentIndex(config.params['translate_type'])

        if config.params['source_language'] and config.params['source_language'] in self.languagename:
            self.source_language.setCurrentText(config.params['source_language'])
        try:
            config.params['tts_type']=int(config.params['tts_type'])
        except:
            config.params['tts_type']=0

        self.tts_type.setCurrentIndex(config.params['tts_type'])
        self.voice_role.clear()
        if config.params['tts_type'] == tts.CLONE_VOICE_TTS:
            self.voice_role.addItems(config.params["clone_voicelist"])
            threading.Thread(target=tools.get_clone_role).start()
        elif config.params['tts_type'] == tts.CHATTTS:
            self.voice_role.addItems(['No'] + list(config.ChatTTS_voicelist))
        elif config.params['tts_type'] == tts.TTS_API:
            self.voice_role.addItems(config.params['ttsapi_voice_role'].strip().split(','))
        elif config.params['tts_type'] == tts.GPTSOVITS_TTS:
            rolelist = tools.get_gptsovits_role()
            self.voice_role.addItems(list(rolelist.keys()) if rolelist else ['GPT-SoVITS'])
        elif config.params['tts_type'] == tts.COSYVOICE_TTS:
            rolelist = tools.get_cosyvoice_role()
            self.voice_role.addItems(list(rolelist.keys()) if rolelist else ['clone'])
        elif config.params['tts_type'] == tts.F5_TTS:
            rolelist = tools.get_f5tts_role()
            self.voice_role.addItems(['clone']+list(rolelist.keys()) if rolelist else ['clone'])
        elif config.params['tts_type'] == tts.FISHTTS:
            rolelist = tools.get_fishtts_role()
            self.voice_role.addItems(list(rolelist.keys()) if rolelist else ['No'])
        elif config.params['tts_type'] == tts.ELEVENLABS_TTS:
            rolelist = tools.get_elevenlabs_role()
            self.voice_role.addItems(['No']+rolelist)
        elif config.params['tts_type'] == tts.OPENAI_TTS:
            rolelist = config.params.get('openaitts_role','')
            self.voice_role.addItems(['No']+rolelist.split(','))
        elif config.params['tts_type'] == tts.GEMINI_TTS:
            rolelist = config.params.get('gemini_ttsrole','')
            self.voice_role.addItems(['No']+rolelist.split(','))
        elif self.win_action.change_by_lang(config.params['tts_type']):
            self.voice_role.clear()

        if config.params['target_language'] and config.params['target_language'] in self.languagename:
            self.target_language.setCurrentText(config.params['target_language'])
            self.win_action.set_voice_role(config.params['target_language'])
            if config.params['voice_role'] and config.params['voice_role'] != 'No' and self.current_rolelist and  config.params['voice_role'] in self.current_rolelist:
                self.voice_role.setCurrentText(config.params['voice_role'])
                self.win_action.show_listen_btn(config.params['voice_role'])



        try:
            config.params['recogn_type'] = int(config.params['recogn_type'])
        except Exception:
            config.params['recogn_type'] = 0

        # 设置当前识别类型
        self.recogn_type.setCurrentIndex(config.params['recogn_type'])

        # 设置需要显示的模型
        self.model_name.clear()
        if config.params['recogn_type']==recognition.Deepgram:
            self.model_name.addItems(config.DEEPGRAM_MODEL)
            curr=config.DEEPGRAM_MODEL
        elif config.params['recogn_type']==recognition.FUNASR_CN:
            self.model_name.addItems(config.FUNASR_MODEL)
            curr=config.FUNASR_MODEL
        else:
            self.model_name.addItems(config.WHISPER_MODEL_LIST)
            curr=config.WHISPER_MODEL_LIST
        if config.params['model_name'] in curr:
            self.model_name.setCurrentText(config.params['model_name'])

        if config.params['recogn_type'] not in [recognition.FASTER_WHISPER,recognition.Faster_Whisper_XXL,recognition.OPENAI_WHISPER,recognition.FUNASR_CN,recognition.Deepgram]:
            self.model_name.setDisabled(True)
        else:
            self.model_name.setDisabled(False)

        self.moshis = {
            "biaozhun": self.action_biaozhun,
            "tiqu": self.action_tiquzimu,
            "peiyin": self.action_peiyin,
            "fanyisrt": self.action_fanyisrt,
            "vas": self.action_vas,
            "videoandaudio": self.action_videoandaudio
        }

        # 如果使用经典UI，则添加主题菜单
        if os.environ.get('PYVIDEOTRANS_CLASSIC_UI') == '1':
            self.add_theme_menu_to_original_ui()

    def _bindsignal(self):
        try:
            from videotrans.task.check_update import CheckUpdateWorker
            from videotrans.task.get_role_list import GetRoleWorker
            from videotrans.task.job import start_thread
            from videotrans.mainwin._signal import UUIDSignalThread
            update_role = GetRoleWorker(parent=self)
            update_role.start()
            self.check_update = CheckUpdateWorker(parent=self)
            self.check_update.start()

            uuid_signal = UUIDSignalThread(parent=self)
            uuid_signal.uito.connect(self.win_action.update_data)
            uuid_signal.start()
            start_thread(self)
        except Exception as e:
            print(e)

        # 绑定翻译和语言相关控件
        self.translate_type.currentIndexChanged.connect(self.win_action.set_translate_type)
        self.source_language.currentIndexChanged.connect(self.win_action.source_language_change)
        self.target_language.currentTextChanged.connect(self.win_action.set_voice_role)

        # 绑定TTS和语音相关控件
        self.tts_type.currentIndexChanged.connect(self.win_action.tts_type_change)
        self.voice_role.currentTextChanged.connect(self.win_action.show_listen_btn)

        # 绑定识别相关控件
        self.recogn_type.currentIndexChanged.connect(self.win_action.recogn_type_change)
        self.model_name.currentTextChanged.connect(self.win_action.check_model_name)
        self.split_type.currentIndexChanged.connect(self.win_action.check_split_type)

        # 绑定功能区域点击事件
        if hasattr(self, 'recognition_group'):
            self.recognition_group.mousePressEvent = lambda event: self.win_action.click_reglabel()
        
        if hasattr(self, 'dubbing_group'):
            self.dubbing_group.mousePressEvent = lambda event: self.win_action.click_tts_type()
            
        if hasattr(self, 'translation_group'):
            self.translation_group.mousePressEvent = lambda event: self.win_action.click_translate_type()
            
        if hasattr(self, 'subtitle_area'):
            self.subtitle_area.mousePressEvent = lambda event: self.win_action.click_subtitle()

        # 绑定其他按钮和控件
        self.proxy.textChanged.connect(self.win_action.change_proxy)
        self.import_sub.clicked.connect(self.win_action.import_sub_fun)
        self.startbtn.clicked.connect(self.win_action.check_start)
        self.btn_save_dir.clicked.connect(self.win_action.get_save_dir)
        self.btn_get_video.clicked.connect(self.win_action.get_mp4)
        self.stop_djs.clicked.connect(self.win_action.reset_timeid)
        self.continue_compos.clicked.connect(self.win_action.set_djs_timeout)
        self.listen_btn.clicked.connect(self.win_action.listen_voice_fun)
        
        # 删除所有点击文字跳转界面的功能
        from videotrans.util import tools
        
        # 只保留存在的操作
        self.action_about.triggered.connect(self.win_action.about)
        self.action_clearcache.triggered.connect(self.win_action.clearcache)
        self.aisendsrt.toggled.connect(self.checkbox_state_changed)
        Path(config.TEMP_DIR+'/stop_process.txt').unlink(missing_ok=True)

    def checkbox_state_changed(self, state):
        """复选框状态发生变化时触发的函数"""
        print(f'{state=},{Qt.CheckState.Checked=}')
        if state:
            print("Checkbox is checked")
            config.settings['aisendsrt']=True
        else:
            print("Checkbox is unchecked")
            config.settings['aisendsrt']=False


    def changeEvent(self, event):

        super().changeEvent(event)  # 确保父类的事件处理被调用
        if event.type() == QEvent.Type.ActivationChange:
            if self.isActiveWindow():  # 只有在窗口被激活时才执行
                # print("Window activated")
                self.aisendsrt.setChecked(config.settings.get('aisendsrt'))

    def closeEvent(self, event):
        config.exit_soft = True
        config.current_status='stop'
        try:
            with open(config.TEMP_DIR+'/stop_process.txt','w',encoding='utf-8') as f:
                f.write('stop')
        except:
            pass
        sets=QSettings("pyvideotrans", "settings")
        sets.setValue("windowSize", self.size())
        self.hide()
        try:
            for w in config.child_forms.values():
                if w and hasattr(w, 'close'):
                    w.hide()
                    w.close()
            if config.INFO_WIN['win']:
                config.INFO_WIN['win'].close()
        except Exception:
            pass
        time.sleep(3)
        from videotrans.util import tools
        print('等待所有进程退出...')
        try:
            tools.kill_ffmpeg_processes()
        except Exception:
            pass
        time.sleep(3)
        os.chdir(config.ROOT_DIR)
        tools._unlink_tmp()
        event.accept()

    def _start_subform(self):
        self.import_sub.setCursor(Qt.PointingHandCursor)
        self.model_name_help.setCursor(Qt.PointingHandCursor)
        self.stop_djs.setCursor(Qt.PointingHandCursor)
        self.continue_compos.setCursor(Qt.PointingHandCursor)
        self.startbtn.setCursor(Qt.PointingHandCursor)
        self.btn_get_video.setCursor(Qt.PointingHandCursor)
        self.btn_save_dir.setCursor(Qt.PointingHandCursor)
        self.listen_btn.setCursor(Qt.PointingHandCursor)
    
        from videotrans import winform

        self.action_biaozhun.triggered.connect(self.win_action.set_biaozhun)
        self.action_tiquzimu.triggered.connect(self.win_action.set_tiquzimu)
        self.action_peiyin.triggered.connect(self.win_action.set_peiyin)
        self.action_fanyisrt.triggered.connect(self.win_action.set_fanyisrt)
        self.action_vas.triggered.connect(self.win_action.set_vas)
        self.action_videoandaudio.triggered.connect(self.win_action.set_videoandaudio)
        
        Path(config.TEMP_DIR+'/stop_process.txt').unlink(missing_ok=True)

    # 设置各种默认值和设置文字 提示等
    def _set_cache_set(self):
        if platform.system() == 'Darwin':
            self.enable_cuda.setChecked(False)
            self.enable_cuda.hide()
        self.source_mp4.setAcceptDrops(True)

        self.stop_djs.setStyleSheet("""background-color:#148CD2;color:#ffffff""")
        self.proxy.setText(config.proxy)
        self.continue_compos.setToolTip(config.transobj['Click to start the next step immediately'])
        self.split_type.addItems([config.transobj['whisper_type_all'], config.transobj['whisper_type_avg']])

        self.subtitle_type.addItems(
            [
                config.transobj['nosubtitle'],
                config.transobj['embedsubtitle'],
                config.transobj['softsubtitle'],
                config.transobj['embedsubtitle2'],
                config.transobj['softsubtitle2']
            ])
        self.subtitle_type.setCurrentIndex(config.params['subtitle_type'])

        if config.params['recogn_type'] > 1:
            self.model_name_help.setVisible(False)
        else:
            self.model_name_help.clicked.connect(self.win_action.show_model_help)

        try:
            config.params['tts_type'] = int(config.params['tts_type'])
        except Exception:
            config.params['tts_type'] = 0

        if config.params['split_type']:
            d = {"all": 0, "avg": 1}
            self.split_type.setCurrentIndex(d[config.params['split_type']])

        if config.params['subtitle_type'] and int(config.params['subtitle_type']) > 0:
            self.subtitle_type.setCurrentIndex(int(config.params['subtitle_type']))

        try:
            self.voice_rate.setValue(int(config.params['voice_rate'].replace('%', '')))
        except Exception:
            self.voice_rate.setValue(0)
        try:
            self.pitch_rate.setValue(int(config.params['pitch'].replace('Hz', '')))
            self.volume_rate.setValue(int(config.params['volume']))
        except Exception:
            self.pitch_rate.setValue(0)
            self.volume_rate.setValue(0)
        self.addbackbtn.clicked.connect(self.win_action.get_background)

        self.split_type.setDisabled(True if config.params['recogn_type'] > 0 else False)
        self.voice_autorate.setChecked(bool(config.params['voice_autorate']))
        self.video_autorate.setChecked(bool(config.params['video_autorate']))
        self.append_video.setChecked(bool(config.params['append_video']))
        self.clear_cache.setChecked(bool(config.params.get('clear_cache')))
        self.enable_cuda.setChecked(True if config.params['cuda'] else False)
        self.only_video.setChecked(True if config.params['only_video'] else False)
        self.is_separate.setChecked(True if config.params['is_separate'] else False)
        self.rephrase.setChecked(config.settings.get('rephrase'))
        self.remove_noise.setChecked(config.params.get('remove_noise'))
        self.copysrt_rawvideo.setChecked(config.params.get('copysrt_rawvideo',False))
        self.auto_align.setChecked(config.params.get('auto_align',False))

        self.bgmvolume.setText(str(config.settings.get('backaudio_volume',0.8)))
        self.is_loop_bgm.setChecked(bool(config.settings.get('loop_backaudio',True)))

        self.enable_cuda.toggled.connect(self.win_action.check_cuda)
