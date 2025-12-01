"""
宝箱系统模块
管理宝箱的显示、开启和奖励内容
"""

import pygame
import random
from equipment import Equipment

class TreasureChest:
    """宝箱类"""
    
    # 宝箱类型
    TYPE_COMMON = "common"      # 普通宝箱（白色）
    TYPE_RARE = "rare"          # 稀有宝箱（蓝色）
    TYPE_EPIC = "epic"          # 史诗宝箱（紫色）
    TYPE_LEGENDARY = "legendary"  # 传说宝箱（金色）
    
    # 宝箱类型对应的颜色
    TYPE_COLORS = {
        TYPE_COMMON: (255, 255, 255),      # 白色
        TYPE_RARE: (100, 150, 255),        # 蓝色
        TYPE_EPIC: (200, 100, 255),         # 紫色
        TYPE_LEGENDARY: (255, 215, 0),      # 金色
    }
    
    # 宝箱类型对应的名称
    TYPE_NAMES = {
        TYPE_COMMON: "普通宝箱",
        TYPE_RARE: "稀有宝箱",
        TYPE_EPIC: "史诗宝箱",
        TYPE_LEGENDARY: "传说宝箱",
    }
    
    def __init__(self, ai_game, chest_type=None):
        """
        初始化宝箱
        
        Args:
            ai_game: 游戏实例
            chest_type: 宝箱类型，None则根据关卡等级随机生成
        """
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.stats = ai_game.stats
        
        # 如果没有指定类型，根据关卡等级随机生成
        if chest_type is None:
            chest_type = self._generate_chest_type()
        
        self.chest_type = chest_type
        self.color = self.TYPE_COLORS[chest_type]
        self.name = self.TYPE_NAMES[chest_type]
        
        # 宝箱位置（屏幕中央）
        self.rect = pygame.Rect(0, 0, 120, 100)
        self.rect.centerx = self.settings.screen_width // 2
        self.rect.centery = self.settings.screen_height // 2
        
        # 动画相关
        self.animation_frame = 0
        self.animation_speed = 0.1
        self.scale = 1.0
        self.pulse_direction = 1
        
        # 奖励内容（在开启时生成）
        self.rewards = []
        self.is_opened = False
        
        # 生成奖励内容
        self._generate_rewards()
    
    def _generate_chest_type(self):
        """
        根据关卡等级生成宝箱类型
        
        Returns:
            str: 宝箱类型
        """
        level = self.stats.level
        
        # 高品质宝箱概率随关卡增加
        weights = {
            self.TYPE_COMMON: max(0.3, 0.6 - level * 0.02),
            self.TYPE_RARE: max(0.2, 0.3 - level * 0.01),
            self.TYPE_EPIC: min(0.3, 0.1 + level * 0.01),
            self.TYPE_LEGENDARY: min(0.2, 0.05 + level * 0.005),
        }
        
        # 归一化权重
        total_weight = sum(weights.values())
        for key in weights:
            weights[key] /= total_weight
        
        # 根据权重随机选择
        rand = random.random()
        cumulative = 0
        for chest_type, weight in weights.items():
            cumulative += weight
            if rand <= cumulative:
                return chest_type
        
        return self.TYPE_COMMON
    
    def _generate_rewards(self):
        """
        根据宝箱类型生成奖励内容
        """
        self.rewards = []
        
        # 根据宝箱类型决定奖励数量和品质
        if self.chest_type == self.TYPE_COMMON:
            # 普通宝箱：1-2个奖励
            reward_count = random.randint(1, 2)
            equipment_quality = Equipment.QUALITY_COMMON
            experience_bonus = 1.0
            gold_bonus = 1.0
        elif self.chest_type == self.TYPE_RARE:
            # 稀有宝箱：2-3个奖励
            reward_count = random.randint(2, 3)
            equipment_quality = random.choice([Equipment.QUALITY_COMMON, Equipment.QUALITY_RARE])
            experience_bonus = 1.5
            gold_bonus = 1.5
        elif self.chest_type == self.TYPE_EPIC:
            # 史诗宝箱：3-4个奖励
            reward_count = random.randint(3, 4)
            equipment_quality = random.choice([Equipment.QUALITY_COMMON, Equipment.QUALITY_RARE, Equipment.QUALITY_EPIC])
            experience_bonus = 2.0
            gold_bonus = 2.0
        else:  # LEGENDARY
            # 传说宝箱：4-5个奖励
            reward_count = random.randint(4, 5)
            equipment_quality = random.choice([Equipment.QUALITY_RARE, Equipment.QUALITY_EPIC, Equipment.QUALITY_LEGENDARY])
            experience_bonus = 3.0
            gold_bonus = 3.0
        
        # 生成奖励
        for _ in range(reward_count):
            reward_type = random.choice(['equipment', 'experience', 'gold', 'skill_book'])
            
            if reward_type == 'equipment':
                # 装备奖励
                equipment = self.ai_game.equipment_manager.generate_equipment(
                    quality=equipment_quality,
                    level=max(1, self.ai_game.upgrade_system.player_level)
                )
                # 获取装备名称
                self.rewards.append({
                    'type': 'equipment',
                    'data': equipment,
                    'name': equipment.name
                })
            elif reward_type == 'experience':
                # 经验值奖励
                base_exp = 50 * max(1, self.ai_game.upgrade_system.player_level)
                exp_amount = int(base_exp * experience_bonus)
                self.rewards.append({
                    'type': 'experience',
                    'data': exp_amount,
                    'name': f'经验值 +{exp_amount}'
                })
            elif reward_type == 'gold':
                # 金币奖励（如果未来实现金币系统）
                base_gold = 100 * max(1, self.stats.level)
                gold_amount = int(base_gold * gold_bonus)
                self.rewards.append({
                    'type': 'gold',
                    'data': gold_amount,
                    'name': f'金币 +{gold_amount}'
                })
            else:  # skill_book
                # 技能书奖励（如果未来实现技能升级系统）
                self.rewards.append({
                    'type': 'skill_book',
                    'data': None,
                    'name': '技能书 x1'
                })
    
    def update(self):
        """更新宝箱动画"""
        if self.is_opened:
            return
        
        # 脉冲动画
        self.animation_frame += self.animation_speed
        if self.animation_frame >= 1.0:
            self.animation_frame = 0.0
            self.pulse_direction *= -1
        
        # 缩放动画（1.0 到 1.1）
        if self.pulse_direction > 0:
            self.scale = 1.0 + (self.animation_frame * 0.1)
        else:
            self.scale = 1.1 - (self.animation_frame * 0.1)
    
    def draw(self):
        """绘制宝箱"""
        if self.is_opened:
            return
        
        # 计算缩放后的尺寸
        scaled_width = int(self.rect.width * self.scale)
        scaled_height = int(self.rect.height * self.scale)
        scaled_rect = pygame.Rect(0, 0, scaled_width, scaled_height)
        scaled_rect.center = self.rect.center
        
        # 绘制宝箱主体（简单的矩形表示）
        pygame.draw.rect(self.screen, self.color, scaled_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), scaled_rect, 3)
        
        # 绘制宝箱装饰（锁）
        lock_size = 20
        lock_rect = pygame.Rect(0, 0, lock_size, lock_size)
        lock_rect.centerx = scaled_rect.centerx
        lock_rect.centery = scaled_rect.centery - 10
        pygame.draw.circle(self.screen, (200, 200, 200), lock_rect.center, lock_size // 2)
        pygame.draw.circle(self.screen, (0, 0, 0), lock_rect.center, lock_size // 2, 2)
        
        # 绘制宝箱名称
        def get_chinese_font(size):
            """获取支持中文的字体"""
            chinese_font_names = [
                'SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi', 'FangSong',
                'simhei', 'microsoft yahei', 'simsun', 'kaiti', 'fangsong',
            ]
            for font_name in chinese_font_names:
                try:
                    test_font = pygame.font.SysFont(font_name, size)
                    test_surface = test_font.render('测试', True, (255, 255, 255))
                    if test_surface.get_width() > 0:
                        return test_font
                except:
                    continue
            return pygame.font.SysFont(None, size)
        
        font = get_chinese_font(24)
        name_text = font.render(self.name, True, self.color)
        name_rect = name_text.get_rect()
        name_rect.centerx = scaled_rect.centerx
        name_rect.bottom = scaled_rect.top - 10
        self.screen.blit(name_text, name_rect)
    
    def open(self):
        """
        开启宝箱
        
        Returns:
            list: 奖励列表
        """
        if self.is_opened:
            return self.rewards
        
        self.is_opened = True
        return self.rewards

