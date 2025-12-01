"""
技能系统模块
管理玩家的主动技能和被动技能
"""

import pygame
import random
import math

class SkillSystem:
    """技能系统管理器"""
    
    # 主动技能类型
    ACTIVE_LASER_BEAM = "laser_beam"      # 激光束：持续伤害
    ACTIVE_MISSILE = "missile"             # 导弹：追踪导弹
    ACTIVE_SHIELD = "shield"               # 护盾：临时无敌
    ACTIVE_SLOW_TIME = "slow_time"         # 时间减缓：降低敌人速度
    ACTIVE_NUKE = "nuke"                   # 全屏爆炸：清除所有敌人
    
    # 被动技能类型
    PASSIVE_PENETRATE = "penetrate"        # 穿透：子弹可穿透敌人
    PASSIVE_SPLIT = "split"                # 分裂：子弹命中后分裂
    PASSIVE_LIFESTEAL = "lifesteal"        # 吸血：击败敌人恢复生命
    PASSIVE_CRITICAL = "critical"          # 暴击：概率造成额外伤害
    
    def __init__(self, ai_game):
        """初始化技能系统"""
        self.ai_game = ai_game
        self.settings = ai_game.settings
        self.stats = ai_game.stats
        
        # 主动技能状态
        self.active_skills = {
            self.ACTIVE_LASER_BEAM: {'unlocked': False, 'level': 0, 'cooldown': 0, 'cooldown_time': 600},  # 10秒冷却
            self.ACTIVE_MISSILE: {'unlocked': False, 'level': 0, 'cooldown': 0, 'cooldown_time': 300},      # 5秒冷却
            self.ACTIVE_SHIELD: {'unlocked': False, 'level': 0, 'cooldown': 0, 'cooldown_time': 900},      # 15秒冷却
            self.ACTIVE_SLOW_TIME: {'unlocked': False, 'level': 0, 'cooldown': 0, 'cooldown_time': 600},  # 10秒冷却
            self.ACTIVE_NUKE: {'unlocked': False, 'level': 0, 'cooldown': 0, 'cooldown_time': 1800},      # 30秒冷却
        }
        
        # 被动技能状态（必须在调用unlock_skill之前初始化）
        self.passive_skills = {
            self.PASSIVE_PENETRATE: {'unlocked': False, 'level': 0},
            self.PASSIVE_SPLIT: {'unlocked': False, 'level': 0},
            self.PASSIVE_LIFESTEAL: {'unlocked': False, 'level': 0},
            self.PASSIVE_CRITICAL: {'unlocked': False, 'level': 0},
        }
        
        # 被动技能效果（初始化默认值）
        self.penetration_count = 0  # 穿透数量
        self.split_chance = 0.0     # 分裂概率
        self.lifesteal_chance = 0.0  # 吸血概率
        self.critical_chance = 0.0   # 暴击概率
        self.critical_multiplier = 2.0  # 暴击倍数
        
        # 解锁第一个主动技能（激光束）作为初始技能
        self.unlock_skill(self.ACTIVE_LASER_BEAM, True)
        
        # 解锁第一个被动技能（穿透）作为初始技能
        self.unlock_skill(self.PASSIVE_PENETRATE, False)
        
        # 主动技能激活状态
        self.laser_beam_active = False
        self.laser_beam_timer = 0
        self.laser_beam_duration = 300  # 5秒持续时间
        
        self.shield_active = False
        self.shield_timer = 0
        self.shield_duration = 600  # 10秒持续时间
        self.shield_hits = 0
        self.max_shield_hits = 3
        
        self.slow_time_active = False
        self.slow_time_timer = 0
        self.slow_time_duration = 600  # 10秒持续时间
        self.original_alien_speed = None
    
    def unlock_skill(self, skill_type, is_active=True):
        """
        解锁技能
        
        Args:
            skill_type: 技能类型
            is_active: 是否为主动技能
        """
        if is_active:
            if skill_type in self.active_skills:
                self.active_skills[skill_type]['unlocked'] = True
                self.active_skills[skill_type]['level'] = 1
        else:
            if skill_type in self.passive_skills:
                self.passive_skills[skill_type]['unlocked'] = True
                self.passive_skills[skill_type]['level'] = 1
                self._update_passive_effects()
    
    def upgrade_skill(self, skill_type, is_active=True):
        """
        升级技能
        
        Args:
            skill_type: 技能类型
            is_active: 是否为主动技能
        """
        if is_active:
            if skill_type in self.active_skills and self.active_skills[skill_type]['unlocked']:
                self.active_skills[skill_type]['level'] += 1
                # 升级后减少冷却时间
                self.active_skills[skill_type]['cooldown_time'] = int(
                    self.active_skills[skill_type]['cooldown_time'] * 0.9
                )
        else:
            if skill_type in self.passive_skills and self.passive_skills[skill_type]['unlocked']:
                self.passive_skills[skill_type]['level'] += 1
                self._update_passive_effects()
    
    def _update_passive_effects(self):
        """更新被动技能效果"""
        # 穿透效果
        if self.passive_skills[self.PASSIVE_PENETRATE]['unlocked']:
            level = self.passive_skills[self.PASSIVE_PENETRATE]['level']
            self.penetration_count = level  # 每级增加1个穿透
        
        # 分裂效果
        if self.passive_skills[self.PASSIVE_SPLIT]['unlocked']:
            level = self.passive_skills[self.PASSIVE_SPLIT]['level']
            self.split_chance = min(0.3 + (level - 1) * 0.1, 0.8)  # 最高80%
        
        # 吸血效果
        if self.passive_skills[self.PASSIVE_LIFESTEAL]['unlocked']:
            level = self.passive_skills[self.PASSIVE_LIFESTEAL]['level']
            self.lifesteal_chance = min(0.1 + (level - 1) * 0.05, 0.3)  # 最高30%
        
        # 暴击效果
        if self.passive_skills[self.PASSIVE_CRITICAL]['unlocked']:
            level = self.passive_skills[self.PASSIVE_CRITICAL]['level']
            self.critical_chance = min(0.15 + (level - 1) * 0.05, 0.5)  # 最高50%
            self.critical_multiplier = 2.0 + (level - 1) * 0.2  # 最高3.0倍
    
    def can_use_skill(self, skill_type):
        """检查技能是否可以使用"""
        if skill_type not in self.active_skills:
            return False
        skill = self.active_skills[skill_type]
        return skill['unlocked'] and skill['cooldown'] <= 0
    
    def use_skill(self, skill_type):
        """
        使用主动技能
        
        Args:
            skill_type: 技能类型
            
        Returns:
            bool: 是否成功使用
        """
        if not self.can_use_skill(skill_type):
            return False
        
        skill = self.active_skills[skill_type]
        
        # 应用装备的冷却减少（如果有装备管理器）
        if hasattr(self.ai_game, 'equipment_manager'):
            equipment_bonuses = self.ai_game.equipment_manager.get_total_bonuses()
            cooldown_reduction = equipment_bonuses.get('skill_cooldown_reduction', 0.0)
            # 计算实际冷却时间（考虑装备加成）
            actual_cooldown = int(skill['cooldown_time'] * (1 - cooldown_reduction))
        else:
            actual_cooldown = skill['cooldown_time']
        
        skill['cooldown'] = actual_cooldown
        
        if skill_type == self.ACTIVE_LASER_BEAM:
            self.laser_beam_active = True
            self.laser_beam_timer = self.laser_beam_duration
        elif skill_type == self.ACTIVE_MISSILE:
            # 发射3枚导弹
            for _ in range(3):
                from missile import Missile
                missile = Missile(self.ai_game)
                self.ai_game.missiles.add(missile)
        elif skill_type == self.ACTIVE_SHIELD:
            self.shield_active = True
            self.shield_timer = self.shield_duration
            self.shield_hits = 0
        elif skill_type == self.ACTIVE_SLOW_TIME:
            self.slow_time_active = True
            self.slow_time_timer = self.slow_time_duration
            if self.original_alien_speed is None:
                self.original_alien_speed = self.settings.alien_speed
            self.settings.alien_speed *= 0.5
        elif skill_type == self.ACTIVE_NUKE:
            self._activate_nuke()
        
        return True
    
    def _activate_nuke(self):
        """激活全屏爆炸"""
        aliens_list = list(self.ai_game.aliens.sprites())
        
        for alien in aliens_list:
            from explosion import Explosion
            explosion = Explosion(self.ai_game, alien.rect.center)
            self.ai_game.explosions.add(explosion)
            self.ai_game.sound_manager.play_explosion()
        
        points = len(aliens_list) * 50
        self.stats.score += points
        self.ai_game.aliens.empty()
        self.ai_game.sb.prep_score()
        self.ai_game.sb.check_high_score()
    
    def update(self):
        """更新技能系统"""
        # 更新主动技能冷却时间
        for skill in self.active_skills.values():
            if skill['cooldown'] > 0:
                skill['cooldown'] -= 1
        
        # 更新激光束效果
        if self.laser_beam_active:
            self.laser_beam_timer -= 1
            if self.laser_beam_timer <= 0:
                self.laser_beam_active = False
        
        # 更新护盾效果
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0 or self.shield_hits >= self.max_shield_hits:
                self.shield_active = False
                self.shield_hits = 0
        
        # 更新时间减缓效果
        if self.slow_time_active:
            self.slow_time_timer -= 1
            if self.slow_time_timer <= 0:
                self.slow_time_active = False
                if self.original_alien_speed is not None:
                    self.settings.alien_speed = self.original_alien_speed
                    self.original_alien_speed = None
    
    def is_shield_active(self):
        """检查护盾是否激活"""
        return self.shield_active
    
    def hit_shield(self):
        """护盾被击中"""
        if self.shield_active:
            self.shield_hits += 1
            return True
        return False
    
    def is_laser_beam_active(self):
        """检查激光束是否激活"""
        return self.laser_beam_active
    
    def check_critical(self):
        """检查是否触发暴击"""
        if self.passive_skills[self.PASSIVE_CRITICAL]['unlocked']:
            return random.random() < self.critical_chance
        return False
    
    def get_critical_multiplier(self):
        """获取暴击倍数"""
        if self.check_critical():
            return self.critical_multiplier
        return 1.0
    
    def check_lifesteal(self):
        """检查是否触发吸血"""
        if self.passive_skills[self.PASSIVE_LIFESTEAL]['unlocked']:
            if random.random() < self.lifesteal_chance:
                # 恢复生命
                if self.stats.ship_left < self.settings.ship_limit + (self.ai_game.upgrade_system.health_level - 1):
                    self.stats.ship_left += 1
                    self.ai_game.sb.prep_ship()
                return True
        return False
    
    def check_split(self):
        """检查是否触发分裂"""
        if self.passive_skills[self.PASSIVE_SPLIT]['unlocked']:
            return random.random() < self.split_chance
        return False
    
    def get_penetration_count(self):
        """获取穿透数量"""
        return self.penetration_count
    
    def reset(self):
        """重置技能系统（新游戏时调用）"""
        # 重置所有技能状态
        for skill in self.active_skills.values():
            skill['cooldown'] = 0
        
        self.laser_beam_active = False
        self.shield_active = False
        self.slow_time_active = False
        
        if self.original_alien_speed is not None:
            self.settings.alien_speed = self.original_alien_speed
            self.original_alien_speed = None

