from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
from PySide6.QtCore import Qt, Signal

class ThemeSelector(QDialog):
    """主题选择器对话框"""
    
    # 定义信号，当主题改变时发出
    themeChanged = Signal(str)
    
    def __init__(self, theme_manager, parent=None):
        """初始化主题选择器
        
        Args:
            theme_manager: 主题管理器实例
            parent: 父窗口
        """
        super(ThemeSelector, self).__init__(parent)
        self.theme_manager = theme_manager
        self.setWindowTitle("选择主题 / Select Theme")
        self.setMinimumWidth(300)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("选择应用程序主题 / Select Application Theme")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 主题选择下拉框
        theme_layout = QHBoxLayout()
        theme_label = QLabel("主题 / Theme:")
        self.theme_combo = QComboBox()
        
        # 添加可用主题
        themes = self.theme_manager.get_available_themes()
        for theme_id, theme_name in themes.items():
            self.theme_combo.addItem(theme_name, theme_id)
            
        # 设置当前主题
        current_theme = self.theme_manager.get_current_theme()
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == current_theme:
                self.theme_combo.setCurrentIndex(i)
                break
                
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)
        
        # 预览提示
        preview_label = QLabel("选择主题后会立即应用，可以预览效果")
        preview_label.setAlignment(Qt.AlignCenter)
        preview_label.setStyleSheet("font-style: italic; color: #666; margin: 10px 0;")
        layout.addWidget(preview_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("应用 / Apply")
        self.cancel_button = QPushButton("取消 / Cancel")
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        # 连接信号
        self.theme_combo.currentIndexChanged.connect(self.preview_theme)
        self.apply_button.clicked.connect(self.apply_theme)
        self.cancel_button.clicked.connect(self.reject)
        
    def preview_theme(self, index):
        """预览所选主题
        
        Args:
            index: 下拉框中的索引
        """
        theme_id = self.theme_combo.itemData(index)
        style_sheet = self.theme_manager.get_theme_style(theme_id)
        
        # 应用到父窗口进行预览
        if self.parent():
            self.parent().setStyleSheet(style_sheet)
        
    def apply_theme(self):
        """应用所选主题并关闭对话框"""
        theme_id = self.theme_combo.itemData(self.theme_combo.currentIndex())
        self.theme_manager.set_theme(theme_id)
        self.themeChanged.emit(theme_id)
        self.accept() 