import sys
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
        

        # 创建一个用于存储游戏统计信息的实例,并创建记分牌
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        # 初始化音效管理器
        self.sound_manager = SoundManager()

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.alien_bullets = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()
        
        self._create_fleet()
        
        # 用于控制外星人射击频率
        self.alien_bullet_timer = 0

        # 让游戏一开始处于非活动状态
        self.game_active = False
        self.game_paused = False

        # 创建 Play 按钮
        self.play_button = Button(self,"Play")

    def run_game(self):
        """开始游戏的主循环"""
        while True:
            self._check_events()

            if self.game_active and not self.game_paused:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()
                self._update_alien_bullets()
                self._fire_alien_bullet()
                self._update_explosions()
                # 更新连击计时器
                self.stats.update_combo_timer()

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

    def _check_play_button(self,mouse_pos):
        """在玩家单击 Play 按钮时开始新游戏"""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.game_active:
            # 还原游戏设置
            self.settings.initialize_dynamic_settings()

            # 重置游戏的统计信息
            self.stats.reset_stats()
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ship()
            self.game_active = True

            # 清空外星人、子弹和外星人子弹列表
            self.bullets.empty()
            self.aliens.empty()
            self.alien_bullets.empty()
            self.explosions.empty()

            # 重置外星人子弹计时器
            self.alien_bullet_timer = 0

            # 创建一个新的外星舰队，并将飞船放在屏幕底部
            self._create_fleet()
            self.ship.center_ship()

            #隐藏光标
            pygame.mouse.set_visible(False)
    
    def _check_keydown_events(self,event):
        """响应按下"""
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
        """创建一颗子弹，并将其加入编组 bullets """
        if len(self.bullets) < self.settings.bullet_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)
            # 播放射击音效
            self.sound_manager.play_shoot()

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
                # 计算分数（基础分数 * 连击倍数）
                base_points = self.settings.alien_points * len(aliens)
                points = int(base_points * combo_multiplier)
                self.stats.score += points
                
                # 为每个被击中的外星人创建爆炸效果
                for alien in aliens:
                    explosion = Explosion(self, alien.rect.center)
                    self.explosions.add(explosion)
                    # 播放爆炸音效
                    self.sound_manager.play_explosion()
            
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


    def _update_screen(self):
        """更新屏幕上的图像，并切换到新屏幕"""
         # 每次循环时都重新绘制屏幕
        self.screen.fill(self.settings.bg_color)
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.ship.blitme()
        self.aliens.draw(self.screen)

        # 显示得分
        self.sb.show_score()

        # 绘制外星人子弹
        for alien_bullet in self.alien_bullets.sprites():
            alien_bullet.draw_bullet()
        
        # 绘制爆炸效果
        for explosion in self.explosions.sprites():
            explosion.draw()

        # 如果游戏处于非活动状态，就绘制 Play 按钮
        if not self.game_active:
            self.play_button.draw_button()
        
        # 如果游戏暂停，显示暂停提示
        if self.game_paused:
            self._show_pause_message()

        # 让最近绘制的屏幕可见
        pygame.display.flip()

    def _create_fleet(self):
        """创建一个外星舰队"""
        
        # 创建一个外星人，再不断添加，直到没有空间添加外星人为止
        # 外星人的间距为外星人的宽度和外星人的高度
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size

        current_x, current_y = alien_width, alien_height
        while current_y < (self.settings.screen_height - 3 * alien_height):
            while current_x < (self.settings.screen_width - 2 * alien_width):
                self._create_alien(current_x,current_y)
                current_x += 2 * alien_width
            # 添加一行外星人后，重置 x 值并递增 y 值
            current_x = alien_width
            current_y += 2 * alien_height

    def _create_alien(self,x_position,y_position):
        """创建一个外星人，并将其加入外星舰队"""
        new_alien = Alien(self)
        new_alien.x = x_position
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position
        self.aliens.add(new_alien)

    def _check_fleet_edges(self):
        """在有外星人到达边缘时，采取相应的措施"""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()

    def _change_fleet_direction(self):
        """将整个舰队向下移动，并改变它们的方向"""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _update_aliens(self):
        """检查是否有外星人位于屏幕边缘，并更新整个外星舰队的位置"""
        self._check_fleet_edges()
        self.aliens.update()

        # 检测外星人和飞船之间的碰撞
        if pygame.sprite.spritecollideany(self.ship,self.aliens):
            # 重置连击（被击中时连击中断）
            self.stats.combo = 0
            self.stats.combo_timer = 0
            self._ship_hit()

        # 检查是否有外星人到达了屏幕的下边缘
        self._check_aliens_bottom()

    def _check_aliens_bottom(self):
        """检查是否有外星人到达了屏幕的下边缘"""
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= self.settings.screen_height:
                # 重置连击（被击中时连击中断）
                self.stats.combo = 0
                self.stats.combo_timer = 0
                # 像飞船被撞到一样进行处理
                self._ship_hit()
                break

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
        """显示暂停提示信息"""
        font = pygame.font.SysFont(None, 72)
        pause_text = font.render("PAUSED", True, (255, 255, 255))
        pause_rect = pause_text.get_rect()
        pause_rect.center = self.screen.get_rect().center
        
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

            # 创建一个新的外星舰队，并将飞船放在屏幕底部的中央
            self._create_fleet()
            self.ship.center_ship()

            # 暂停
            sleep(0.5)
        else:
            self.game_active = False
            pygame.mouse.set_visible(True)


if __name__ == '__main__':
    # 创建游戏实例并运行游戏
    ai = AlienInvasion();
    ai.run_game();