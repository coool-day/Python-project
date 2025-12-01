class Settings:
    """存储游戏《 Alien Invasion 》中所有设置的类"""

    def __init__(self):
        """初始化游戏的静态设置"""
        # 屏幕设置
        self.screen_width = 1200
        self.screen_height = 800
        self.bg_color = (230,230,230)

        # 飞船的设置
        self.ship_limit = 3

        # 子弹设置
        self.bullet_width = 3
        self.bullet_height = 15
        self.bullet_color = (60,60,60)
        self.bullet_allowed = 300

        # 外星人子弹设置
        self.alien_bullet_width = 3
        self.alien_bullet_height = 15
        self.alien_bullet_speed = 1.5

        # 外星人设置
        self.fleet_drop_speed = 10

        # 以什么速度加快游戏的节奏
        self.speedup_scale = 1.1
        # 外星人分数的提高速度
        self.score_scale = 1.5

        self.initialize_dynamic_settings()

    def initialize_dynamic_settings(self):
        """
        初始化随游戏进行而变化的设置
        每次新游戏或重置时调用
        """
        # 保存基础速度值（用于升级系统）
        self.base_ship_speed = 1.5
        self.base_bullet_speed = 2.5
        
        # 关卡速度倍数（随关卡提升而增加，新游戏时重置为1.0）
        self.level_speed_multiplier = 1.0
        
        self.ship_speed = self.base_ship_speed
        self.bullet_speed = self.base_bullet_speed
        self.alien_speed = 1.0

        # fleet_direction 为 1 表示向右移动，为 -1 表示向左移动
        self.fleet_direction = 1

        # 记分设置
        self.alien_points = 50

    def increase_speed(self):
        """提高速度设置的值和外星人分数"""
        # 增加关卡速度倍数
        self.level_speed_multiplier *= self.speedup_scale
        
        # 应用关卡速度倍数（升级系统会在_apply_upgrade_attributes中应用升级倍数）
        self.ship_speed = self.base_ship_speed * self.level_speed_multiplier
        self.bullet_speed = self.base_bullet_speed * self.level_speed_multiplier
        self.alien_speed *= self.speedup_scale
        self.alien_bullet_speed *= self.speedup_scale

        self.alien_points = int(self.alien_points * self.score_scale)
        print(self.alien_points)