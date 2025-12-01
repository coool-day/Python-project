"""
道具效果系统模块
管理各种道具的激活效果
"""

import pygame
import random
import math

class TreasureEffects:
    """道具效果管理器"""
    
    def __init__(self, ai_game):
        """初始化道具效果系统"""
        self.ai_game = ai_game
        self.settings = ai_game.settings
        self.stats = ai_game.stats
        
        # 激活的道具效果
        self.active_effects = {}
        
        # 激光效果
        self.laser_active = False
        self.laser_timer = 0
        self.laser_duration = 600  # 10秒（60帧/秒）
        
        # 护盾效果
        self.shield_active = False
        self.shield_timer = 0
        self.shield_duration = 900  # 15秒
        self.shield_hits = 0
        self.max_shield_hits = 3  # 护盾最多承受3次攻击
        
        # 导弹效果
        self.missile_active = False
        self.missile_timer = 0
        self.missile_duration = 300  # 5秒
        self.missile_cooldown = 0
        
        # 时间减缓效果
        self.slow_time_active = False
        self.slow_time_timer = 0
        self.slow_time_duration = 600  # 10秒
        self.original_alien_speed = None
        
        # 双倍分数效果
        self.double_score_active = False
        self.double_score_timer = 0
        self.double_score_duration = 900  # 15秒
    
    def activate_effect(self, treasure_type):
        """
        激活道具效果
        
        Args:
            treasure_type: 道具类型
        """
        if treasure_type == "laser":
            self.laser_active = True
            self.laser_timer = self.laser_duration
        elif treasure_type == "shield":
            self.shield_active = True
            self.shield_timer = self.shield_duration
            self.shield_hits = 0
        elif treasure_type == "missile":
            self.missile_active = True
            self.missile_timer = self.missile_duration
        elif treasure_type == "slow_time":
            self.slow_time_active = True
            self.slow_time_timer = self.slow_time_duration
            # 保存原始速度
            if self.original_alien_speed is None:
                self.original_alien_speed = self.settings.alien_speed
            # 降低外星人速度
            self.settings.alien_speed *= 0.5
        elif treasure_type == "nuke":
            # 全屏爆炸：立即清除所有外星人
            self._activate_nuke()
        elif treasure_type == "heal":
            # 生命恢复：立即恢复1条生命
            self._activate_heal()
        elif treasure_type == "double_score":
            self.double_score_active = True
            self.double_score_timer = self.double_score_duration
    
    def _activate_nuke(self):
        """激活全屏爆炸效果"""
        # 清除所有外星人
        for alien in self.ai_game.aliens.sprites():
            # 创建爆炸效果
            explosion = self.ai_game.explosions.__class__(self.ai_game, alien.rect.center)
            self.ai_game.explosions.add(explosion)
            # 播放爆炸音效
            self.ai_game.sound_manager.play_explosion()
        
        # 给予分数（每个外星人50分）
        points = len(self.ai_game.aliens) * 50
        self.stats.score += points
        
        # 清空外星人
        self.ai_game.aliens.empty()
        
        # 更新分数显示
        self.ai_game.sb.prep_score()
        self.ai_game.sb.check_high_score()
    
    def _activate_heal(self):
        """激活生命恢复效果"""
        if self.stats.ship_left < self.settings.ship_limit + (self.ai_game.upgrade_system.health_level - 1):
            self.stats.ship_left += 1
            self.ai_game.sb.prep_ship()
    
    def update(self):
        """更新所有激活的效果"""
        # 更新激光效果
        if self.laser_active:
            self.laser_timer -= 1
            if self.laser_timer <= 0:
                self.laser_active = False
        
        # 更新护盾效果
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0 or self.shield_hits >= self.max_shield_hits:
                self.shield_active = False
                self.shield_hits = 0
        
        # 更新导弹效果
        if self.missile_active:
            self.missile_timer -= 1
            self.missile_cooldown = max(0, self.missile_cooldown - 1)
            if self.missile_timer <= 0:
                self.missile_active = False
        
        # 更新时间减缓效果
        if self.slow_time_active:
            self.slow_time_timer -= 1
            if self.slow_time_timer <= 0:
                self.slow_time_active = False
                # 恢复原始速度
                if self.original_alien_speed is not None:
                    self.settings.alien_speed = self.original_alien_speed
                    self.original_alien_speed = None
        
        # 更新双倍分数效果
        if self.double_score_active:
            self.double_score_timer -= 1
            if self.double_score_timer <= 0:
                self.double_score_active = False
    
    def is_shield_active(self):
        """检查护盾是否激活"""
        return self.shield_active
    
    def hit_shield(self):
        """护盾被击中"""
        if self.shield_active:
            self.shield_hits += 1
            return True
        return False
    
    def is_laser_active(self):
        """检查激光是否激活"""
        return self.laser_active
    
    def is_missile_active(self):
        """检查导弹是否激活"""
        return self.missile_active
    
    def can_fire_missile(self):
        """检查是否可以发射导弹"""
        return self.missile_active and self.missile_cooldown <= 0
    
    def fire_missile(self):
        """发射导弹（重置冷却）"""
        self.missile_cooldown = 30  # 0.5秒冷却
    
    def get_score_multiplier(self):
        """获取分数倍数"""
        if self.double_score_active:
            return 2.0
        return 1.0
    
    def reset(self):
        """重置所有效果（新游戏时调用）"""
        self.laser_active = False
        self.shield_active = False
        self.missile_active = False
        self.slow_time_active = False
        self.double_score_active = False
        
        self.laser_timer = 0
        self.shield_timer = 0
        self.missile_timer = 0
        self.slow_time_timer = 0
        self.double_score_timer = 0
        
        if self.original_alien_speed is not None:
            self.settings.alien_speed = self.original_alien_speed
            self.original_alien_speed = None

