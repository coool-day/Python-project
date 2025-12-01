"""
宝箱奖励界面模块
显示宝箱开启动画和奖励内容
"""

import pygame
import random
import math
from equipment import Equipment

class ChestRewardUI:
    """宝箱奖励界面类"""
    
    def __init__(self, ai_game):
        """
        初始化宝箱奖励界面
        
        Args:
            ai_game: 游戏实例
        """
        self.ai_game = ai_game
        self.screen = ai_game.screen
        self.settings = ai_game.settings
        self.stats = ai_game.stats
        
        # 字体设置（支持中文）
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
        
        self.title_font = get_chinese_font(48)
        self.reward_font = get_chinese_font(32)
        self.hint_font = get_chinese_font(24)
        
        # 颜色设置
        self.bg_color = (0, 0, 0, 200)  # 半透明黑色背景
        self.title_color = (255, 215, 0)  # 金色标题
        self.reward_color = (255, 255, 255)  # 白色奖励文本
        
        # 动画状态
        self.is_showing = False
        self.animation_timer = 0
        self.animation_duration = 180  # 3秒（60帧/秒）
        self.rewards = []
        self.reward_animations = []  # 奖励动画状态
        
        # 粒子效果
        self.particles = []
    
    def show_rewards(self, rewards):
        """
        显示奖励界面
        
        Args:
            rewards: 奖励列表
        """
        self.rewards = rewards
        self.is_showing = True
        self.animation_timer = 0
        
        # 初始化奖励动画
        self.reward_animations = []
        for i, reward in enumerate(rewards):
            self.reward_animations.append({
                'index': i,
                'alpha': 0,
                'y_offset': 50,
                'scale': 0.5,
                'delay': i * 10,  # 每个奖励延迟显示
            })
        
        # 创建粒子效果
        self._create_particles()
    
    def _create_particles(self):
        """创建开启宝箱的粒子效果"""
        self.particles = []
        center_x = self.settings.screen_width // 2
        center_y = self.settings.screen_height // 2
        
        # 创建50个粒子
        for _ in range(50):
            angle = random.uniform(0, 2 * 3.14159)
            speed = random.uniform(2, 8)
            color = random.choice([
                (255, 215, 0),  # 金色
                (255, 255, 255),  # 白色
                (200, 100, 255),  # 紫色
                (100, 150, 255),  # 蓝色
            ])
            
            # 计算速度分量（使用三角函数）
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            
            self.particles.append({
                'x': center_x,
                'y': center_y,
                'vx': vx,
                'vy': vy,
                'color': color,
                'life': 60,  # 粒子生命周期
                'max_life': 60,
            })
    
    def update(self):
        """更新奖励界面动画"""
        if not self.is_showing:
            return
        
        self.animation_timer += 1
        
        # 更新奖励动画
        for anim in self.reward_animations:
            if self.animation_timer >= anim['delay']:
                # 淡入动画
                if anim['alpha'] < 255:
                    anim['alpha'] = min(255, anim['alpha'] + 15)
                
                # 上移动画
                if anim['y_offset'] > 0:
                    anim['y_offset'] = max(0, anim['y_offset'] - 2)
                
                # 缩放动画
                if anim['scale'] < 1.0:
                    anim['scale'] = min(1.0, anim['scale'] + 0.05)
        
        # 更新粒子效果
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            
            # 移除死亡粒子
            if particle['life'] <= 0:
                self.particles.remove(particle)
        
        # 检查是否结束显示
        if self.animation_timer >= self.animation_duration:
            self.is_showing = False
            self._apply_rewards()
    
    def _apply_rewards(self):
        """应用奖励到游戏系统"""
        for reward in self.rewards:
            if reward['type'] == 'equipment':
                # 装备奖励：添加到背包或自动装备
                equipment = reward['data']
                if not self.ai_game.equipment_manager.add_to_inventory(equipment):
                    # 如果背包满了，尝试自动装备
                    self.ai_game.equipment_manager.equip(equipment)
            elif reward['type'] == 'experience':
                # 经验值奖励
                exp_amount = reward['data']
                self.ai_game.upgrade_system.add_experience(exp_amount)
            elif reward['type'] == 'gold':
                # 金币奖励（如果未来实现金币系统）
                # gold_amount = reward['data']
                pass
            elif reward['type'] == 'skill_book':
                # 技能书奖励（如果未来实现技能升级系统）
                pass
    
    def handle_keydown(self, event):
        """
        处理按键事件
        
        Args:
            event: pygame事件对象
            
        Returns:
            bool: 是否处理了事件
        """
        if not self.is_showing:
            return False
        
        # 按空格键或回车键跳过动画
        if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
            self.animation_timer = self.animation_duration - 1
            return True
        
        return False
    
    def draw(self):
        """绘制奖励界面"""
        if not self.is_showing:
            return
        
        # 绘制半透明背景
        bg_surface = pygame.Surface((self.settings.screen_width, self.settings.screen_height))
        bg_surface.set_alpha(200)
        bg_surface.fill((0, 0, 0))
        self.screen.blit(bg_surface, (0, 0))
        
        # 绘制粒子效果
        for particle in self.particles:
            alpha = int(255 * (particle['life'] / particle['max_life']))
            color = particle['color']
            if alpha > 0:
                pygame.draw.circle(
                    self.screen,
                    color,
                    (int(particle['x']), int(particle['y'])),
                    3
                )
        
        # 绘制标题
        title_text = self.title_font.render("宝箱开启！", True, self.title_color)
        title_rect = title_text.get_rect()
        title_rect.centerx = self.settings.screen_width // 2
        title_rect.top = 100
        self.screen.blit(title_text, title_rect)
        
        # 绘制奖励列表
        start_y = 250
        y_spacing = 60
        
        for i, reward in enumerate(self.rewards):
            anim = self.reward_animations[i]
            
            # 如果还在延迟中，跳过
            if self.animation_timer < anim['delay']:
                continue
            
            # 创建带透明度的表面
            reward_surface = pygame.Surface((600, 50), pygame.SRCALPHA)
            
            # 绘制奖励文本
            reward_text = self.reward_font.render(
                f"获得：{reward['name']}",
                True,
                self.reward_color
            )
            
            # 应用透明度
            reward_text.set_alpha(anim['alpha'])
            
            # 计算位置（带动画偏移）
            reward_rect = reward_text.get_rect()
            reward_rect.centerx = self.settings.screen_width // 2
            reward_rect.centery = start_y + i * y_spacing + anim['y_offset']
            
            # 绘制奖励图标（根据类型）
            icon_size = 40
            icon_x = reward_rect.left - 60
            icon_y = reward_rect.centery - icon_size // 2
            
            if reward['type'] == 'equipment':
                # 装备图标（根据品质显示颜色）
                equipment = reward['data']
                color = Equipment.QUALITY_COLORS.get(equipment.quality, (255, 255, 255))
                pygame.draw.rect(
                    self.screen,
                    color,
                    (icon_x, icon_y, icon_size, icon_size),
                    3
                )
            elif reward['type'] == 'experience':
                # 经验值图标（黄色星星）
                pygame.draw.polygon(
                    self.screen,
                    (255, 215, 0),
                    [
                        (icon_x + icon_size // 2, icon_y),
                        (icon_x + icon_size * 0.7, icon_y + icon_size * 0.3),
                        (icon_x + icon_size, icon_y + icon_size * 0.3),
                        (icon_x + icon_size * 0.75, icon_y + icon_size * 0.5),
                        (icon_x + icon_size * 0.85, icon_y + icon_size),
                        (icon_x + icon_size // 2, icon_y + icon_size * 0.7),
                        (icon_x + icon_size * 0.15, icon_y + icon_size),
                        (icon_x + icon_size * 0.25, icon_y + icon_size * 0.5),
                        (icon_x, icon_y + icon_size * 0.3),
                        (icon_x + icon_size * 0.3, icon_y + icon_size * 0.3),
                    ]
                )
            elif reward['type'] == 'gold':
                # 金币图标（金色圆圈）
                pygame.draw.circle(
                    self.screen,
                    (255, 215, 0),
                    (icon_x + icon_size // 2, icon_y + icon_size // 2),
                    icon_size // 2,
                    3
                )
            else:  # skill_book
                # 技能书图标（紫色书本）
                pygame.draw.rect(
                    self.screen,
                    (200, 100, 255),
                    (icon_x, icon_y, icon_size, icon_size),
                    3
                )
            
            # 绘制奖励文本
            self.screen.blit(reward_text, reward_rect)
        
        # 绘制提示文本
        if self.animation_timer > 60:  # 1秒后显示提示
            hint_text = self.hint_font.render(
                "按空格键或回车键继续",
                True,
                (200, 200, 200)
            )
            hint_rect = hint_text.get_rect()
            hint_rect.centerx = self.settings.screen_width // 2
            hint_rect.bottom = self.settings.screen_height - 50
            self.screen.blit(hint_text, hint_rect)

