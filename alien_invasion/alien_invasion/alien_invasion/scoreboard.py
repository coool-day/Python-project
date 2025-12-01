import pygame.font
from pygame.sprite import Group

from ship import Ship

class Scoreboard:
    """显示得分信息的类"""
    
    def __init__(self,ai_game):
        """初始化记录得分的属性"""
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.screen_rect = self.screen.get_rect()
        self.settings = ai_game.settings
        self.stats = ai_game.stats
        self.upgrade_system = ai_game.upgrade_system

        # 显示得分信息时使用的字体设置（使用支持中文的字体）
        def get_chinese_font(size):
            """获取支持中文的字体"""
            # Windows常见中文字体名称（尝试多种可能的名称格式）
            chinese_font_names = [
                'SimHei',           # 黑体
                'Microsoft YaHei', # 微软雅黑
                'SimSun',           # 宋体
                'KaiTi',            # 楷体
                'FangSong',         # 仿宋
                'simhei',           # 小写
                'microsoft yahei',  # 小写
                'simsun',           # 小写
                'kaiti',            # 小写
                'fangsong',         # 小写
            ]
            
            # 尝试每个字体名称
            for font_name in chinese_font_names:
                try:
                    test_font = pygame.font.SysFont(font_name, size)
                    # 测试是否能正确渲染中文
                    test_surface = test_font.render('测试', True, (255, 255, 255))
                    # 如果渲染成功且宽度合理，说明字体可用
                    if test_surface.get_width() > 0:
                        return test_font
                except:
                    continue
            
            # 如果所有中文字体都失败，尝试使用默认字体
            try:
                return pygame.font.SysFont(None, size)
            except:
                # 最后的备选方案
                return pygame.font.Font(None, size)
        
        self.text_color = (30,30,30)
        self.font = get_chinese_font(48)
        self.small_font = get_chinese_font(32)  # 用于经验值条

        # 准备包含最高分和当前得分的图像
        self.prep_score()
        self.prep_high_score()
        self.prep_level()
        self.prep_ship()
        # 初始化连击显示（combo默认为0，不显示）
        self.combo_image = None

    def prep_score(self):
        """将得分渲染为图像"""
        rounded_score = round(self.stats.score,-1)
        score_str = f"{rounded_score:,}"
        self.score_image = self.font.render(
            score_str,True,self.text_color,self.settings.bg_color)

        # 在屏幕右上角显示得分
        self.score_rect = self.score_image.get_rect()
        self.score_rect.right = self.screen_rect.right - 20
        self.score_rect.top = 20

    def prep_high_score(self):
        """将最高分渲染为图像"""
        high_score = round(self.stats.high_score,-1)
        high_score_str = f"{high_score:,}"
        self.high_score_image = self.font.render(
            high_score_str,True,self.text_color,self.settings.bg_color)

        # 将最高分放在屏幕顶部的中央
        self.high_score_rect = self.high_score_image.get_rect()
        self.high_score_rect.centerx = self.screen_rect.centerx
        self.high_score_rect.top = self.high_score_rect.top

    def show_score(self):
        """在屏幕上绘制得分、等级和余下的飞船数"""
        self.screen.blit(self.score_image, self.score_rect)
        self.screen.blit(self.high_score_image,self.high_score_rect)
        self.screen.blit(self.level_image,self.level_rect)
        self.ships.draw(self.screen)
        
        # 如果有连击，显示连击数
        if self.stats.combo > 0:
            self.prep_combo()
            if self.combo_image:
                self.screen.blit(self.combo_image, self.combo_rect)
        
        # 显示经验值条和玩家等级
        self._draw_experience_bar()

    def check_high_score(self):
        """检查是否诞生了新的最高分"""
        if self.stats.score > self.stats.high_score:
            self.stats.high_score  = self.stats.score
            self.prep_high_score()

    def prep_level(self):
        """将等级渲染为图像"""
        level_str = str(self.stats.level)
        self.level_image = self.font.render(
            level_str,True,self.text_color,self.settings.bg_color)

        # 将等级放在得分下面
        self.level_rect = self.level_image.get_rect()
        self.level_rect.right = self.score_rect.right
        self.level_rect.top = self.score_rect.bottom + 10

    def prep_ship(self):
        """显示还剩下多少飞船"""
        self.ships = Group()
        for ship_number in range(self.stats.ship_left):
            ship = Ship(self.ai_game)
            ship.rect.x = 10 + ship_number * ship.rect.width
            ship.rect.y = 10
            self.ships.add(ship)
    
    def prep_combo(self):
        """将连击数渲染为图像"""
        if self.stats.combo > 0:
            combo_str = f"Combo x{self.stats.combo}!"
            # 连击数使用更醒目的颜色
            if self.stats.combo >= 20:
                combo_color = (255, 0, 255)  # 紫色 - 超高连击
            elif self.stats.combo >= 10:
                combo_color = (255, 215, 0)  # 金色 - 高连击
            else:
                combo_color = (255, 165, 0)  # 橙色 - 普通连击
            
            self.combo_image = self.font.render(
                combo_str, True, combo_color, self.settings.bg_color)
            
            # 将连击数放在屏幕左侧
            self.combo_rect = self.combo_image.get_rect()
            self.combo_rect.left = 20
            self.combo_rect.top = 100
        else:
            # 如果没有连击，清空图像
            self.combo_image = None
    
    def _draw_experience_bar(self):
        """绘制经验值条"""
        # 经验值条位置（在屏幕左侧，连击下方）
        bar_x = 20
        bar_y = 150
        bar_width = 300
        bar_height = 25
        
        # 获取经验值百分比
        exp_percentage = self.upgrade_system.get_experience_percentage()
        
        # 绘制经验值条背景
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, (50, 50, 50), bg_rect)  # 深灰色背景
        pygame.draw.rect(self.screen, (100, 100, 100), bg_rect, 2)  # 边框
        
        # 绘制经验值条填充
        fill_width = int(bar_width * exp_percentage)
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            # 根据经验值百分比使用不同颜色
            if exp_percentage < 0.5:
                fill_color = (100, 200, 100)  # 绿色
            elif exp_percentage < 0.8:
                fill_color = (200, 200, 100)  # 黄色
            else:
                fill_color = (255, 200, 100)  # 橙色（接近升级）
            pygame.draw.rect(self.screen, fill_color, fill_rect)
        
        # 绘制经验值文本
        exp_text = f"Lv.{self.upgrade_system.player_level}  EXP: {self.upgrade_system.experience}/{self.upgrade_system.experience_to_next_level}"
        exp_image = self.small_font.render(exp_text, True, (255, 255, 255))
        exp_rect = exp_image.get_rect()
        exp_rect.left = bar_x
        exp_rect.top = bar_y - 30
        self.screen.blit(exp_image, exp_rect)