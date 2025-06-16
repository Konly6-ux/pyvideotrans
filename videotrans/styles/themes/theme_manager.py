from PySide6.QtCore import QSettings
import os
from pathlib import Path

class ThemeManager:
    """主题管理器，用于管理和切换应用程序主题"""
    
    # 可用主题列表
    THEMES = {
        "dark": "暗黑主题 (Dark)",
        "light": "明亮主题 (Light)",
        "apple": "苹果风格 (Apple)",
        "minimal": "极简主题 (Minimal)",
        "classic": "经典主题 (Classic)"
    }
    
    def __init__(self, root_dir):
        """初始化主题管理器
        
        Args:
            root_dir: 应用程序根目录
        """
        self.root_dir = root_dir
        self.settings = QSettings("pyvideotrans", "settings")
        self.current_theme = self.settings.value("theme", "dark")
        
        # 确保主题目录存在
        self.themes_dir = os.path.join(root_dir, "videotrans", "styles", "themes")
        os.makedirs(self.themes_dir, exist_ok=True)
    
    def get_theme_path(self, theme_name=None):
        """获取指定主题的样式表路径
        
        Args:
            theme_name: 主题名称，如果为None则使用当前主题
            
        Returns:
            主题样式表的路径
        """
        if theme_name is None:
            theme_name = self.current_theme
            
        # 如果主题文件不存在，则使用默认主题
        theme_path = os.path.join(self.themes_dir, f"{theme_name}.qss")
        if not os.path.exists(theme_path):
            theme_path = os.path.join(self.root_dir, "videotrans", "styles", "style.qss")
            
        return theme_path
    
    def set_theme(self, theme_name):
        """设置当前主题
        
        Args:
            theme_name: 主题名称
            
        Returns:
            主题样式表的内容
        """
        if theme_name in self.THEMES:
            self.current_theme = theme_name
            self.settings.setValue("theme", theme_name)
            
        return self.get_theme_style()
    
    def get_theme_style(self, theme_name=None):
        """获取主题样式表内容
        
        Args:
            theme_name: 主题名称，如果为None则使用当前主题
            
        Returns:
            主题样式表的内容
        """
        theme_path = self.get_theme_path(theme_name)
        try:
            with open(theme_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"加载主题样式表失败: {e}")
            # 如果加载失败，尝试加载默认样式
            default_path = os.path.join(self.root_dir, "videotrans", "styles", "style.qss")
            with open(default_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    def get_available_themes(self):
        """获取所有可用的主题列表
        
        Returns:
            主题名称和显示名称的字典
        """
        return self.THEMES
    
    def get_current_theme(self):
        """获取当前主题名称
        
        Returns:
            当前主题名称
        """
        return self.current_theme 