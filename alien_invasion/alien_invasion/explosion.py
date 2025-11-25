import pygame
from pygame.sprite import Sprite

class Explosion(Sprite):
    """管理爆炸动画效果的类"""
    
    def __init__(self, ai_game, center):
        """在指定位置创建爆炸效果"""
        super().__init__()
        self.screen = ai_game.screen
        self.center = center
        
        # 爆炸动画参数
        self.frame = 0
        self.max_frames = 10  # 爆炸动画帧数
        self.animation_speed = 2  # 每2帧更新一次动画
        
        # 爆炸颜色和大小
        self.colors = [
            (255, 255, 0),   # 黄色
            (255, 165, 0),   # 橙色
            (255, 0, 0),     # 红色
            (128, 0, 0),     # 深红色
        ]
        self.max_radius = 30
        
    def update(self):
        """更新爆炸动画"""
        self.frame += 1
    
    def is_finished(self):
        """检查爆炸动画是否完成"""
        return self.frame >= self.max_frames * self.animation_speed
    
    def draw(self):
        """绘制爆炸效果"""
        if self.frame >= self.max_frames * self.animation_speed:
            return
        
        # 计算当前帧的半径和颜色
        progress = (self.frame // self.animation_speed) / self.max_frames
        radius = int(self.max_radius * progress)
        
        # 根据进度选择颜色
        color_index = min(int(progress * len(self.colors)), len(self.colors) - 1)
        color = self.colors[color_index]
        
        # 绘制多个同心圆创建爆炸效果
        for i in range(3):
            r = radius - i * 5
            if r > 0:
                alpha = 255 - int(progress * 255)
                # 使用半透明效果
                pygame.draw.circle(self.screen, color, self.center, r, 2)
                # 填充内部
                if r > 3:
                    inner_color = tuple(min(255, c + 50) for c in color)
                    pygame.draw.circle(self.screen, inner_color, self.center, r - 2)

