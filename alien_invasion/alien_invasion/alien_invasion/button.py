import pygame.font

class Button:
    """为游戏创建按钮的类"""

    def __init__(self, ai_game, msg):
        """初始化按钮的属性"""
        self.screen = ai_game.screen
        self.screen_rect = self.screen.get_rect()

        # 设置按钮的尺寸和其他属性（美化版）
        self.width, self.height = 250, 60
        self.button_color = (0, 150, 0)  # 深绿色
        self.hover_color = (0, 200, 0)  # 浅绿色（悬停）
        self.text_color = (255, 255, 255)
        self.border_color = (100, 255, 100)  # 边框颜色
        
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
        
        self.font = get_chinese_font(36)

        # 创建按钮的 rect 对象，并使其居中
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.centerx = self.screen_rect.centerx
        self.rect.centery = self.screen_rect.centery + 200

        # 按钮的标签只需创建一次
        self._prep_msg(msg)
        
        # 悬停状态
        self.is_hovered = False

    def _prep_msg(self, msg):
        """将 msg 渲染为图像，并使其在按钮上居中"""
        self.msg_image = self.font.render(msg, True, self.text_color)
        self.msg_image_rect = self.msg_image.get_rect()
        self.msg_image_rect.center = self.rect.center

    def check_hover(self, mouse_pos):
        """检查鼠标是否悬停在按钮上"""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def draw_button(self):
        """绘制一个用颜色填充的按钮，再绘制文本（美化版）"""
        # 根据悬停状态选择颜色
        current_color = self.hover_color if self.is_hovered else self.button_color
        
        # 绘制按钮背景（带圆角效果）
        pygame.draw.rect(self.screen, current_color, self.rect, border_radius=10)
        
        # 绘制边框
        pygame.draw.rect(self.screen, self.border_color, self.rect, width=3, border_radius=10)
        
        # 绘制文本
        self.screen.blit(self.msg_image, self.msg_image_rect)