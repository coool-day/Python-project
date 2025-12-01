"""
宝藏/道具系统模块
管理道具的生成、掉落、拾取和效果
"""

import pygame
import random
from pygame.sprite import Sprite

class Treasure(Sprite):
    """宝藏/道具类"""
    
    # 道具类型定义
    TYPE_LASER = "laser"           # 激光：增强射击
    TYPE_SHIELD = "shield"         # 护盾：临时无敌
    TYPE_MISSILE = "missile"       # 导弹：追踪导弹
    TYPE_SLOW_TIME = "slow_time"   # 时间减缓：降低敌人速度
    TYPE_NUKE = "nuke"             # 全屏爆炸：清除所有敌人
    TYPE_HEAL = "heal"             # 生命恢复：恢复1条生命
    TYPE_DOUBLE_SCORE = "double_score"  # 双倍分数：临时双倍分数
    
    def __init__(self, ai_game, x, y, treasure_type=None):
        """
        初始化道具
        
        Args:
            ai_game: 游戏实例
            x, y: 道具生成位置
            treasure_type: 道具类型，如果为None则随机选择
        """
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        
        # 道具类型
        if treasure_type is None:
            # 随机选择道具类型（不同道具的掉落概率不同）
            rand = random.random()
            if rand < 0.25:  # 25% 激光
                self.treasure_type = self.TYPE_LASER
            elif rand < 0.40:  # 15% 护盾
                self.treasure_type = self.TYPE_SHIELD
            elif rand < 0.50:  # 10% 导弹
                self.treasure_type = self.TYPE_MISSILE
            elif rand < 0.58:  # 8% 时间减缓
                self.treasure_type = self.TYPE_SLOW_TIME
            elif rand < 0.63:  # 5% 全屏爆炸
                self.treasure_type = self.TYPE_NUKE
            elif rand < 0.80:  # 17% 生命恢复
                self.treasure_type = self.TYPE_HEAL
            else:  # 20% 双倍分数
                self.treasure_type = self.TYPE_DOUBLE_SCORE
        else:
            self.treasure_type = treasure_type
        
        # 道具属性
        self.size = 20  # 道具大小
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.rect.centerx = x
        self.rect.centery = y
        
        # 道具颜色（根据类型）
        self.color = self._get_color()
        
        # 掉落速度（缓慢向下移动）
        self.fall_speed = 1.0
        self.y = float(self.rect.y)
        
        # 闪烁效果
        self.alpha = 255
        self.alpha_direction = -5
        
        # 旋转效果
        self.rotation = 0
        
    def _get_color(self):
        """根据道具类型返回颜色"""
        color_map = {
            self.TYPE_LASER: (255, 0, 255),        # 紫色 - 激光
            self.TYPE_SHIELD: (0, 255, 255),        # 青色 - 护盾
            self.TYPE_MISSILE: (255, 165, 0),       # 橙色 - 导弹
            self.TYPE_SLOW_TIME: (0, 255, 0),       # 绿色 - 时间减缓
            self.TYPE_NUKE: (255, 0, 0),           # 红色 - 全屏爆炸
            self.TYPE_HEAL: (255, 192, 203),       # 粉色 - 生命恢复
            self.TYPE_DOUBLE_SCORE: (255, 215, 0), # 金色 - 双倍分数
        }
        return color_map.get(self.treasure_type, (255, 255, 255))
    
    def get_name(self):
        """获取道具名称（中文）"""
        name_map = {
            self.TYPE_LASER: "激光",
            self.TYPE_SHIELD: "护盾",
            self.TYPE_MISSILE: "导弹",
            self.TYPE_SLOW_TIME: "时间减缓",
            self.TYPE_NUKE: "全屏爆炸",
            self.TYPE_HEAL: "生命恢复",
            self.TYPE_DOUBLE_SCORE: "双倍分数",
        }
        return name_map.get(self.treasure_type, "未知")
    
    def update(self):
        """更新道具位置和效果"""
        # 向下移动
        self.y += self.fall_speed
        self.rect.y = int(self.y)
        
        # 闪烁效果
        self.alpha += self.alpha_direction
        if self.alpha <= 150:
            self.alpha_direction = 5
        elif self.alpha >= 255:
            self.alpha_direction = -5
        
        # 旋转效果
        self.rotation += 2
        if self.rotation >= 360:
            self.rotation = 0
        
        # 如果掉出屏幕底部，移除
        if self.rect.top > self.settings.screen_height:
            return True
        return False
    
    def draw(self):
        """绘制道具"""
        # 创建带透明度的表面
        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # 绘制道具（根据类型绘制不同形状）
        if self.treasure_type == self.TYPE_LASER:
            # 激光：绘制菱形
            points = [
                (self.size // 2, 0),
                (self.size, self.size // 2),
                (self.size // 2, self.size),
                (0, self.size // 2)
            ]
            pygame.draw.polygon(surface, self.color, points)
        elif self.treasure_type == self.TYPE_SHIELD:
            # 护盾：绘制圆形
            pygame.draw.circle(surface, self.color, (self.size // 2, self.size // 2), self.size // 2 - 2)
            pygame.draw.circle(surface, (255, 255, 255), (self.size // 2, self.size // 2), self.size // 2 - 4, 2)
        elif self.treasure_type == self.TYPE_MISSILE:
            # 导弹：绘制三角形
            points = [
                (self.size // 2, 0),
                (0, self.size),
                (self.size, self.size)
            ]
            pygame.draw.polygon(surface, self.color, points)
        elif self.treasure_type == self.TYPE_SLOW_TIME:
            # 时间减缓：绘制时钟图标（简化版）
            pygame.draw.circle(surface, self.color, (self.size // 2, self.size // 2), self.size // 2 - 2, 2)
            pygame.draw.line(surface, self.color, (self.size // 2, self.size // 2), 
                           (self.size // 2, self.size // 4), 2)
        elif self.treasure_type == self.TYPE_NUKE:
            # 全屏爆炸：绘制星形
            center = (self.size // 2, self.size // 2)
            for i in range(8):
                angle = i * 45
                import math
                x = center[0] + math.cos(math.radians(angle)) * (self.size // 2 - 2)
                y = center[1] + math.sin(math.radians(angle)) * (self.size // 2 - 2)
                pygame.draw.circle(surface, self.color, (int(x), int(y)), 2)
        elif self.treasure_type == self.TYPE_HEAL:
            # 生命恢复：绘制心形（简化版）
            pygame.draw.circle(surface, self.color, (self.size // 3, self.size // 3), self.size // 4)
            pygame.draw.circle(surface, self.color, (2 * self.size // 3, self.size // 3), self.size // 4)
            points = [
                (self.size // 2, self.size // 2),
                (0, self.size // 3),
                (self.size // 2, self.size),
                (self.size, self.size // 3)
            ]
            pygame.draw.polygon(surface, self.color, points)
        else:
            # 默认：绘制方形
            pygame.draw.rect(surface, self.color, (2, 2, self.size - 4, self.size - 4))
        
        # 设置透明度
        surface.set_alpha(self.alpha)
        
        # 绘制到屏幕
        self.screen.blit(surface, self.rect)

