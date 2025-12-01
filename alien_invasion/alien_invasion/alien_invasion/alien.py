import pygame
import random
from pygame.sprite import Sprite

class Alien(Sprite):
    """表示单个外星人的类"""

    def __init__(self,ai_game):
        """初始化外星人并设置其起始位置"""
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings

        # 加载外星人图像并设置其rect属性
        self.image = pygame.image.load('images/alien.bmp')
        self.rect = self.image.get_rect()

        # 每个外星人最初的都在屏幕的左上角附近
        self.rect.x = self.rect.width
        self.rect.y = self.rect.height

        # 存储外星人的精确位置（使用浮点数以支持平滑移动）
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        
        # 随机移动方向（每个外星人有自己的随机移动模式）
        # 水平方向：-1到1之间的随机值，但总体向右
        self.horizontal_direction = random.uniform(-0.3, 1.0)
        # 垂直方向：总是向下，但速度有随机变化
        self.vertical_speed = self.settings.alien_speed * random.uniform(0.8, 1.2)
        
        # 随机移动频率（每N帧改变一次方向）
        self.direction_change_timer = 0
        self.direction_change_interval = random.randint(30, 90)  # 0.5-1.5秒

    def check_edges(self):
        """如果外星人位于屏幕边缘，就返回 True """
        screen_rect = self.screen.get_rect()
        return (self.rect.right >= screen_rect.right) or (self.rect.left <= 0)

    def update(self):
        """更新外星人位置（随机但总体向下移动）"""
        # 更新方向改变计时器
        self.direction_change_timer += 1
        if self.direction_change_timer >= self.direction_change_interval:
            # 随机改变水平移动方向（但保持总体向右的趋势）
            self.horizontal_direction = random.uniform(-0.3, 1.0)
            self.direction_change_timer = 0
            self.direction_change_interval = random.randint(30, 90)
        
        # 水平移动（随机但总体向右）
        horizontal_speed = self.settings.alien_speed * self.horizontal_direction
        self.x += horizontal_speed
        
        # 如果到达屏幕边缘，反弹
        screen_rect = self.screen.get_rect()
        if self.rect.right >= screen_rect.right or self.rect.left <= 0:
            self.horizontal_direction *= -1
        
        # 垂直移动（总是向下，但速度有随机变化）
        self.y += self.vertical_speed
        
        # 更新rect位置
        self.rect.x = self.x
        self.rect.y = self.y

