"""
大招系统模块
管理飞船的大招充能和释放
"""

import pygame
import random
import math

class UltimateSkill:
    """大招系统类"""
    
    # 大招类型
    TYPE_NUKE = "nuke"                 # 核爆：全屏清除所有敌人
    TYPE_TIME_STOP = "time_stop"       # 时间停止：暂停所有敌人移动
    TYPE_METEOR_SHOWER = "meteor"      # 流星雨：从天而降的导弹
    TYPE_LASER_BEAM = "laser_beam"     # 激光束：持续伤害的激光
    
    def __init__(self, ai_game):
        """
        初始化大招系统
        
        Args:
            ai_game: 游戏实例
        """
        self.ai_game = ai_game
        self.settings = ai_game.settings
        self.stats = ai_game.stats
        
        # 大招充能系统
        self.aliens_killed = 0          # 击败的外星人数量
        self.charge_required = 30       # 释放大招需要击败的外星人数量
        self.charge = 0                 # 当前充能值（0-100）
        
        # 大招激活状态
        self.is_active = False
        self.active_timer = 0
        self.active_type = None
        
        # 时间停止效果
        self.time_stop_duration = 300   # 5秒
        self.original_alien_speed = None
        self.original_alien_bullet_speed = None
        
        # 流星雨效果
        self.meteor_count = 20          # 流星数量
        self.meteors_fired = 0
        
        # 激光束效果
        self.laser_beam_duration = 180  # 3秒
        self.laser_beam_active = False
    
    def add_kill(self, count=1):
        """
        添加击败的外星人数量（增加充能）
        
        Args:
            count: 击败的外星人数量
        """
        self.aliens_killed += count
        # 计算充能百分比（基于击败的外星人数量）
        # 每击败charge_required个外星人，充能达到100%
        kills_since_last_ultimate = self.aliens_killed % self.charge_required
        self.charge = min(100, int((kills_since_last_ultimate / self.charge_required) * 100))
    
    def can_use_ultimate(self):
        """
        检查是否可以释放大招
        
        Returns:
            bool: 是否可以释放
        """
        return self.charge >= 100 and not self.is_active
    
    def use_ultimate(self, ultimate_type=None):
        """
        释放大招
        
        Args:
            ultimate_type: 大招类型，None则随机选择
            
        Returns:
            bool: 是否成功释放
        """
        if not self.can_use_ultimate():
            return False
        
        # 如果没有指定类型，随机选择
        if ultimate_type is None:
            ultimate_type = random.choice([
                self.TYPE_NUKE,
                self.TYPE_TIME_STOP,
                self.TYPE_METEOR_SHOWER,
                self.TYPE_LASER_BEAM
            ])
        
        self.active_type = ultimate_type
        self.is_active = True
        
        # 消耗充能
        self.charge = 0
        
        # 根据类型执行不同的大招效果
        if ultimate_type == self.TYPE_NUKE:
            self._activate_nuke()
        elif ultimate_type == self.TYPE_TIME_STOP:
            self._activate_time_stop()
        elif ultimate_type == self.TYPE_METEOR_SHOWER:
            self._activate_meteor_shower()
        elif ultimate_type == self.TYPE_LASER_BEAM:
            self._activate_laser_beam()
        
        return True
    
    def _activate_nuke(self):
        """激活核爆大招：立即清除所有敌人"""
        aliens_list = list(self.ai_game.aliens.sprites())
        
        # 清除所有外星人并创建爆炸效果
        for alien in aliens_list:
            from explosion import Explosion
            explosion = Explosion(self.ai_game, alien.rect.center)
            self.ai_game.explosions.add(explosion)
            self.ai_game.sound_manager.play_explosion()
        
        # 给予大量分数
        points = len(aliens_list) * 100
        self.stats.score += points
        
        # 清空外星人
        self.ai_game.aliens.empty()
        
        # 更新分数显示
        self.ai_game.sb.prep_score()
        self.ai_game.sb.check_high_score()
        
        # 核爆立即完成
        self.is_active = False
    
    def _activate_time_stop(self):
        """激活时间停止：暂停所有敌人移动"""
        # 保存原始速度
        if self.original_alien_speed is None:
            self.original_alien_speed = self.settings.alien_speed
        if self.original_alien_bullet_speed is None:
            self.original_alien_bullet_speed = self.settings.alien_bullet_speed
        
        # 停止敌人移动
        self.settings.alien_speed = 0.01  # 几乎停止
        self.settings.alien_bullet_speed = 0.01
        
        # 设置持续时间
        self.active_timer = self.time_stop_duration
    
    def _activate_meteor_shower(self):
        """激活流星雨：从天而降的导弹"""
        self.meteors_fired = 0
        self.active_timer = 60  # 1秒内发射完所有流星
    
    def _activate_laser_beam(self):
        """
        激活激光束：持续伤害的激光
        在持续时间内，所有射击都会发射激光子弹
        """
        self.laser_beam_active = True
        self.active_timer = self.laser_beam_duration
    
    def update(self):
        """更新大招系统"""
        if not self.is_active:
            return
        
        # 更新时间停止效果
        if self.active_type == self.TYPE_TIME_STOP:
            self.active_timer -= 1
            if self.active_timer <= 0:
                # 恢复原始速度
                if self.original_alien_speed is not None:
                    self.settings.alien_speed = self.original_alien_speed
                    self.original_alien_speed = None
                if self.original_alien_bullet_speed is not None:
                    self.settings.alien_bullet_speed = self.original_alien_bullet_speed
                    self.original_alien_bullet_speed = None
                self.is_active = False
        
        # 更新流星雨效果
        elif self.active_type == self.TYPE_METEOR_SHOWER:
            # 每帧发射几颗流星
            if self.meteors_fired < self.meteor_count and self.active_timer > 0:
                # 每3帧发射一颗流星
                if self.active_timer % 3 == 0:
                    self._fire_meteor()
                    self.meteors_fired += 1
            self.active_timer -= 1
            if self.active_timer <= 0:
                self.is_active = False
        
        # 更新激光束效果
        elif self.active_type == self.TYPE_LASER_BEAM:
            self.active_timer -= 1
            if self.active_timer <= 0:
                self.laser_beam_active = False
                self.is_active = False
    
    def _fire_meteor(self):
        """发射一颗流星（从屏幕顶部随机位置）"""
        from missile import Missile
        
        # 在屏幕顶部随机位置生成流星
        x = random.randint(50, self.settings.screen_width - 50)
        y = -20
        
        # 创建导弹（修改初始位置）
        meteor = Missile(self.ai_game)
        meteor.rect.centerx = x
        meteor.rect.centery = y
        meteor.x = float(x)
        meteor.y = float(y)
        
        self.ai_game.missiles.add(meteor)
    
    def is_laser_beam_active(self):
        """检查激光束是否激活"""
        return self.laser_beam_active
    
    def is_time_stop_active(self):
        """检查时间停止是否激活"""
        return self.is_active and self.active_type == self.TYPE_TIME_STOP
    
    def get_charge_percentage(self):
        """
        获取充能百分比
        
        Returns:
            float: 充能百分比（0.0-1.0）
        """
        return self.charge / 100.0
    
    def get_ultimate_name(self):
        """获取当前大招名称（中文）"""
        if not self.is_active:
            return None
        
        name_map = {
            self.TYPE_NUKE: "核爆",
            self.TYPE_TIME_STOP: "时间停止",
            self.TYPE_METEOR_SHOWER: "流星雨",
            self.TYPE_LASER_BEAM: "激光束",
        }
        return name_map.get(self.active_type, "未知")
    
    def reset(self):
        """重置大招系统（新游戏时调用）"""
        self.aliens_killed = 0
        self.charge = 0
        self.is_active = False
        self.active_timer = 0
        self.laser_beam_active = False
        
        # 恢复速度（如果时间停止激活）
        if self.original_alien_speed is not None:
            self.settings.alien_speed = self.original_alien_speed
            self.original_alien_speed = None
        if self.original_alien_bullet_speed is not None:
            self.settings.alien_bullet_speed = self.original_alien_bullet_speed
            self.original_alien_bullet_speed = None

