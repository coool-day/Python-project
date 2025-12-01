"""
装备系统模块
定义装备类和装备属性
"""

import random

class Equipment:
    """装备类"""
    
    # 装备类型
    TYPE_WEAPON = "weapon"         # 武器：增加攻击力和射速
    TYPE_ARMOR = "armor"           # 护甲：增加生命上限和防御
    TYPE_ENGINE = "engine"         # 引擎：增加移动速度
    TYPE_CORE = "core"             # 能量核心：增加技能效果和能量恢复
    
    # 装备品质
    QUALITY_COMMON = "common"      # 普通（白色）
    QUALITY_RARE = "rare"          # 稀有（蓝色）
    QUALITY_EPIC = "epic"          # 史诗（紫色）
    QUALITY_LEGENDARY = "legendary"  # 传说（金色）
    
    # 品质对应的属性倍数
    QUALITY_MULTIPLIERS = {
        QUALITY_COMMON: 1.0,       # 基础属性
        QUALITY_RARE: 1.3,         # +30%
        QUALITY_EPIC: 1.6,          # +60%
        QUALITY_LEGENDARY: 2.0,     # +100%
    }
    
    # 品质对应的颜色（RGB）
    QUALITY_COLORS = {
        QUALITY_COMMON: (255, 255, 255),      # 白色
        QUALITY_RARE: (100, 150, 255),        # 蓝色
        QUALITY_EPIC: (200, 100, 255),         # 紫色
        QUALITY_LEGENDARY: (255, 215, 0),      # 金色
    }
    
    def __init__(self, equipment_type=None, quality=None, level=1):
        """
        初始化装备
        
        Args:
            equipment_type: 装备类型，如果为None则随机选择
            quality: 装备品质，如果为None则根据概率随机生成
            level: 装备等级（影响基础属性）
        """
        # 装备类型
        if equipment_type is None:
            equipment_type = random.choice([
                self.TYPE_WEAPON,
                self.TYPE_ARMOR,
                self.TYPE_ENGINE,
                self.TYPE_CORE
            ])
        self.equipment_type = equipment_type
        
        # 装备品质（根据概率生成）
        if quality is None:
            rand = random.random()
            if rand < 0.5:          # 50% 普通
                quality = self.QUALITY_COMMON
            elif rand < 0.75:       # 25% 稀有
                quality = self.QUALITY_RARE
            elif rand < 0.90:       # 15% 史诗
                quality = self.QUALITY_EPIC
            else:                   # 10% 传说
                quality = self.QUALITY_LEGENDARY
        self.quality = quality
        
        # 装备等级
        self.level = level
        
        # 品质倍数
        self.quality_multiplier = self.QUALITY_MULTIPLIERS[quality]
        
        # 根据类型和品质生成属性
        self._generate_attributes()
        
        # 装备名称
        self.name = self._generate_name()
    
    def _generate_attributes(self):
        """根据装备类型和品质生成属性"""
        # 基础属性值（根据等级）
        base_value = 10 + (self.level - 1) * 5
        
        # 根据装备类型生成不同的属性
        if self.equipment_type == self.TYPE_WEAPON:
            # 武器：攻击力、射速
            self.attack_bonus = int(base_value * self.quality_multiplier)
            self.fire_rate_bonus = int(base_value * 0.5 * self.quality_multiplier)
            self.health_bonus = 0
            self.speed_bonus = 0
            self.skill_cooldown_reduction = 0
        elif self.equipment_type == self.TYPE_ARMOR:
            # 护甲：生命上限、防御（减少伤害）
            self.attack_bonus = 0
            self.fire_rate_bonus = 0
            self.health_bonus = int(base_value * 0.8 * self.quality_multiplier)
            self.speed_bonus = 0
            self.skill_cooldown_reduction = 0
            self.defense_reduction = 0.1 * self.quality_multiplier  # 减少受到的伤害
        elif self.equipment_type == self.TYPE_ENGINE:
            # 引擎：移动速度
            self.attack_bonus = 0
            self.fire_rate_bonus = 0
            self.health_bonus = 0
            self.speed_bonus = int(base_value * 0.6 * self.quality_multiplier)
            self.skill_cooldown_reduction = 0
        elif self.equipment_type == self.TYPE_CORE:
            # 能量核心：技能冷却减少、技能效果增强
            self.attack_bonus = 0
            self.fire_rate_bonus = 0
            self.health_bonus = 0
            self.speed_bonus = 0
            self.skill_cooldown_reduction = 0.1 * self.quality_multiplier  # 减少技能冷却时间
    
    def _generate_name(self):
        """生成装备名称"""
        # 品质前缀
        quality_prefixes = {
            self.QUALITY_COMMON: "普通",
            self.QUALITY_RARE: "稀有",
            self.QUALITY_EPIC: "史诗",
            self.QUALITY_LEGENDARY: "传说"
        }
        
        # 类型名称
        type_names = {
            self.TYPE_WEAPON: "武器",
            self.TYPE_ARMOR: "护甲",
            self.TYPE_ENGINE: "引擎",
            self.TYPE_CORE: "能量核心"
        }
        
        prefix = quality_prefixes.get(self.quality, "")
        type_name = type_names.get(self.equipment_type, "")
        
        return f"{prefix}{type_name}"
    
    def get_color(self):
        """获取装备品质对应的颜色"""
        return self.QUALITY_COLORS.get(self.quality, (255, 255, 255))
    
    def get_description(self):
        """获取装备描述"""
        desc_parts = []
        
        if self.attack_bonus > 0:
            desc_parts.append(f"攻击力+{self.attack_bonus}")
        if self.fire_rate_bonus > 0:
            desc_parts.append(f"射速+{self.fire_rate_bonus}%")
        if self.health_bonus > 0:
            desc_parts.append(f"生命+{self.health_bonus}")
        if self.speed_bonus > 0:
            desc_parts.append(f"速度+{self.speed_bonus}%")
        if self.skill_cooldown_reduction > 0:
            desc_parts.append(f"技能冷却-{int(self.skill_cooldown_reduction * 100)}%")
        if hasattr(self, 'defense_reduction') and self.defense_reduction > 0:
            desc_parts.append(f"伤害减免+{int(self.defense_reduction * 100)}%")
        
        return " | ".join(desc_parts) if desc_parts else "无属性"

