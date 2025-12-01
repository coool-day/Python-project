import pygame
from pygame.sprite import Sprite

class AlienBullet(Sprite):
    """管理外星人所发射的子弹的类"""

    def __init__(self, ai_game, alien):
        """在外星人的当前位置创建一个子弹对象"""
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.color = (255, 0, 0)  # 红色，用于区分玩家子弹

        # 在(0,0)处创建一个表示子弹的矩形，再设置正确的位置
        self.rect = pygame.Rect(0, 0, self.settings.alien_bullet_width,
                                self.settings.alien_bullet_height)
        self.rect.midbottom = alien.rect.midbottom

        # 存储用浮点数表示的子弹位置
        self.y = float(self.rect.y)
    
    def update(self):
        """向下移动子弹"""
        # 更新子弹的准确位置
        self.y += self.settings.alien_bullet_speed
        # 更新表示子弹的 rect 的位置
        self.rect.y = self.y

    def draw_bullet(self):
        """在屏幕上绘制子弹"""
        pygame.draw.rect(self.screen, self.color, self.rect)

