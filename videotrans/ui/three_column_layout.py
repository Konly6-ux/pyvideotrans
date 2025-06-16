from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QSizePolicy, QFrame, QLabel, QScrollArea, QGroupBox

from videotrans.component.controlobj import TextGetdir
from videotrans.configure import config
from videotrans.recognition import RECOGN_NAME_LIST
from videotrans.tts import TTS_NAME_LIST

class ThreeColumnLayout(object):
    """三栏布局UI类，用于替换原有的UI布局"""
    
    def setupUi(self, MainWindow, original_ui):
        """设置三栏布局UI
        
        Args:
            MainWindow: 主窗口对象
            original_ui: 原始UI对象，包含所有控件
        """
        # 保存对原始UI的引用
        self.original_ui = original_ui
        
        # 创建中央部件
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        # 主布局
        self.main_layout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.main_layout.setObjectName("main_layout")
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # 创建三个面板
        self.setup_video_settings_panel()  # 视频设置栏
        self.setup_process_panel()         # 处理过程栏
        self.setup_subtitle_panel()        # 字幕栏
        
        # 将三个面板添加到主布局
        self.main_layout.addWidget(self.video_settings_panel)
        self.main_layout.addWidget(self.process_panel)
        self.main_layout.addWidget(self.subtitle_panel)
        
        # 设置面板比例
        self.main_layout.setStretch(0, 3)  # 视频设置栏
        self.main_layout.setStretch(1, 2)  # 处理过程栏
        self.main_layout.setStretch(2, 3)  # 字幕栏
        
        # 设置中央部件
        MainWindow.setCentralWidget(self.centralwidget)
        
        # 保留原始UI的菜单栏和工具栏
        self.menubar = original_ui.menubar
        self.toolBar = original_ui.toolBar
        
        # 添加主题选择菜单项
        self.setup_theme_menu(MainWindow)
        
    def setup_video_settings_panel(self):
        """设置视频设置面板"""
        # 创建视频设置面板
        self.video_settings_panel = QtWidgets.QWidget()
        self.video_settings_panel.setObjectName("video_settings_panel")
        
        # 视频设置面板布局
        self.video_settings_layout = QtWidgets.QVBoxLayout(self.video_settings_panel)
        self.video_settings_layout.setObjectName("video_settings_layout")
        self.video_settings_layout.setContentsMargins(10, 10, 10, 10)
        self.video_settings_layout.setSpacing(15)
        
        # 面板标题
        self.video_settings_title = QLabel("视频设置 / Video Settings")
        self.video_settings_title.setObjectName("panel_title")
        self.video_settings_title.setProperty("class", "panel_title")
        self.video_settings_layout.addWidget(self.video_settings_title)
        
        # 分隔线
        self.video_settings_separator = QFrame()
        self.video_settings_separator.setFrameShape(QFrame.HLine)
        self.video_settings_separator.setFrameShadow(QFrame.Sunken)
        self.video_settings_separator.setObjectName("separator")
        self.video_settings_separator.setProperty("class", "separator")
        self.video_settings_layout.addWidget(self.video_settings_separator)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        
        # 创建滚动区域内容
        scroll_content = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(15)
        
        # 1. 视频文件组
        self._add_video_file_group(scroll_layout)
        
        # 2. 翻译设置组
        self._add_translation_group(scroll_layout)
        
        # 3. 配音设置组
        self._add_dubbing_group(scroll_layout)
        
        # 4. 语音识别设置组
        self._add_recognition_group(scroll_layout)
        
        # 5. 高级设置组
        self._add_advanced_settings_group(scroll_layout)
        
        # 6. 启动按钮组
        self._add_start_button_group(scroll_layout)
        
        # 设置滚动区域
        scroll_area.setWidget(scroll_content)
        self.video_settings_layout.addWidget(scroll_area)
        
    def _add_video_file_group(self, layout):
        """添加视频文件选择组"""
        ui = self.original_ui
        
        # 创建组框
        group_box = QGroupBox("视频文件 / Video Files")
        group_box.setProperty("class", "setting_group")
        group_layout = QtWidgets.QVBoxLayout(group_box)
        
        # 视频选择行
        video_selection_layout = QtWidgets.QHBoxLayout()
        video_selection_layout.addWidget(ui.btn_get_video)
        video_selection_layout.addWidget(ui.select_file_type)
        video_selection_layout.addWidget(ui.source_mp4)
        video_selection_layout.addStretch()
        group_layout.addLayout(video_selection_layout)
        
        # 保存目录行
        save_dir_layout = QtWidgets.QHBoxLayout()
        save_dir_layout.addWidget(ui.btn_save_dir)
        save_dir_layout.addStretch()
        group_layout.addLayout(save_dir_layout)
        
        # 选项行
        options_layout = QtWidgets.QHBoxLayout()
        options_layout.addWidget(ui.clear_cache)
        options_layout.addWidget(ui.copysrt_rawvideo)
        options_layout.addWidget(ui.only_video)
        options_layout.addWidget(ui.shutdown)
        options_layout.addStretch()
        group_layout.addLayout(options_layout)
        
        # 添加到主布局
        layout.addWidget(group_box)
        
    def _add_translation_group(self, layout):
        """添加翻译设置组"""
        ui = self.original_ui
        
        # 创建组框
        group_box = QGroupBox("翻译设置 / Translation Settings")
        group_box.setProperty("class", "setting_group")
        group_layout = QtWidgets.QVBoxLayout(group_box)
        
        # 翻译类型行
        translate_type_layout = QtWidgets.QHBoxLayout()
        translate_type_layout.addWidget(ui.label_9)
        translate_type_layout.addWidget(ui.translate_type)
        translate_type_layout.addStretch()
        group_layout.addLayout(translate_type_layout)
        
        # 语言设置行
        language_layout = QtWidgets.QHBoxLayout()
        language_layout.addWidget(ui.label_2)
        language_layout.addWidget(ui.source_language)
        language_layout.addWidget(ui.label_3)
        language_layout.addWidget(ui.target_language)
        language_layout.addStretch()
        group_layout.addLayout(language_layout)
        
        # 术语表和代理行
        glossary_proxy_layout = QtWidgets.QHBoxLayout()
        glossary_proxy_layout.addWidget(ui.glossary)
        glossary_proxy_layout.addWidget(ui.aisendsrt)
        glossary_proxy_layout.addWidget(ui.label)
        glossary_proxy_layout.addWidget(ui.proxy)
        glossary_proxy_layout.addStretch()
        group_layout.addLayout(glossary_proxy_layout)
        
        # 添加到主布局
        layout.addWidget(group_box)
        
    def _add_dubbing_group(self, layout):
        """添加配音设置组"""
        ui = self.original_ui
        
        # 创建组框
        group_box = QGroupBox("配音设置 / Dubbing Settings")
        group_box.setProperty("class", "setting_group")
        group_layout = QtWidgets.QVBoxLayout(group_box)
        
        # 配音渠道行
        dubbing_channel_layout = QtWidgets.QHBoxLayout()
        dubbing_channel_layout.addWidget(ui.tts_text)
        dubbing_channel_layout.addWidget(ui.tts_type)
        dubbing_channel_layout.addStretch()
        group_layout.addLayout(dubbing_channel_layout)
        
        # 配音角色行
        dubbing_role_layout = QtWidgets.QHBoxLayout()
        dubbing_role_layout.addWidget(ui.label_4)
        dubbing_role_layout.addWidget(ui.voice_role)
        dubbing_role_layout.addWidget(ui.listen_btn)
        dubbing_role_layout.addStretch()
        group_layout.addLayout(dubbing_role_layout)
        
        # 配音参数行
        dubbing_params_layout = QtWidgets.QHBoxLayout()
        dubbing_params_layout.addWidget(ui.label_6)
        dubbing_params_layout.addWidget(ui.voice_rate)
        dubbing_params_layout.addWidget(ui.volume_label)
        dubbing_params_layout.addWidget(ui.volume_rate)
        dubbing_params_layout.addWidget(ui.pitch_label)
        dubbing_params_layout.addWidget(ui.pitch_rate)
        dubbing_params_layout.addStretch()
        group_layout.addLayout(dubbing_params_layout)
        
        # 添加到主布局
        layout.addWidget(group_box)
        
    def _add_recognition_group(self, layout):
        """添加语音识别设置组"""
        ui = self.original_ui
        
        # 创建组框
        group_box = QGroupBox("语音识别设置 / Speech Recognition Settings")
        group_box.setProperty("class", "setting_group")
        group_layout = QtWidgets.QVBoxLayout(group_box)
        
        # 识别类型行
        recognition_type_layout = QtWidgets.QHBoxLayout()
        recognition_type_layout.addWidget(ui.reglabel)
        recognition_type_layout.addWidget(ui.recogn_type)
        recognition_type_layout.addStretch()
        group_layout.addLayout(recognition_type_layout)
        
        # 模型选择行
        model_layout = QtWidgets.QHBoxLayout()
        model_layout.addWidget(ui.model_name_help)
        model_layout.addWidget(ui.model_name)
        model_layout.addStretch()
        group_layout.addLayout(model_layout)
        
        # 切割模式行
        split_layout = QtWidgets.QHBoxLayout()
        split_layout.addWidget(ui.split_label)
        split_layout.addWidget(ui.split_type)
        
        # 添加equal_split_layout的内容
        equal_split_layout = QtWidgets.QHBoxLayout()
        equal_split_layout.addWidget(ui.equal_split_time)
        equal_split_layout.addWidget(ui.equal_split_time_label)
        split_layout.addLayout(equal_split_layout)
        split_layout.addStretch()
        group_layout.addLayout(split_layout)
        
        # 处理选项行
        processing_options_layout = QtWidgets.QHBoxLayout()
        processing_options_layout.addWidget(ui.rephrase)
        processing_options_layout.addWidget(ui.remove_noise)
        processing_options_layout.addStretch()
        group_layout.addLayout(processing_options_layout)
        
        # 高级参数行（可折叠）
        advanced_recognition_layout = QtWidgets.QVBoxLayout()
        advanced_recognition_header = QtWidgets.QHBoxLayout()
        advanced_recognition_header.addWidget(ui.hfaster_help)
        advanced_recognition_header.addStretch()
        advanced_recognition_layout.addLayout(advanced_recognition_header)

        # 参数行1
        params_layout1 = QtWidgets.QHBoxLayout()
        params_layout1.addWidget(ui.threshold_label)
        params_layout1.addWidget(ui.threshold)
        params_layout1.addWidget(ui.min_speech_duration_ms_label)
        params_layout1.addWidget(ui.min_speech_duration_ms)
        params_layout1.addStretch()
        advanced_recognition_layout.addLayout(params_layout1)
        
        # 参数行2
        params_layout2 = QtWidgets.QHBoxLayout()
        params_layout2.addWidget(ui.min_silence_duration_ms_label)
        params_layout2.addWidget(ui.min_silence_duration_ms)
        params_layout2.addWidget(ui.max_speech_duration_s_label)
        params_layout2.addWidget(ui.max_speech_duration_s)
        params_layout2.addStretch()
        advanced_recognition_layout.addLayout(params_layout2)
        
        # 参数行3
        params_layout3 = QtWidgets.QHBoxLayout()
        params_layout3.addWidget(ui.speech_pad_ms_label)
        params_layout3.addWidget(ui.speech_pad_ms)
        params_layout3.addStretch()
        advanced_recognition_layout.addLayout(params_layout3)
        
        # 添加高级参数布局
        group_layout.addLayout(advanced_recognition_layout)
        
        # 添加到主布局
        layout.addWidget(group_box)
        
    def _add_advanced_settings_group(self, layout):
        """添加高级设置组"""
        ui = self.original_ui
        
        # 创建组框
        group_box = QGroupBox("高级设置 / Advanced Settings")
        group_box.setProperty("class", "setting_group")
        group_layout = QtWidgets.QVBoxLayout(group_box)
        
        # 对齐控制行
        alignment_layout = QtWidgets.QHBoxLayout()
        alignment_layout.addWidget(ui.align_btn)
        alignment_layout.addStretch()
        group_layout.addLayout(alignment_layout)
        
        # 视频选项行
        video_options_layout = QtWidgets.QHBoxLayout()
        video_options_layout.addWidget(ui.append_video)
        video_options_layout.addWidget(ui.voice_autorate)
        video_options_layout.addWidget(ui.video_autorate)
        video_options_layout.addStretch()
        group_layout.addLayout(video_options_layout)
        
        # 字幕选项行
        subtitle_options_layout = QtWidgets.QHBoxLayout()
        subtitle_options_layout.addWidget(ui.subtitle_type)
        subtitle_options_layout.addWidget(ui.label_cjklinenums)
        subtitle_options_layout.addWidget(ui.cjklinenums)
        subtitle_options_layout.addWidget(ui.label_othlinenums)
        subtitle_options_layout.addWidget(ui.othlinenums)
        subtitle_options_layout.addStretch()
        group_layout.addLayout(subtitle_options_layout)
        
        # 背景音频行1
        bg_audio_layout1 = QtWidgets.QHBoxLayout()
        bg_audio_layout1.addWidget(ui.is_separate)
        bg_audio_layout1.addWidget(ui.auto_align)
        bg_audio_layout1.addStretch()
        group_layout.addLayout(bg_audio_layout1)
        
        # 背景音频行2
        bg_audio_layout2 = QtWidgets.QHBoxLayout()
        bg_audio_layout2.addWidget(ui.addbackbtn)
        bg_audio_layout2.addWidget(ui.back_audio)
        bg_audio_layout2.addStretch()
        group_layout.addLayout(bg_audio_layout2)
        
        # 背景音频行3
        bg_audio_layout3 = QtWidgets.QHBoxLayout()
        bg_audio_layout3.addWidget(ui.is_loop_bgm)
        bg_audio_layout3.addWidget(ui.bgmvolume_label)
        bg_audio_layout3.addWidget(ui.bgmvolume)
        bg_audio_layout3.addStretch()
        group_layout.addLayout(bg_audio_layout3)
        
        # 添加提示文本
        group_layout.addWidget(ui.show_tips)
        
        # 添加到主布局
        layout.addWidget(group_box)
        
    def _add_start_button_group(self, layout):
        """添加启动按钮组"""
        ui = self.original_ui
        
        # 创建组框
        group_box = QGroupBox("执行任务 / Execute Task")
        group_box.setProperty("class", "setting_group")
        group_layout = QtWidgets.QVBoxLayout(group_box)
        
        # 启动按钮行
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)
        
        # 创建垂直布局来放置enable_cuda复选框
        cuda_layout = QtWidgets.QVBoxLayout()
        cuda_layout.setAlignment(Qt.AlignVCenter)
        cuda_layout.addWidget(ui.enable_cuda)
        
        button_layout.addLayout(cuda_layout)
        button_layout.addWidget(ui.startbtn)
        button_layout.addWidget(ui.continue_compos)
        button_layout.addWidget(ui.stop_djs)
        
        # 添加到组布局
        group_layout.addLayout(button_layout)
        
        # 添加到主布局
        layout.addWidget(group_box)
        
    def setup_process_panel(self):
        """设置处理过程面板"""
        # 创建处理过程面板
        self.process_panel = QtWidgets.QWidget()
        self.process_panel.setObjectName("process_panel")
        
        # 处理过程面板布局
        self.process_layout = QtWidgets.QVBoxLayout(self.process_panel)
        self.process_layout.setObjectName("process_layout")
        self.process_layout.setContentsMargins(10, 10, 10, 10)
        self.process_layout.setSpacing(10)
        
        # 面板标题
        self.process_title = QLabel("处理过程 / Process")
        self.process_title.setObjectName("panel_title")
        self.process_title.setProperty("class", "panel_title")
        self.process_layout.addWidget(self.process_title)
        
        # 分隔线
        self.process_separator = QFrame()
        self.process_separator.setFrameShape(QFrame.HLine)
        self.process_separator.setFrameShadow(QFrame.Sunken)
        self.process_separator.setObjectName("separator")
        self.process_separator.setProperty("class", "separator")
        self.process_layout.addWidget(self.process_separator)
        
        # 添加超时提示
        self.process_layout.addWidget(self.original_ui.timeout_tips)
        
        # 添加处理过程滚动区域
        self.process_layout.addWidget(self.original_ui.scroll_area)
        
    def setup_subtitle_panel(self):
        """设置字幕面板"""
        # 创建字幕面板
        self.subtitle_panel = QtWidgets.QWidget()
        self.subtitle_panel.setObjectName("subtitle_panel")
        
        # 字幕面板布局
        self.subtitle_layout_main = QtWidgets.QVBoxLayout(self.subtitle_panel)
        self.subtitle_layout_main.setObjectName("subtitle_layout_main")
        self.subtitle_layout_main.setContentsMargins(10, 10, 10, 10)
        self.subtitle_layout_main.setSpacing(10)
        
        # 面板标题
        self.subtitle_title = QLabel("字幕编辑 / Subtitle")
        self.subtitle_title.setObjectName("panel_title")
        self.subtitle_title.setProperty("class", "panel_title")
        self.subtitle_layout_main.addWidget(self.subtitle_title)
        
        # 分隔线
        self.subtitle_separator = QFrame()
        self.subtitle_separator.setFrameShape(QFrame.HLine)
        self.subtitle_separator.setFrameShadow(QFrame.Sunken)
        self.subtitle_separator.setObjectName("separator")
        self.subtitle_separator.setProperty("class", "separator")
        self.subtitle_layout_main.addWidget(self.subtitle_separator)
        
        # 创建字幕编辑区域
        subtitle_area_layout = QtWidgets.QVBoxLayout()
        subtitle_area_layout.addWidget(self.original_ui.subtitle_area)
        subtitle_area_layout.addWidget(self.original_ui.import_sub)
        
        # 创建目标字幕区域布局
        target_subtitle_layout = QtWidgets.QVBoxLayout()
        
        # 创建水平布局来放置两个字幕区域
        subtitle_layout = QtWidgets.QHBoxLayout()
        subtitle_layout.addLayout(subtitle_area_layout)
        subtitle_layout.addLayout(target_subtitle_layout)
        
        # 将字幕布局添加到主布局
        self.subtitle_layout_main.addLayout(subtitle_layout)
        
    def setup_theme_menu(self, MainWindow):
        """设置主题菜单"""
        # 创建主题菜单
        self.menu_theme = QtWidgets.QMenu(self.menubar)
        self.menu_theme.setObjectName("menu_theme")
        self.menu_theme.setTitle("主题 / Theme")
        
        # 添加主题菜单到菜单栏
        self.menubar.addAction(self.menu_theme.menuAction())
        
        # 创建主题选择动作
        self.action_theme = QAction(MainWindow)
        self.action_theme.setObjectName("action_theme")
        self.action_theme.setText("选择主题 / Select Theme")
        
        # 添加主题选择动作到主题菜单
        self.menu_theme.addAction(self.action_theme) 