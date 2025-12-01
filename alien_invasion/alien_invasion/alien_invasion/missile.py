"""
导弹类
追踪导弹，自动追踪最近的外星人
"""

import pygame
import math
from pygame.sprite import Sprite

class Missile(Sprite):
    """追踪导弹类"""
    
    def __init__(self, ai_game):
        """初始化导弹"""
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.aliens = ai_game.aliens
        
        # 导弹属性
        self.width = 8
        self.height = 15
        self.color = (255, 165, 0)  # 橙色
        self.speed = 4.0
        
        # 创建导弹矩形
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.midtop = ai_game.ship.rect.midtop
        
        # 存储精确位置
        self.x = float(self.rect.x)
        self.y = float(self.rect.y)
        
        # 目标外星人
        self.target = None
        self._find_target()
    
    def _find_target(self):
        """寻找最近的外星人作为目标"""
        if not self.aliens:
            return
        
        min_distance = float('inf')
        closest_alien = None
        
        for alien in self.aliens.sprites():
            # 计算距离
            dx = alien.rect.centerx - self.rect.centerx
            dy = alien.rect.centery - self.rect.centery
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance < min_distance:
                min_distance = distance
                closest_alien = alien
        
        self.target = closest_alien
    
    def update(self):
        """更新导弹位置（追踪目标）"""
        # 如果目标不存在或已被摧毁，寻找新目标
        if self.target is None or self.target not in self.aliens:
            self._find_target()
        
        # 如果有目标，追踪目标
        if self.target:
            # 计算方向
            dx = self.target.rect.centerx - self.rect.centerx
            dy = self.target.rect.centery - self.rect.centery
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance > 0:
                # 归一化方向向量
                dx /= distance
                dy /= distance
                
                # 移动导弹
                self.x += dx * self.speed
                self.y += dy * self.speed
        
        # 更新rect
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        
        # 如果超出屏幕，移除
        if (self.rect.bottom < 0 or 
            self.rect.top > self.settings.screen_height or
            self.rect.right < 0 or 
            self.rect.left > self.settings.screen_width):
            return True
        return False
    
    def draw(self):
        """绘制导弹"""
        # 绘制导弹主体
        pygame.draw.rect(self.screen, self.color, self.rect)
        
        # 绘制尾焰效果
        if self.target:
            # 计算尾焰方向（与移动方向相反）
            dx = self.target.rect.centerx - self.rect.centerx
            dy = self.target.rect.centery - self.rect.centery
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance > 0:
                dx /= distance
                dy /= distance
                
                # 绘制尾焰
                tail_x = self.rect.centerx - dx * 10
                tail_y = self.rect.centery - dy * 10
                pygame.draw.circle(self.screen, (255, 255, 0), 
                                 (int(tail_x), int(tail_y)), 3)

