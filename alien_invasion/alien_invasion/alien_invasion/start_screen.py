"""
开始界面模块
显示游戏标题、操作指引和开始按钮
"""

import pygame

class StartScreen:
    """开始界面类"""
    
    def __init__(self, ai_game):
        """
        初始化开始界面
        
        Args:
            ai_game: 游戏实例
        """
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.screen_rect = self.screen.get_rect()
        
        # 字体设置（支持中文）
        def get_chinese_font(size):
            """获取支持中文的字体"""
            chinese_font_names = [
                'SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi', 'FangSong',
                'simhei', 'microsoft yahei', 'simsun', 'kaiti', 'fangsong',
            ]
            for font_name in chinese_font_names:
                try:
                    test_font = pygame.font.SysFont(font_name, size)
                    test_surface = test_font.render('测试', True, (255, 255, 255))
                    if test_surface.get_width() > 0:
                        return test_font
                except:
                    continue
            return pygame.font.SysFont(None, size)
        
        self.title_font = get_chinese_font(72)
        self.subtitle_font = get_chinese_font(36)
        self.instruction_font = get_chinese_font(24)
        self.hint_font = get_chinese_font(20)
        
        # 颜色设置
        self.title_color = (255, 215, 0)  # 金色标题
        self.subtitle_color = (200, 200, 255)  # 浅蓝色副标题
        self.text_color = (255, 255, 255)  # 白色文本
        self.hint_color = (200, 200, 200)  # 灰色提示
        
        # 准备文本
        self._prep_texts()
    
    def _prep_texts(self):
        """准备所有文本图像"""
        # 游戏标题
        self.title_image = self.title_font.render(
            "外星人入侵", True, self.title_color
        )
        self.title_rect = self.title_image.get_rect()
        self.title_rect.centerx = self.screen_rect.centerx
        self.title_rect.top = 100
        
        # 副标题
        self.subtitle_image = self.subtitle_font.render(
            "Alien Invasion", True, self.subtitle_color
        )
        self.subtitle_rect = self.subtitle_image.get_rect()
        self.subtitle_rect.centerx = self.screen_rect.centerx
        self.subtitle_rect.top = self.title_rect.bottom + 20
        
        # 操作指引
        self.instructions = [
            "【基本操作】",
            "方向键：移动飞船",
            "空格键：发射子弹",
            "P键：暂停/继续",
            "",
            "【技能系统】",
            "1-5键：使用主动技能",
            "U键：释放大招（充能满时）",
            "",
            "【游戏机制】",
            "• 击败外星人获得经验和分数",
            "• 升级后选择属性提升",
            "• 每5关必得宝箱奖励",
            "• 拾取道具获得临时增益",
            "",
            "【提示】",
            "• 保持连击可以获得更高分数",
            "• 合理使用技能应对困难关卡",
            "• 装备可以大幅提升属性",
        ]
        
        # 准备指引文本
        self.instruction_images = []
        self.instruction_rects = []
        start_y = self.subtitle_rect.bottom + 60
        spacing = 28
        
        for i, instruction in enumerate(self.instructions):
            if instruction.startswith("【"):
                # 标题行，使用较大字体和特殊颜色
                color = (100, 200, 255)  # 浅蓝色
                font = self.subtitle_font
            elif instruction.startswith("•"):
                # 列表项，使用缩进
                color = (200, 255, 200)  # 浅绿色
                font = self.instruction_font
            else:
                color = self.text_color
                font = self.instruction_font
            
            instruction_image = font.render(instruction, True, color)
            instruction_rect = instruction_image.get_rect()
            instruction_rect.left = self.screen_rect.centerx - 300
            instruction_rect.top = start_y + i * spacing
            
            self.instruction_images.append(instruction_image)
            self.instruction_rects.append(instruction_rect)
        
        # 提示文本
        self.hint_image = self.hint_font.render(
            "点击 Play 按钮或按空格键开始游戏", True, self.hint_color
        )
        self.hint_rect = self.hint_image.get_rect()
        self.hint_rect.centerx = self.screen_rect.centerx
        self.hint_rect.bottom = self.settings.screen_height - 30
    
    def draw(self):
        """绘制开始界面"""
        # 绘制标题
        self.screen.blit(self.title_image, self.title_rect)
        self.screen.blit(self.subtitle_image, self.subtitle_rect)
        
        # 绘制操作指引
        for image, rect in zip(self.instruction_images, self.instruction_rects):
            self.screen.blit(image, rect)
        
        # 绘制提示
        self.screen.blit(self.hint_image, self.hint_rect)

