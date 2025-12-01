"""
升级系统模块
管理玩家的经验值、等级和属性升级
"""

class UpgradeSystem:
    """管理玩家升级系统的类"""
    
    def __init__(self, ai_game):
        """初始化升级系统"""
        self.settings = ai_game.settings
        self.stats = ai_game.stats
        
        # 玩家等级相关（区别于关卡等级）
        self.player_level = 1
        self.experience = 0
        self.experience_to_next_level = 100  # 升级所需经验值
        
        # 属性升级等级（每个属性可以独立升级）
        self.attack_level = 1      # 攻击力等级
        self.fire_rate_level = 1   # 射速等级
        self.speed_level = 1       # 移动速度等级
        self.health_level = 1      # 生命上限等级
        self.bullet_count_level = 1  # 子弹数量等级
        
        # 属性加成倍数（基于等级）
        self.attack_multiplier = 1.0
        self.fire_rate_multiplier = 1.0
        self.speed_multiplier = 1.0
        
        # 计算初始属性加成
        self._update_attribute_multipliers()
    
    def add_experience(self, amount):
        """
        添加经验值
        
        Args:
            amount: 要添加的经验值数量
        """
        self.experience += amount
        
        # 检查是否升级
        while self.experience >= self.experience_to_next_level:
            self._level_up()
    
    def _level_up(self):
        """玩家升级处理"""
        # 扣除升级所需经验
        self.experience -= self.experience_to_next_level
        
        # 提升玩家等级
        self.player_level += 1
        
        # 计算下一级所需经验（递增）
        self.experience_to_next_level = int(100 * (1.2 ** (self.player_level - 1)))
        
        # 标记需要显示升级选择界面
        self.stats.show_upgrade_menu = True
    
    def upgrade_attack(self):
        """升级攻击力"""
        self.attack_level += 1
        self._update_attribute_multipliers()
    
    def upgrade_fire_rate(self):
        """升级射速"""
        self.fire_rate_level += 1
        self._update_attribute_multipliers()
    
    def upgrade_speed(self):
        """升级移动速度"""
        self.speed_level += 1
        self._update_attribute_multipliers()
    
    def upgrade_health(self):
        """升级生命上限"""
        self.health_level += 1
        # 增加当前生命数（最多增加1）
        if self.stats.ship_left < self.settings.ship_limit + (self.health_level - 1):
            self.stats.ship_left += 1
    
    def upgrade_bullet_count(self):
        """升级子弹数量"""
        self.bullet_count_level += 1
        # 增加同时可发射的子弹数量
        self.settings.bullet_allowed = min(300 + (self.bullet_count_level - 1) * 50, 500)
    
    def _update_attribute_multipliers(self):
        """更新属性加成倍数"""
        # 攻击力：每级增加10%伤害
        self.attack_multiplier = 1.0 + (self.attack_level - 1) * 0.1
        
        # 射速：每级减少5%射击间隔（增加射速）
        self.fire_rate_multiplier = 1.0 - (self.fire_rate_level - 1) * 0.05
        if self.fire_rate_multiplier < 0.3:  # 最低限制为30%
            self.fire_rate_multiplier = 0.3
        
        # 移动速度：每级增加8%速度
        self.speed_multiplier = 1.0 + (self.speed_level - 1) * 0.08
    
    def get_experience_percentage(self):
        """
        获取当前经验值百分比（用于显示经验条）
        
        Returns:
            float: 经验值百分比（0.0-1.0）
        """
        if self.experience_to_next_level == 0:
            return 1.0
        return min(self.experience / self.experience_to_next_level, 1.0)
    
    def reset(self):
        """重置升级系统（新游戏时调用）"""
        self.player_level = 1
        self.experience = 0
        self.experience_to_next_level = 100
        
        self.attack_level = 1
        self.fire_rate_level = 1
        self.speed_level = 1
        self.health_level = 1
        self.bullet_count_level = 1
        
        self._update_attribute_multipliers()
        self.settings.bullet_allowed = 300

