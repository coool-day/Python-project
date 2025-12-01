"""
激光子弹类
增强的子弹，可以穿透多个敌人
"""

import pygame
from pygame.sprite import Sprite

class LaserBullet(Sprite):
    """激光子弹类（可以穿透敌人）"""
    
    def __init__(self, ai_game):
        """初始化激光子弹"""
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        
        # 激光属性（比普通子弹更大、更快）
        self.width = 5
        self.height = 20
        self.color = (255, 0, 255)  # 紫色
        self.speed = 4.0
        
        # 创建激光矩形
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.midtop = ai_game.ship.rect.midtop
        
        # 存储精确位置
        self.y = float(self.rect.y)
        
        # 穿透计数（可以穿透3个敌人）
        self.penetration = 3
        self.hit_aliens = []
    
    def update(self):
        """更新激光位置"""
        self.y -= self.speed
        self.rect.y = int(self.y)
        
        # 如果超出屏幕顶部，移除
        if self.rect.bottom < 0:
            return True
        return False
    
    def draw(self):
        """绘制激光"""
        # 绘制激光主体
        pygame.draw.rect(self.screen, self.color, self.rect)
        
        # 绘制发光效果
        glow_rect = pygame.Rect(self.rect.x - 2, self.rect.y, 
                               self.width + 4, self.height)
        pygame.draw.rect(self.screen, (255, 100, 255), glow_rect, 1)
    
    def can_penetrate(self):
        """检查是否还能穿透"""
        return len(self.hit_aliens) < self.penetration
    
    def add_hit_alien(self, alien):
        """添加被击中的外星人（避免重复伤害）"""
        if alien not in self.hit_aliens:
            self.hit_aliens.append(alien)

