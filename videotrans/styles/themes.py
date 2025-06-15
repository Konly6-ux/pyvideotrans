# 创建主题管理器文件
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

from videotrans.configure import config

# 主题颜色方案
THEMES = {
    "dark_blue": {
        "name": "深蓝主题" if config.defaulelang == 'zh' else "Dark Blue",
        "primary": "#19232D",         # 主背景色
        "secondary": "#455364",       # 次背景色
        "accent": "#148CD2",          # 强调色
        "text": "#DFE1E2",            # 主文本色
        "text_secondary": "#788D9C",  # 次文本色
        "border": "#32414B",          # 边框色
        "highlight": "#1A72BB",       # 高亮色
        "selection": "#346792",       # 选中色
        "button": "#455364",          # 按钮色
        "button_hover": "#54687A",    # 按钮悬停色
        "button_pressed": "#60798B",  # 按钮按下色
        "input_bg": "#19232D",        # 输入框背景色
        "input_border": "#455364",    # 输入框边框色
    },
    "dark_gray": {
        "name": "深灰主题" if config.defaulelang == 'zh' else "Dark Gray",
        "primary": "#2D2D2D",         # 主背景色
        "secondary": "#3D3D3D",       # 次背景色
        "accent": "#E67E22",          # 强调色
        "text": "#F0F0F0",            # 主文本色
        "text_secondary": "#A0A0A0",  # 次文本色
        "border": "#505050",          # 边框色
        "highlight": "#F39C12",       # 高亮色
        "selection": "#D35400",       # 选中色
        "button": "#3D3D3D",          # 按钮色
        "button_hover": "#4D4D4D",    # 按钮悬停色
        "button_pressed": "#5D5D5D",  # 按钮按下色
        "input_bg": "#2D2D2D",        # 输入框背景色
        "input_border": "#505050",    # 输入框边框色
    },
    "light_blue": {
        "name": "浅蓝主题" if config.defaulelang == 'zh' else "Light Blue",
        "primary": "#F0F0F0",         # 主背景色
        "secondary": "#E1E1E1",       # 次背景色
        "accent": "#2980B9",          # 强调色
        "text": "#2C3E50",            # 主文本色
        "text_secondary": "#7F8C8D",  # 次文本色
        "border": "#BDC3C7",          # 边框色
        "highlight": "#3498DB",       # 高亮色
        "selection": "#2980B9",       # 选中色
        "button": "#E1E1E1",          # 按钮色
        "button_hover": "#D1D1D1",    # 按钮悬停色
        "button_pressed": "#C1C1C1",  # 按钮按下色
        "input_bg": "#FFFFFF",        # 输入框背景色
        "input_border": "#BDC3C7",    # 输入框边框色
    },
    "dark_green": {
        "name": "深绿主题" if config.defaulelang == 'zh' else "Dark Green",
        "primary": "#1E2723",         # 主背景色
        "secondary": "#2C3C33",       # 次背景色
        "accent": "#2ECC71",          # 强调色
        "text": "#ECF0F1",            # 主文本色
        "text_secondary": "#95A5A6",  # 次文本色
        "border": "#34495E",          # 边框色
        "highlight": "#27AE60",       # 高亮色
        "selection": "#16A085",       # 选中色
        "button": "#2C3C33",          # 按钮色
        "button_hover": "#3C4C43",    # 按钮悬停色
        "button_pressed": "#4C5C53",  # 按钮按下色
        "input_bg": "#1E2723",        # 输入框背景色
        "input_border": "#34495E",    # 输入框边框色
    },
    "purple_dream": {
        "name": "紫色梦境" if config.defaulelang == 'zh' else "Purple Dream",
        "primary": "#2E1E3B",         # 主背景色
        "secondary": "#3D2C4C",       # 次背景色
        "accent": "#9B59B6",          # 强调色
        "text": "#ECF0F1",            # 主文本色
        "text_secondary": "#95A5A6",  # 次文本色
        "border": "#34495E",          # 边框色
        "highlight": "#8E44AD",       # 高亮色
        "selection": "#6C3483",       # 选中色
        "button": "#3D2C4C",          # 按钮色
        "button_hover": "#4D3C5C",    # 按钮悬停色
        "button_pressed": "#5D4C6C",  # 按钮按下色
        "input_bg": "#2E1E3B",        # 输入框背景色
        "input_border": "#34495E",    # 输入框边框色
    }
}

class ThemeManager:
    """主题管理器，负责切换和应用主题"""
    
    def __init__(self):
        self.current_theme = "dark_blue"  # 默认主题
        self.qss_template_path = os.path.join(config.ROOT_DIR, "videotrans/styles/style_template.qss")
        self.qss_output_path = os.path.join(config.ROOT_DIR, "videotrans/styles/style.qss")
        
        # 确保模板文件存在，如果不存在则创建
        if not os.path.exists(self.qss_template_path):
            self._create_template_from_current()
    
    def _create_template_from_current(self):
        """从当前QSS文件创建模板"""
        current_qss_path = os.path.join(config.ROOT_DIR, "videotrans/styles/style.qss")
        if os.path.exists(current_qss_path):
            with open(current_qss_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 将颜色值替换为占位符
            template_content = content
            for theme_key, theme_data in THEMES["dark_blue"].items():
                if theme_key != "name" and isinstance(theme_data, str) and theme_data.startswith('#'):
                    template_content = template_content.replace(theme_data, f"{{{theme_key}}}")
            
            # 保存模板
            with open(self.qss_template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
        else:
            # 如果当前QSS不存在，创建一个基本模板
            self._create_basic_template()
    
    def _create_basic_template(self):
        """创建基本QSS模板"""
        with open(self.qss_template_path, 'w', encoding='utf-8') as f:
            f.write("""
/* 基本QSS模板 */
QWidget {
    background-color: {primary};
    color: {text};
    selection-background-color: {selection};
    selection-color: {text};
}

QPushButton {
    background-color: {button};
    color: {text};
    border: 1px solid {border};
    border-radius: 4px;
    padding: 4px 8px;
}

QPushButton:hover {
    background-color: {button_hover};
}

QPushButton:pressed {
    background-color: {button_pressed};
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: {input_bg};
    color: {text};
    border: 1px solid {input_border};
    border-radius: 4px;
    padding: 2px 4px;
}

QComboBox {
    background-color: {input_bg};
    color: {text};
    border: 1px solid {input_border};
    border-radius: 4px;
    padding: 2px 4px;
}

QLabel {
    color: {text};
    background-color: transparent;
}

QCheckBox {
    color: {text};
    background-color: transparent;
}

QScrollBar:vertical {
    background-color: {primary};
    width: 12px;
    margin: 12px 0 12px 0;
    border: 1px solid {border};
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: {secondary};
    min-height: 20px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background-color: {accent};
}

QScrollBar:horizontal {
    background-color: {primary};
    height: 12px;
    margin: 0 12px 0 12px;
    border: 1px solid {border};
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: {secondary};
    min-width: 20px;
    border-radius: 3px;
}

QScrollBar::handle:horizontal:hover {
    background-color: {accent};
}

QMenuBar {
    background-color: {secondary};
    color: {text};
}

QMenuBar::item {
    background: transparent;
}

QMenuBar::item:selected {
    background-color: {highlight};
    color: {text};
}

QMenu {
    background-color: {secondary};
    color: {text};
    border: 1px solid {border};
}

QMenu::item:selected {
    background-color: {highlight};
    color: {text};
}

QTabWidget::pane {
    border: 1px solid {border};
    background-color: {primary};
}

QTabBar::tab {
    background-color: {secondary};
    color: {text};
    padding: 4px 8px;
    border: 1px solid {border};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: {primary};
    border-bottom: 1px solid {primary};
}

QTabBar::tab:!selected {
    margin-top: 2px;
}
""")
    
    def apply_theme(self, theme_name):
        """应用指定的主题"""
        if theme_name not in THEMES:
            config.logger.error(f"未知主题: {theme_name}")
            return False
        
        self.current_theme = theme_name
        theme_data = THEMES[theme_name]
        
        # 保存当前主题到配置
        if 'ui_theme' not in config.settings:
            config.settings['ui_theme'] = theme_name
        else:
            config.settings['ui_theme'] = theme_name
        
        # 从模板生成QSS
        try:
            if os.path.exists(self.qss_template_path):
                with open(self.qss_template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                
                # 替换占位符
                qss_content = template_content
                for key, value in theme_data.items():
                    if key != "name" and isinstance(value, str):
                        qss_content = qss_content.replace(f"{{{key}}}", value)
                
                # 保存到输出文件
                with open(self.qss_output_path, 'w', encoding='utf-8') as f:
                    f.write(qss_content)
                
                # 保存到用户主题文件
                user_theme_path = self._get_user_theme_path(theme_name)
                try:
                    with open(user_theme_path, 'w', encoding='utf-8') as f:
                        f.write(qss_content)
                except Exception as e:
                    config.logger.error(f"保存用户主题文件失败: {str(e)}")
                
                return True
            else:
                config.logger.error(f"主题模板文件不存在: {self.qss_template_path}")
                return False
        except Exception as e:
            config.logger.error(f"应用主题时出错: {str(e)}")
            return False
    
    def get_theme_list(self):
        """获取所有主题的名称列表"""
        return [(key, data["name"]) for key, data in THEMES.items()]
    
    def get_current_theme(self):
        """获取当前主题名称"""
        return self.current_theme

# 全局主题管理器实例
theme_manager = ThemeManager()