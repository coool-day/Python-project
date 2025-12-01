"""
装备管理器模块
管理玩家的装备系统，包括装备生成、装备、卸下等功能
"""

import random
from equipment import Equipment

class EquipmentManager:
    """装备管理器"""
    
    def __init__(self, ai_game):
        """
        初始化装备管理器
        
        Args:
            ai_game: 游戏实例
        """
        self.ai_game = ai_game
        self.settings = ai_game.settings
        self.stats = ai_game.stats
        self.upgrade_system = ai_game.upgrade_system
        self.skill_system = ai_game.skill_system
        
        # 当前装备的装备（每个类型只能装备一个）
        self.equipped_weapon = None      # 装备的武器
        self.equipped_armor = None       # 装备的护甲
        self.equipped_engine = None      # 装备的引擎
        self.equipped_core = None        # 装备的能量核心
        
        # 背包（存储未装备的装备，最多20个）
        self.inventory = []
        self.max_inventory_size = 20
        
        # 属性加成（汇总所有装备的属性）
        self.total_attack_bonus = 0
        self.total_fire_rate_bonus = 0
        self.total_health_bonus = 0
        self.total_speed_bonus = 0
        self.total_skill_cooldown_reduction = 0.0
        self.total_defense_reduction = 0.0
        
        # 计算初始属性加成
        self._update_total_bonuses()
    
    def generate_equipment(self, equipment_type=None, quality=None, level=None):
        """
        生成一件装备
        
        Args:
            equipment_type: 装备类型，None则随机
            quality: 装备品质，None则根据概率随机
            level: 装备等级，None则根据玩家等级生成
            
        Returns:
            Equipment: 生成的装备对象
        """
        # 如果没有指定等级，根据玩家等级生成
        if level is None:
            level = max(1, self.upgrade_system.player_level)
        
        # 生成装备（Equipment类已在文件顶部导入）
        equipment = Equipment(equipment_type, quality, level)
        
        return equipment
    
    def add_to_inventory(self, equipment):
        """
        将装备添加到背包
        
        Args:
            equipment: 装备对象
            
        Returns:
            bool: 是否成功添加（背包满了返回False）
        """
        if len(self.inventory) >= self.max_inventory_size:
            return False
        
        self.inventory.append(equipment)
        return True
    
    def equip(self, equipment):
        """
        装备一件装备
        
        Args:
            equipment: 要装备的装备对象
            
        Returns:
            bool: 是否成功装备
        """
        # 根据装备类型装备到对应槽位
        if equipment.equipment_type == Equipment.TYPE_WEAPON:
            # 如果已有装备，先卸下
            if self.equipped_weapon:
                self.unequip(Equipment.TYPE_WEAPON)
            self.equipped_weapon = equipment
        elif equipment.equipment_type == Equipment.TYPE_ARMOR:
            if self.equipped_armor:
                self.unequip(Equipment.TYPE_ARMOR)
            self.equipped_armor = equipment
        elif equipment.equipment_type == Equipment.TYPE_ENGINE:
            if self.equipped_engine:
                self.unequip(Equipment.TYPE_ENGINE)
            self.equipped_engine = equipment
        elif equipment.equipment_type == Equipment.TYPE_CORE:
            if self.equipped_core:
                self.unequip(Equipment.TYPE_CORE)
            self.equipped_core = equipment
        else:
            return False
        
        # 从背包中移除（如果存在）
        if equipment in self.inventory:
            self.inventory.remove(equipment)
        
        # 更新属性加成
        self._update_total_bonuses()
        
        # 应用装备属性到游戏
        self._apply_equipment_bonuses()
        
        return True
    
    def unequip(self, equipment_type):
        """
        卸下装备
        
        Args:
            equipment_type: 装备类型
            
        Returns:
            bool: 是否成功卸下
        """
        equipment = None
        
        if equipment_type == Equipment.TYPE_WEAPON:
            equipment = self.equipped_weapon
            self.equipped_weapon = None
        elif equipment_type == Equipment.TYPE_ARMOR:
            equipment = self.equipped_armor
            self.equipped_armor = None
        elif equipment_type == Equipment.TYPE_ENGINE:
            equipment = self.equipped_engine
            self.equipped_engine = None
        elif equipment_type == Equipment.TYPE_CORE:
            equipment = self.equipped_core
            self.equipped_core = None
        else:
            return False
        
        # 如果背包未满，添加到背包
        if equipment and len(self.inventory) < self.max_inventory_size:
            self.inventory.append(equipment)
        
        # 更新属性加成
        self._update_total_bonuses()
        
        # 应用装备属性到游戏
        self._apply_equipment_bonuses()
        
        return True
    
    def _update_total_bonuses(self):
        """更新所有装备的总属性加成"""
        # 重置所有加成
        self.total_attack_bonus = 0
        self.total_fire_rate_bonus = 0
        self.total_health_bonus = 0
        self.total_speed_bonus = 0
        self.total_skill_cooldown_reduction = 0.0
        self.total_defense_reduction = 0.0
        
        # 累加所有装备的属性
        for equipment in [self.equipped_weapon, self.equipped_armor, 
                          self.equipped_engine, self.equipped_core]:
            if equipment:
                self.total_attack_bonus += equipment.attack_bonus
                self.total_fire_rate_bonus += equipment.fire_rate_bonus
                self.total_health_bonus += equipment.health_bonus
                self.total_speed_bonus += equipment.speed_bonus
                self.total_skill_cooldown_reduction += equipment.skill_cooldown_reduction
                if hasattr(equipment, 'defense_reduction'):
                    self.total_defense_reduction += equipment.defense_reduction
        
        # 限制防御减免（最高50%）
        self.total_defense_reduction = min(self.total_defense_reduction, 0.5)
    
    def _apply_equipment_bonuses(self):
        """
        应用装备属性加成到游戏系统
        注意：装备加成会与升级系统叠加
        """
        # 生命上限加成（需要更新生命数）
        if self.total_health_bonus > 0:
            # 计算应该增加的生命数
            health_increase = self.total_health_bonus // 10  # 每10点生命加成增加1条生命
            max_health = (self.settings.ship_limit + 
                         (self.upgrade_system.health_level - 1) + 
                         health_increase)
            
            # 如果当前生命数小于最大值，增加生命
            if self.stats.ship_left < max_health:
                self.stats.ship_left = min(self.stats.ship_left + 1, max_health)
                if hasattr(self.ai_game, 'sb'):
                    self.ai_game.sb.prep_ship()
        
        # 技能冷却减少（应用到技能系统）
        # 注意：这个效果在技能系统初始化时应用，这里只是更新
        # 实际的冷却减少会在技能使用时动态计算
    
    def get_equipped_equipment(self):
        """
        获取所有已装备的装备
        
        Returns:
            dict: 包含所有已装备装备的字典
        """
        return {
            Equipment.TYPE_WEAPON: self.equipped_weapon,
            Equipment.TYPE_ARMOR: self.equipped_armor,
            Equipment.TYPE_ENGINE: self.equipped_engine,
            Equipment.TYPE_CORE: self.equipped_core,
        }
    
    def get_total_bonuses(self):
        """
        获取总属性加成
        
        Returns:
            dict: 包含所有属性加成的字典
        """
        return {
            'attack': self.total_attack_bonus,
            'fire_rate': self.total_fire_rate_bonus,
            'health': self.total_health_bonus,
            'speed': self.total_speed_bonus,
            'skill_cooldown_reduction': self.total_skill_cooldown_reduction,
            'defense_reduction': self.total_defense_reduction,
        }
    
    def reset(self):
        """重置装备系统（新游戏时调用）"""
        # 清空所有装备
        self.equipped_weapon = None
        self.equipped_armor = None
        self.equipped_engine = None
        self.equipped_core = None
        
        # 清空背包
        self.inventory = []
        
        # 重置属性加成
        self._update_total_bonuses()

