import sys
import random
from time import sleep

import pygame

import alien
from settings import Settings
from game_stats import GameStats
from scoreboard import Scoreboard
from button import Button
from ship import Ship
from bullet import Bullet
from alien import Alien
from alien_bullet import AlienBullet
from sound_manager import SoundManager
from explosion import Explosion
from upgrade_system import UpgradeSystem
from upgrade_menu import UpgradeMenu
from treasure import Treasure
from treasure_effects import TreasureEffects
from missile import Missile
from laser_bullet import LaserBullet
from skill_system import SkillSystem
from equipment_manager import EquipmentManager
from equipment import Equipment
from ultimate_skill import UltimateSkill
from treasure_chest import TreasureChest
from chest_reward_ui import ChestRewardUI
from start_screen import StartScreen

class AlienInvasion:
    """管理游戏资源和行为的类"""

    def __init__(self):
        """初始化游戏并创建游戏资源"""
        pygame.init()
        # 指定游戏帧率
        self.clock = pygame.time.Clock()
        self.settings = Settings()        

        # 指定游戏窗口尺寸
        self.screen=pygame.display.set_mode(
            (self.settings.screen_width,self.settings.screen_height))
        pygame.display.set_caption("Alien Invasion")
        

        # 创建一个用于存储游戏统计信息的实例
        self.stats = GameStats(self)
        
        # 初始化升级系统（需要在Scoreboard之前初始化，因为Scoreboard需要访问它）
        self.upgrade_system = UpgradeSystem(self)
        
        # 初始化技能系统
        self.skill_system = SkillSystem(self)
        
        # 初始化装备管理器
        self.equipment_manager = EquipmentManager(self)
        
        # 初始化大招系统
        self.ultimate_skill = UltimateSkill(self)
        
        # 创建记分牌（需要在upgrade_system之后初始化）
        self.sb = Scoreboard(self)
        
        # 初始化升级菜单
        self.upgrade_menu = UpgradeMenu(self)
        
        # 初始化宝箱奖励界面
        self.chest_reward_ui = ChestRewardUI(self)

        # 初始化音效管理器
        self.sound_manager = SoundManager()

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.alien_bullets = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()
        self.treasures = pygame.sprite.Group()  # 道具组
        self.missiles = pygame.sprite.Group()   # 导弹组
        self.laser_bullets = pygame.sprite.Group()  # 激光子弹组
        
        # 初始化道具效果系统
        self.treasure_effects = TreasureEffects(self)
        
        self._create_fleet()
        
        # 用于控制外星人射击频率
        self.alien_bullet_timer = 0
        
        # 用于控制玩家射击频率（射速升级相关）
        self.bullet_cooldown = 0
        self.base_bullet_cooldown = 10  # 基础射击冷却时间（帧数）

        # 让游戏一开始处于非活动状态
        self.game_active = False
        self.game_paused = False

        # 创建开始界面
        self.start_screen = StartScreen(self)
        
        # 创建 Play 按钮（美化版）
        self.play_button = Button(self, "开始游戏")

    def run_game(self):
        """开始游戏的主循环"""
        while True:
            self._check_events()

            # 更新宝箱奖励界面（无论游戏是否暂停都需要更新动画）
            self.chest_reward_ui.update()
            # 如果奖励界面关闭，恢复游戏
            if not self.chest_reward_ui.is_showing and self.game_paused:
                self.game_paused = False
            
            if self.game_active and not self.game_paused:
                # 如果显示升级菜单，不更新游戏逻辑
                if not self.stats.show_upgrade_menu:
                    self.ship.update()
                    self._update_bullets()
                    self._update_aliens()
                    self._update_alien_bullets()
                    self._fire_alien_bullet()
                    self._update_explosions()
                    self._update_treasures()
                    self._update_missiles()
                    self._update_laser_bullets()
                    self._check_treasure_collisions()
                    # 更新连击计时器
                    self.stats.update_combo_timer()
                    # 更新射击冷却
                    if self.bullet_cooldown > 0:
                        self.bullet_cooldown -= 1
                    # 更新道具效果
                    self.treasure_effects.update()
                    # 更新技能系统
                    self.skill_system.update()
                    # 更新大招系统
                    self.ultimate_skill.update()
                    # 应用升级后的属性
                    self._apply_upgrade_attributes()

            self._update_screen()
            self.clock.tick(60)

    def _check_events(self):
        """响应按键和鼠标事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stats.save_high_score()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)
            elif event.type == pygame.MOUSEMOTION:
                # 检查按钮悬停效果
                if not self.game_active:
                    mouse_pos = pygame.mouse.get_pos()
                    self.play_button.check_hover(mouse_pos)

    def _check_play_button(self,mouse_pos):
        """在玩家单击 Play 按钮时开始新游戏"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.game_active:
            # 还原游戏设置
            self.settings.initialize_dynamic_settings()

            # 重置游戏的统计信息
            self.stats.reset_stats()
            # 重置升级系统
            self.upgrade_system.reset()
            # 重置技能系统
            self.skill_system.reset()
            # 重置装备系统
            self.equipment_manager.reset()
            # 重置大招系统
            self.ultimate_skill.reset()
            # 重置道具效果
            self.treasure_effects.reset()
            # 重置射击冷却
            self.bullet_cooldown = 0
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ship()
            self.game_active = True

            # 清空外星人、子弹和外星人子弹列表
            self.bullets.empty()
            self.aliens.empty()
            self.alien_bullets.empty()
            self.explosions.empty()
            self.treasures.empty()
            self.missiles.empty()
            self.laser_bullets.empty()

            # 重置外星人子弹计时器
            self.alien_bullet_timer = 0

            # 创建一个新的外星舰队，并将飞船放在屏幕底部
            self._create_fleet()
            self.ship.center_ship()

            #隐藏光标
            pygame.mouse.set_visible(False)
    
    def _check_keydown_events(self,event):
        """响应按下"""
        # 如果游戏未开始，按空格键开始游戏
        if not self.game_active:
            if event.key == pygame.K_SPACE:
                # 模拟点击Play按钮
                self._check_play_button(self.screen_rect.center)
            return
        
        # 处理宝箱奖励界面按键
        if self.chest_reward_ui.handle_keydown(event):
            # 如果奖励界面关闭，恢复游戏
            if not self.chest_reward_ui.is_showing:
                self.game_paused = False
            return
        
        # 如果显示升级菜单，优先处理升级菜单的按键
        if self.stats.show_upgrade_menu:
            if self.upgrade_menu.handle_keydown(event):
                # 选择了升级选项，关闭升级菜单
                self.stats.show_upgrade_menu = False
                # 更新记分牌（生命数可能变化）
                self.sb.prep_ship()
            return
        
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_UP:
            self.ship.moving_up = True
        elif event.key == pygame.K_DOWN:
            self.ship.moving_down = True
        elif event.key == pygame.K_q:
            self.stats.save_high_score()
            pygame.quit()
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()
        elif event.key == pygame.K_p:
            self._toggle_pause()
        # 主动技能按键（1-5，但需要避免与升级菜单冲突）
        elif event.key == pygame.K_1 and not self.stats.show_upgrade_menu:
            self.skill_system.use_skill(SkillSystem.ACTIVE_LASER_BEAM)
        elif event.key == pygame.K_2 and not self.stats.show_upgrade_menu:
            self.skill_system.use_skill(SkillSystem.ACTIVE_MISSILE)
        elif event.key == pygame.K_3 and not self.stats.show_upgrade_menu:
            self.skill_system.use_skill(SkillSystem.ACTIVE_SHIELD)
        elif event.key == pygame.K_4 and not self.stats.show_upgrade_menu:
            self.skill_system.use_skill(SkillSystem.ACTIVE_SLOW_TIME)
        elif event.key == pygame.K_5 and not self.stats.show_upgrade_menu:
            self.skill_system.use_skill(SkillSystem.ACTIVE_NUKE)
        # 大招按键（U键）
        elif event.key == pygame.K_u and not self.stats.show_upgrade_menu:
            self.ultimate_skill.use_ultimate()

    def _check_keyup_events(self,event):
        """响应释放"""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False
        elif event.key == pygame.K_UP:
            self.ship.moving_up = False
        elif event.key == pygame.K_DOWN:
            self.ship.moving_down = False

    def _fire_bullet(self):
        """创建子弹（根据激活的道具效果选择子弹类型）"""
        # 检查射击冷却时间（射速升级相关）
        if self.bullet_cooldown > 0:
            return
        
        # 如果激光效果激活（道具、技能或大招），发射激光子弹
        if (self.treasure_effects.is_laser_active() or 
            self.skill_system.is_laser_beam_active() or 
            self.ultimate_skill.is_laser_beam_active()):
            if len(self.laser_bullets) < 50:  # 激光子弹上限
                new_laser = LaserBullet(self)
                self.laser_bullets.add(new_laser)
                # 播放射击音效
                self.sound_manager.play_shoot()
                # 激光冷却时间更短
                cooldown_multiplier = self.upgrade_system.fire_rate_multiplier * 0.7
                self.bullet_cooldown = int(self.base_bullet_cooldown * cooldown_multiplier)
        # 如果导弹效果激活，发射导弹
        elif self.treasure_effects.can_fire_missile():
            new_missile = Missile(self)
            self.missiles.add(new_missile)
            self.treasure_effects.fire_missile()
            # 播放射击音效
            self.sound_manager.play_shoot()
            # 导弹冷却时间
            self.bullet_cooldown = 20
        # 普通子弹
        else:
            if len(self.bullets) < self.settings.bullet_allowed:
                new_bullet = Bullet(self)
                self.bullets.add(new_bullet)
                # 播放射击音效
                self.sound_manager.play_shoot()
                # 设置射击冷却时间（根据射速升级和装备加成调整）
                equipment_bonuses = self.equipment_manager.get_total_bonuses()
                fire_rate_bonus = 1.0 - (equipment_bonuses['fire_rate'] / 100.0)
                fire_rate_bonus = max(0.3, fire_rate_bonus)  # 最低限制为30%
                cooldown_multiplier = self.upgrade_system.fire_rate_multiplier * fire_rate_bonus
                self.bullet_cooldown = int(self.base_bullet_cooldown * cooldown_multiplier)

    def _update_bullets(self):
        """更新子弹的位置并删除已消失的子弹"""
        # 更新子弹的位置
        self.bullets.update()

        # 删除已消失的子弹
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        
        self._check_bullet_alien_collisions()


    def _check_bullet_alien_collisions(self):
        """响应子弹和外星人的碰撞"""
        # 删除发生碰撞的子弹和外星人
        collisions = pygame.sprite.groupcollide(
            self.bullets,self.aliens,True,True)

        if collisions:
            # 更新连击
            self.stats.update_combo()
            # 获取连击倍数
            combo_multiplier = self.stats.get_combo_multiplier()
            
            for aliens in collisions.values():
                # 计算分数（基础分数 * 连击倍数 * 道具倍数 * 暴击倍数 * 装备攻击加成）
                base_points = self.settings.alien_points * len(aliens)
                critical_multiplier = self.skill_system.get_critical_multiplier()
                equipment_bonuses = self.equipment_manager.get_total_bonuses()
                attack_bonus_multiplier = 1.0 + (equipment_bonuses['attack'] / 100.0)  # 装备攻击加成影响分数
                score_multiplier = (combo_multiplier * 
                                  self.treasure_effects.get_score_multiplier() * 
                                  critical_multiplier * 
                                  attack_bonus_multiplier)
                points = int(base_points * score_multiplier)
                self.stats.score += points
                
                # 为每个被击中的外星人创建爆炸效果
                for alien in aliens:
                    explosion = Explosion(self, alien.rect.center)
                    self.explosions.add(explosion)
                    # 播放爆炸音效
                    self.sound_manager.play_explosion()
                    
                    # 检查被动技能：吸血
                    self.skill_system.check_lifesteal()
                    
                    # 检查被动技能：分裂（在敌人位置生成分裂子弹）
                    if self.skill_system.check_split():
                        # 创建分裂子弹（向两侧发射）
                        for angle in [-30, 30]:
                            import math
                            split_bullet = Bullet(self)
                            split_bullet.rect.centerx = alien.rect.centerx
                            split_bullet.rect.centery = alien.rect.centery
                            # 设置分裂子弹的方向（简化处理，向上但带角度）
                            self.bullets.add(split_bullet)
                    
                    # 随机掉落道具（15%概率）
                    if random.random() < 0.15:
                        treasure = Treasure(self, alien.rect.centerx, alien.rect.centery)
                        self.treasures.add(treasure)
                
                # 击败外星人获得经验值（每个外星人10点经验）
                exp_gained = 10 * len(aliens)
                self.upgrade_system.add_experience(exp_gained)
                
                # 增加大招充能（每个外星人增加充能）
                self.ultimate_skill.add_kill(len(aliens))
            
            self.sb.prep_score()
            self.sb.check_high_score()

        if not self.aliens:
            # 删除现有的子弹并创建一个新的外星舰队
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            # 提高等级
            self.stats.level += 1
            self.sb.prep_level()
            
            # 通关奖励：宝箱系统（每5关必得，其他关卡30%概率）
            if self.stats.level % 5 == 0 or random.random() < 0.3:
                self._reward_chest()


    def _update_screen(self):
        """更新屏幕上的图像，并切换到新屏幕"""
         # 每次循环时都重新绘制屏幕
        self.screen.fill(self.settings.bg_color)
        
        # 绘制子弹
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        
        # 绘制激光子弹
        for laser in self.laser_bullets.sprites():
            laser.draw()
        
        # 绘制导弹
        for missile in self.missiles.sprites():
            missile.draw()
        
        # 绘制飞船
        self.ship.blitme()
        
        # 绘制护盾效果（如果激活，道具或技能）
        if self.treasure_effects.is_shield_active() or self.skill_system.is_shield_active():
            shield_rect = pygame.Rect(
                self.ship.rect.x - 5,
                self.ship.rect.y - 5,
                self.ship.rect.width + 10,
                self.ship.rect.height + 10
            )
            pygame.draw.ellipse(self.screen, (0, 255, 255), shield_rect, 3)
        
        # 绘制外星人
        self.aliens.draw(self.screen)

        # 显示得分
        self.sb.show_score()

        # 绘制外星人子弹
        for alien_bullet in self.alien_bullets.sprites():
            alien_bullet.draw_bullet()
        
        # 绘制道具
        for treasure in self.treasures.sprites():
            treasure.draw()
        
        # 绘制爆炸效果
        for explosion in self.explosions.sprites():
            explosion.draw()
        
        # 绘制激活的道具效果提示
        self._draw_active_effects()
        # 绘制技能系统UI
        self._draw_skills_ui()
        # 绘制装备系统UI
        self._draw_equipment_ui()
        # 绘制大招系统UI
        self._draw_ultimate_ui()
        
        # 绘制宝箱奖励界面（如果正在显示）
        self.chest_reward_ui.draw()

        # 如果游戏处于非活动状态，绘制开始界面和 Play 按钮
        if not self.game_active:
            self.start_screen.draw()
            self.play_button.draw_button()
        
        # 如果游戏暂停，显示暂停提示
        if self.game_paused:
            self._show_pause_message()
        
        # 如果显示升级菜单，绘制升级菜单
        if self.stats.show_upgrade_menu:
            self.upgrade_menu.draw()

        # 让最近绘制的屏幕可见
        pygame.display.flip()
    
    def _draw_active_effects(self):
        """绘制激活的道具效果提示"""
        active_effects = []
        font = pygame.font.SysFont(None, 24)
        
        # 检查各种效果
        if self.treasure_effects.laser_active:
            remaining = self.treasure_effects.laser_timer // 60
            active_effects.append(f"激光: {remaining}秒")
        
        if self.treasure_effects.shield_active:
            remaining = self.treasure_effects.shield_timer // 60
            hits_left = self.treasure_effects.max_shield_hits - self.treasure_effects.shield_hits
            active_effects.append(f"护盾: {remaining}秒 ({hits_left}次)")
        
        if self.treasure_effects.missile_active:
            remaining = self.treasure_effects.missile_timer // 60
            active_effects.append(f"导弹: {remaining}秒")
        
        if self.treasure_effects.slow_time_active:
            remaining = self.treasure_effects.slow_time_timer // 60
            active_effects.append(f"时间减缓: {remaining}秒")
        
        if self.treasure_effects.double_score_active:
            remaining = self.treasure_effects.double_score_timer // 60
            active_effects.append(f"双倍分数: {remaining}秒")
        
        # 绘制效果提示（在屏幕左上角）
        y_offset = 200
        for i, effect_text in enumerate(active_effects):
            text_surface = font.render(effect_text, True, (255, 255, 0))
            self.screen.blit(text_surface, (20, y_offset + i * 25))
    
    def _draw_skills_ui(self):
        """绘制技能系统UI（显示技能冷却时间和激活状态）"""
        font = pygame.font.SysFont(None, 20)
        skill_names = {
            SkillSystem.ACTIVE_LASER_BEAM: "1-激光束",
            SkillSystem.ACTIVE_MISSILE: "2-导弹",
            SkillSystem.ACTIVE_SHIELD: "3-护盾",
            SkillSystem.ACTIVE_SLOW_TIME: "4-时间减缓",
            SkillSystem.ACTIVE_NUKE: "5-全屏爆炸",
        }
        
        # 在屏幕右下角显示技能状态
        start_x = self.settings.screen_width - 200
        start_y = self.settings.screen_height - 150
        
        y_offset = 0
        for skill_type, skill_name in skill_names.items():
            skill = self.skill_system.active_skills[skill_type]
            
            if skill['unlocked']:
                # 计算冷却时间
                cooldown_sec = skill['cooldown'] // 60
                
                # 检查是否激活
                is_active = False
                if skill_type == SkillSystem.ACTIVE_LASER_BEAM and self.skill_system.laser_beam_active:
                    is_active = True
                elif skill_type == SkillSystem.ACTIVE_SHIELD and self.skill_system.shield_active:
                    is_active = True
                elif skill_type == SkillSystem.ACTIVE_SLOW_TIME and self.skill_system.slow_time_active:
                    is_active = True
                
                # 选择颜色
                if is_active:
                    color = (0, 255, 0)  # 绿色 - 激活中
                elif skill['cooldown'] > 0:
                    color = (200, 200, 200)  # 灰色 - 冷却中
                else:
                    color = (255, 255, 255)  # 白色 - 可用
                
                # 显示技能名称和状态
                if skill['cooldown'] > 0:
                    text = f"{skill_name}: {cooldown_sec}秒"
                elif is_active:
                    text = f"{skill_name}: 激活中"
                else:
                    text = f"{skill_name}: 就绪"
                
                text_surface = font.render(text, True, color)
                self.screen.blit(text_surface, (start_x, start_y + y_offset))
                y_offset += 22
    
    def _reward_chest(self):
        """
        通关奖励：生成宝箱并显示奖励界面
        """
        # 创建宝箱（根据关卡等级自动生成类型）
        chest = TreasureChest(self)
        
        # 开启宝箱并获取奖励
        rewards = chest.open()
        
        # 显示奖励界面
        self.chest_reward_ui.show_rewards(rewards)
        
        # 暂停游戏直到奖励界面关闭
        self.game_paused = True
    
    def _reward_equipment(self):
        """
        通关奖励：生成并自动装备一件装备（已废弃，改用宝箱系统）
        保留此方法以保持向后兼容
        """
        # 根据关卡等级决定装备品质概率
        level = self.stats.level
        
        # 高品质装备概率随关卡增加
        quality_weights = {
            Equipment.QUALITY_COMMON: max(0.3, 0.6 - level * 0.02),
            Equipment.QUALITY_RARE: max(0.2, 0.3 - level * 0.01),
            Equipment.QUALITY_EPIC: min(0.3, 0.1 + level * 0.01),
            Equipment.QUALITY_LEGENDARY: min(0.2, 0.05 + level * 0.005),
        }
        
        # 根据权重随机选择品质
        rand = random.random()
        cumulative = 0
        selected_quality = Equipment.QUALITY_COMMON
        for quality, weight in quality_weights.items():
            cumulative += weight
            if rand <= cumulative:
                selected_quality = quality
                break
        
        # 生成装备
        equipment = self.equipment_manager.generate_equipment(
            quality=selected_quality,
            level=max(1, self.upgrade_system.player_level)
        )
        
        # 自动装备（如果该类型已有装备，则替换）
        self.equipment_manager.equip(equipment)
    
    def _draw_equipment_ui(self):
        """绘制装备系统UI（显示当前装备的装备）"""
        font = pygame.font.SysFont(None, 18)
        
        # 在屏幕左下角显示装备信息
        start_x = 20
        start_y = self.settings.screen_height - 120
        
        # 标题
        title_font = pygame.font.SysFont(None, 22)
        title_text = title_font.render("装备:", True, (255, 255, 255))
        self.screen.blit(title_text, (start_x, start_y))
        start_y += 25
        
        # 显示已装备的装备
        equipped = self.equipment_manager.get_equipped_equipment()
        slot_names = {
            Equipment.TYPE_WEAPON: "武器",
            Equipment.TYPE_ARMOR: "护甲",
            Equipment.TYPE_ENGINE: "引擎",
            Equipment.TYPE_CORE: "核心",
        }
        
        y_offset = 0
        for slot_type, slot_name in slot_names.items():
            equipment = equipped[slot_type]
            if equipment:
                # 获取装备颜色
                color = equipment.get_color()
                text = f"{slot_name}: {equipment.name}"
            else:
                color = (150, 150, 150)  # 灰色 - 未装备
                text = f"{slot_name}: 未装备"
            
            text_surface = font.render(text, True, color)
            self.screen.blit(text_surface, (start_x, start_y + y_offset))
            y_offset += 20
    
    def _draw_ultimate_ui(self):
        """绘制大招系统UI（显示充能条和状态）"""
        # 在屏幕底部中央显示大招充能条
        bar_width = 300
        bar_height = 30
        bar_x = (self.settings.screen_width - bar_width) // 2
        bar_y = self.settings.screen_height - 60
        
        # 获取充能百分比
        charge_percentage = self.ultimate_skill.get_charge_percentage()
        
        # 绘制充能条背景
        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, (50, 50, 50), bg_rect)  # 深灰色背景
        pygame.draw.rect(self.screen, (100, 100, 100), bg_rect, 2)  # 边框
        
        # 绘制充能条填充
        fill_width = int(bar_width * charge_percentage)
        if fill_width > 0:
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            # 根据充能百分比使用不同颜色
            if charge_percentage < 0.5:
                fill_color = (100, 100, 255)  # 蓝色
            elif charge_percentage < 1.0:
                fill_color = (255, 200, 100)  # 橙色
            else:
                fill_color = (255, 0, 0)  # 红色（已满）
            pygame.draw.rect(self.screen, fill_color, fill_rect)
        
        # 绘制充能文本（使用支持中文的字体）
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
        if self.ultimate_skill.can_use_ultimate():
            text = "大招就绪！按U键释放"
            text_color = (255, 255, 0)  # 黄色
        else:
            killed = self.ultimate_skill.aliens_killed % self.ultimate_skill.charge_required
            required = self.ultimate_skill.charge_required
            text = f"大招充能: {self.ultimate_skill.charge}% ({killed}/{required})"
            text_color = (255, 255, 255)  # 白色
        
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect()
        text_rect.centerx = bar_x + bar_width // 2
        text_rect.bottom = bar_y - 5
        self.screen.blit(text_surface, text_rect)
        
        # 如果大招激活，显示激活状态
        if self.ultimate_skill.is_active:
            ultimate_name = self.ultimate_skill.get_ultimate_name()
            if ultimate_name:
                active_font = get_chinese_font(32)
                active_text = active_font.render(f"大招激活: {ultimate_name}!", True, (255, 215, 0))
                active_rect = active_text.get_rect()
                active_rect.centerx = self.settings.screen_width // 2
                active_rect.top = 50
                self.screen.blit(active_text, active_rect)

    def _create_fleet(self):
        """创建一个外星舰队（根据关卡等级调整数量）"""
        # 清空现有的外星人
        self.aliens.empty()
        
        # 根据关卡等级计算外星人数量
        # 基础数量 + 每级增加的数量
        base_alien_count = 12  # 第1关的基础数量
        aliens_per_level = 3   # 每级增加的外星人数量
        total_aliens = base_alien_count + (self.stats.level - 1) * aliens_per_level
        # 限制最大数量，避免过多
        max_aliens = 40
        total_aliens = min(total_aliens, max_aliens)
        
        # 创建一个外星人用于获取尺寸
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size

        # 计算可以放置外星人的区域
        available_width = self.settings.screen_width - 2 * alien_width
        available_height = self.settings.screen_height - 3 * alien_height
        
        # 随机生成外星人位置
        aliens_created = 0
        attempts = 0
        max_attempts = total_aliens * 10  # 防止无限循环
        
        while aliens_created < total_aliens and attempts < max_attempts:
            attempts += 1
            # 随机位置（主要在屏幕上半部分）
            x = random.randint(alien_width, int(available_width))
            y = random.randint(alien_height, int(available_height * 0.6))  # 只在上半部分生成
            
            # 检查是否与现有外星人重叠
            new_alien = Alien(self)
            new_alien.rect.x = x
            new_alien.rect.y = y
            new_alien.x = float(x)
            new_alien.y = float(y)
            
            # 检查重叠
            overlap = False
            for existing_alien in self.aliens.sprites():
                if new_alien.rect.colliderect(existing_alien.rect):
                    overlap = True
                    break
            
            if not overlap:
                self.aliens.add(new_alien)
                aliens_created += 1

    def _create_alien(self,x_position,y_position):
        """创建一个外星人，并将其加入外星舰队（已弃用，改用_spawn_new_alien）"""
        new_alien = Alien(self)
        new_alien.x = x_position
        new_alien.y = float(y_position)
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position
        self.aliens.add(new_alien)
    
    def _spawn_new_alien(self):
        """在屏幕顶部随机位置生成一个新的外星人"""
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        
        # 在屏幕顶部区域随机生成
        x = random.randint(alien_width, self.settings.screen_width - alien_width)
        y = random.randint(alien_height, int(self.settings.screen_height * 0.3))  # 在屏幕顶部30%区域
        
        alien.x = float(x)
        alien.y = float(y)
        alien.rect.x = x
        alien.rect.y = y
        
        self.aliens.add(alien)

    def _check_fleet_edges(self):
        """检查外星人是否到达边缘（已弃用，现在每个外星人独立处理边缘）"""
        # 这个方法现在不再需要，因为每个外星人独立处理边缘碰撞
        pass

    def _change_fleet_direction(self):
        """改变舰队方向（已弃用，现在每个外星人独立移动）"""
        # 这个方法现在不再需要
        pass

    def _update_aliens(self):
        """检查是否有外星人位于屏幕边缘，并更新整个外星舰队的位置"""
        # 更新所有外星人的位置（每个外星人独立移动）
        self.aliens.update()

        # 检测外星人和飞船之间的碰撞
        if pygame.sprite.spritecollideany(self.ship,self.aliens):
            # 检查是否有护盾（道具或技能）
            if self.treasure_effects.hit_shield() or self.skill_system.hit_shield():
                # 护盾吸收了伤害
                pass
            else:
                # 重置连击（被击中时连击中断）
                self.stats.combo = 0
                self.stats.combo_timer = 0
                self._ship_hit()

        # 检查是否有外星人到达了屏幕的下边缘（移除并生成新的）
        self._check_aliens_bottom()
        
        # 如果外星人数量过少（少于预期数量的50%），补充一些
        expected_count = 12 + (self.stats.level - 1) * 3
        expected_count = min(expected_count, 40)
        if len(self.aliens) < expected_count * 0.5:
            # 补充外星人到预期数量
            while len(self.aliens) < expected_count:
                self._spawn_new_alien()

    def _check_aliens_bottom(self):
        """检查是否有外星人到达了屏幕的下边缘"""
        aliens_to_remove = []
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= self.settings.screen_height:
                # 标记为需要移除
                aliens_to_remove.append(alien)
        
        # 移除到达底部的外星人
        if aliens_to_remove:
            for alien in aliens_to_remove:
                self.aliens.remove(alien)
            
            # 在屏幕顶部随机位置生成新的外星人（保持外星人数量）
            for _ in range(len(aliens_to_remove)):
                self._spawn_new_alien()

    def _update_alien_bullets(self):
        """更新外星人子弹的位置并删除已消失的子弹"""
        # 更新外星人子弹的位置
        self.alien_bullets.update()

        # 删除已消失的子弹
        for alien_bullet in self.alien_bullets.copy():
            if alien_bullet.rect.top >= self.settings.screen_height:
                self.alien_bullets.remove(alien_bullet)
        
        # 检测外星人子弹与飞船的碰撞
        collisions = pygame.sprite.spritecollide(self.ship, self.alien_bullets, True)
        if collisions:
            # 检查是否有护盾（道具或技能）
            if self.treasure_effects.hit_shield() or self.skill_system.hit_shield():
                # 护盾吸收了伤害
                pass
            else:
                # 检查装备防御减免
                equipment_bonuses = self.equipment_manager.get_total_bonuses()
                if equipment_bonuses['defense_reduction'] > 0:
                    # 有防御减免，概率免疫伤害
                    if random.random() < equipment_bonuses['defense_reduction']:
                        # 完全免疫这次伤害
                        pass
                    else:
                        # 重置连击（被击中时连击中断）
                        self.stats.combo = 0
                        self.stats.combo_timer = 0
                        self._ship_hit()
                else:
                    # 重置连击（被击中时连击中断）
                    self.stats.combo = 0
                    self.stats.combo_timer = 0
                    self._ship_hit()

    def _fire_alien_bullet(self):
        """让一个随机的外星人发射子弹"""
        import random
        # 每隔一定时间，随机选择一个外星人射击
        self.alien_bullet_timer += 1
        if self.alien_bullet_timer >= 60 and len(self.aliens) > 0:  # 每60帧（约1秒）射击一次
            # 随机选择一个外星人
            shooting_alien = random.choice(self.aliens.sprites())
            new_alien_bullet = AlienBullet(self, shooting_alien)
            self.alien_bullets.add(new_alien_bullet)
            self.alien_bullet_timer = 0

    def _update_explosions(self):
        """更新爆炸动画"""
        self.explosions.update()
        
        # 删除已完成的爆炸动画
        explosions_to_remove = [
            explosion for explosion in self.explosions.sprites()
            if explosion.is_finished()
        ]
        for explosion in explosions_to_remove:
            self.explosions.remove(explosion)
    
    def _toggle_pause(self):
        """切换游戏暂停状态"""
        if self.game_active:
            self.game_paused = not self.game_paused
    
    def _show_pause_message(self):
        """显示暂停提示信息（美化版）"""
        # 获取支持中文的字体
        def get_chinese_font(size):
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
        
        # 绘制半透明背景
        overlay = pygame.Surface((self.settings.screen_width, self.settings.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # 暂停文字
        font = get_chinese_font(72)
        pause_text = font.render("游戏暂停", True, (255, 215, 0))
        pause_rect = pause_text.get_rect()
        pause_rect.centerx = self.screen.get_rect().centerx
        pause_rect.centery = self.screen.get_rect().centery - 30
        
        # 提示文字
        hint_font = get_chinese_font(32)
        hint_text = hint_font.render("按 P 键继续游戏", True, (200, 200, 200))
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = self.screen.get_rect().centerx
        hint_rect.top = pause_rect.bottom + 20
        
        self.screen.blit(pause_text, pause_rect)
        self.screen.blit(hint_text, hint_rect)
        
        # 创建半透明背景
        overlay = pygame.Surface((self.settings.screen_width, self.settings.screen_height))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # 显示暂停文字
        self.screen.blit(pause_text, pause_rect)
        
        # 显示提示信息
        hint_font = pygame.font.SysFont(None, 36)
        hint_text = hint_font.render("Press P to continue", True, (200, 200, 200))
        hint_rect = hint_text.get_rect()
        hint_rect.centerx = pause_rect.centerx
        hint_rect.top = pause_rect.bottom + 20
        self.screen.blit(hint_text, hint_rect)
    
    def _apply_upgrade_attributes(self):
        """
        应用升级后的属性到游戏设置
        注意：需要同时考虑关卡速度倍数、升级倍数和装备加成
        """
        # 获取装备加成
        equipment_bonuses = self.equipment_manager.get_total_bonuses()
        
        # 应用移动速度（基础速度 * 关卡倍数 * 升级倍数 * 装备加成）
        speed_multiplier = (1.0 + equipment_bonuses['speed'] / 100.0)  # 装备速度加成转换为倍数
        self.settings.ship_speed = (
            self.settings.base_ship_speed 
            * self.settings.level_speed_multiplier 
            * self.upgrade_system.speed_multiplier
            * speed_multiplier
        )
        
        # 应用攻击力（影响子弹速度，体现为更强的穿透力）
        attack_multiplier = (1.0 + equipment_bonuses['attack'] / 100.0)  # 装备攻击加成转换为倍数
        self.settings.bullet_speed = (
            self.settings.base_bullet_speed 
            * self.settings.level_speed_multiplier 
            * self.upgrade_system.attack_multiplier
            * attack_multiplier
        )
        
        # 应用射速加成（装备的射速加成）
        if equipment_bonuses['fire_rate'] > 0:
            # 射速加成会减少射击冷却时间
            fire_rate_bonus = 1.0 - (equipment_bonuses['fire_rate'] / 100.0)
            # 这个加成会在_fire_bullet中应用
    
    def _update_treasures(self):
        """更新道具位置"""
        for treasure in self.treasures.copy():
            if treasure.update():
                self.treasures.remove(treasure)
    
    def _check_treasure_collisions(self):
        """检测道具与飞船的碰撞（拾取道具）"""
        collisions = pygame.sprite.spritecollide(self.ship, self.treasures, True)
        for treasure in collisions:
            # 激活道具效果
            self.treasure_effects.activate_effect(treasure.treasure_type)
            # 播放拾取音效（如果有）
            # self.sound_manager.play_treasure_pickup()
    
    def _update_missiles(self):
        """更新导弹位置并检测碰撞"""
        for missile in self.missiles.copy():
            if missile.update():
                self.missiles.remove(missile)
        
        # 检测导弹与外星人的碰撞
        collisions = pygame.sprite.groupcollide(self.missiles, self.aliens, True, True)
        if collisions:
            for aliens in collisions.values():
                for alien in aliens:
                    explosion = Explosion(self, alien.rect.center)
                    self.explosions.add(explosion)
                    self.sound_manager.play_explosion()
                    
                    # 计算分数
                    base_points = self.settings.alien_points
                    score_multiplier = self.treasure_effects.get_score_multiplier()
                    points = int(base_points * score_multiplier)
                    self.stats.score += points
                    
                    # 获得经验
                    self.upgrade_system.add_experience(10)
                    
                    # 增加大招充能
                    self.ultimate_skill.add_kill(1)
            
            self.sb.prep_score()
            self.sb.check_high_score()
    
    def _update_laser_bullets(self):
        """更新激光子弹位置并检测碰撞"""
        for laser in self.laser_bullets.copy():
            if laser.update():
                self.laser_bullets.remove(laser)
        
        # 检测激光与外星人的碰撞（激光可以穿透）
        score_updated = False
        for laser in self.laser_bullets.sprites():
            if not laser.can_penetrate():
                continue
            
            # 检测碰撞
            hit_aliens = pygame.sprite.spritecollide(laser, self.aliens, False)
            for alien in hit_aliens:
                if alien not in laser.hit_aliens:
                    # 标记为已击中
                    laser.add_hit_alien(alien)
                    
                    # 移除外星人
                    self.aliens.remove(alien)
                    
                    # 创建爆炸效果
                    explosion = Explosion(self, alien.rect.center)
                    self.explosions.add(explosion)
                    self.sound_manager.play_explosion()
                    
                    # 计算分数
                    base_points = self.settings.alien_points
                    score_multiplier = self.treasure_effects.get_score_multiplier()
                    points = int(base_points * score_multiplier)
                    self.stats.score += points
                    score_updated = True
                    
                    # 获得经验
                    self.upgrade_system.add_experience(10)
                    
                    # 如果不能再穿透，移除激光
                    if not laser.can_penetrate():
                        self.laser_bullets.remove(laser)
                        break
        
        # 更新分数显示
        if score_updated:
            self.sb.prep_score()
            self.sb.check_high_score()
    
    def _ship_hit(self):
        """响应飞船和外星人的碰撞"""
        # 播放飞船被击中音效
        self.sound_manager.play_ship_hit()
        
        if self.stats.ship_left > 0:
            # 将 ship_left 减 1
            self.stats.ship_left -= 1
            self.sb.prep_ship()

            # 清空外星人列表、子弹列表和外星人子弹列表
            self.bullets.empty()
            self.aliens.empty()
            self.alien_bullets.empty()
            self.explosions.empty()
            self.treasures.empty()
            self.missiles.empty()
            self.laser_bullets.empty()

            # 创建一个新的外星舰队，并将飞船放在屏幕底部的中央
            self._create_fleet()
            self.ship.center_ship()
            
            # 重置道具效果
            self.treasure_effects.reset()
            # 重置技能系统（保留装备）
            self.skill_system.reset()

            # 暂停
            sleep(0.5)
        else:
            self.game_active = False
            pygame.mouse.set_visible(True)


if __name__ == '__main__':
    # 创建游戏实例并运行游戏
    ai = AlienInvasion()
    ai.run_game()