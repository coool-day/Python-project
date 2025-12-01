"""
升级选择界面模块
当玩家升级时显示升级选项，让玩家选择要升级的属性
"""

import pygame

class UpgradeMenu:
    """升级选择界面的类"""
    
    def __init__(self, ai_game):
        """初始化升级菜单"""
        self.screen = ai_game.screen
        self.screen_rect = self.screen.get_rect()
        self.settings = ai_game.settings
        self.upgrade_system = ai_game.upgrade_system
        self.skill_system = ai_game.skill_system
        
        # 字体设置（使用支持中文的字体）
        # 尝试使用常见的中文字体，如果不存在则使用默认字体
        def get_chinese_font(size):
            """获取支持中文的字体"""
            # Windows常见中文字体名称（尝试多种可能的名称格式）
            chinese_font_names = [
                'SimHei',           # 黑体
                'Microsoft YaHei', # 微软雅黑
                'SimSun',           # 宋体
                'KaiTi',            # 楷体
                'FangSong',         # 仿宋
                'simhei',           # 小写
                'microsoft yahei',  # 小写
                'simsun',           # 小写
                'kaiti',            # 小写
                'fangsong',         # 小写
            ]
            
            # 尝试每个字体名称
            for font_name in chinese_font_names:
                try:
                    test_font = pygame.font.SysFont(font_name, size)
                    # 测试是否能正确渲染中文
                    test_surface = test_font.render('测试', True, (255, 255, 255))
                    # 如果渲染成功且宽度合理，说明字体可用
                    if test_surface.get_width() > 0:
                        return test_font
                except:
                    continue
            
            # 如果所有中文字体都失败，尝试使用默认字体
            try:
                return pygame.font.SysFont(None, size)
            except:
                # 最后的备选方案
                return pygame.font.Font(None, size)
        
        self.title_font = get_chinese_font(72)
        self.option_font = get_chinese_font(48)
        self.desc_font = get_chinese_font(32)
        
        # 颜色设置
        self.bg_color = (0, 0, 0, 200)  # 半透明黑色背景
        self.title_color = (255, 215, 0)  # 金色标题
        self.option_color = (255, 255, 255)  # 白色选项
        self.highlight_color = (100, 200, 255)  # 高亮颜色
        self.desc_color = (200, 200, 200)  # 灰色描述
        
        # 升级选项（包含属性和技能）
        self._build_options()
        
        # 当前选中的选项索引
        self.selected_index = 0
        
        # 准备文本图像
        self._prep_texts()
    
    def _build_options(self):
        """构建升级选项列表（包含属性和技能）"""
        self.options = []
        
        # 属性升级选项
        self.options.extend([
            {
                'name': '攻击力',
                'key': '1',
                'type': 'attribute',
                'desc': f'当前等级: {self.upgrade_system.attack_level}',
                'upgrade_func': self.upgrade_system.upgrade_attack,
                'icon': '[ATK]'
            },
            {
                'name': '射速',
                'key': '2',
                'type': 'attribute',
                'desc': f'当前等级: {self.upgrade_system.fire_rate_level}',
                'upgrade_func': self.upgrade_system.upgrade_fire_rate,
                'icon': '[SPD]'
            },
            {
                'name': '移动速度',
                'key': '3',
                'type': 'attribute',
                'desc': f'当前等级: {self.upgrade_system.speed_level}',
                'upgrade_func': self.upgrade_system.upgrade_speed,
                'icon': '[MOV]'
            },
            {
                'name': '生命上限',
                'key': '4',
                'type': 'attribute',
                'desc': f'当前等级: {self.upgrade_system.health_level}',
                'upgrade_func': self.upgrade_system.upgrade_health,
                'icon': '[HP]'
            },
            {
                'name': '子弹数量',
                'key': '5',
                'type': 'attribute',
                'desc': f'当前等级: {self.upgrade_system.bullet_count_level}',
                'upgrade_func': self.upgrade_system.upgrade_bullet_count,
                'icon': '[BUL]'
            }
        ])
        
        # 主动技能选项
        active_skill_configs = [
            {
                'skill_type': self.skill_system.ACTIVE_LASER_BEAM,
                'name': '激光束',
                'key': '6',
                'icon': '[LASER]',
                'base_desc': '持续5秒的增强射击'
            },
            {
                'skill_type': self.skill_system.ACTIVE_MISSILE,
                'name': '导弹',
                'key': '7',
                'icon': '[MISSILE]',
                'base_desc': '发射3枚追踪导弹'
            },
            {
                'skill_type': self.skill_system.ACTIVE_SHIELD,
                'name': '护盾',
                'key': '8',
                'icon': '[SHIELD]',
                'base_desc': '10秒无敌，可承受3次攻击'
            },
            {
                'skill_type': self.skill_system.ACTIVE_SLOW_TIME,
                'name': '时间减缓',
                'key': '9',
                'icon': '[SLOW]',
                'base_desc': '降低敌人速度50%，持续10秒'
            },
            {
                'skill_type': self.skill_system.ACTIVE_NUKE,
                'name': '全屏爆炸',
                'key': '0',
                'icon': '[NUKE]',
                'base_desc': '清除所有敌人'
            }
        ]
        
        for config in active_skill_configs:
            skill = self.skill_system.active_skills[config['skill_type']]
            if not skill['unlocked']:
                # 未解锁的技能
                self.options.append({
                    'name': config['name'],
                    'key': config['key'],
                    'type': 'skill_unlock',
                    'skill_type': config['skill_type'],
                    'is_active': True,
                    'base_desc': config.get('base_desc', config.get('desc', '')),
                    'desc': f'解锁技能 - {config.get("base_desc", config.get("desc", ""))}',
                    'upgrade_func': lambda st=config['skill_type']: self.skill_system.unlock_skill(st, True),
                    'icon': config['icon']
                })
            else:
                # 已解锁的技能，可以升级
                self.options.append({
                    'name': config['name'],
                    'key': config['key'],
                    'type': 'skill_upgrade',
                    'skill_type': config['skill_type'],
                    'is_active': True,
                    'base_desc': config.get('base_desc', config.get('desc', '')),
                    'desc': f'等级: {skill["level"]} - {config.get("base_desc", config.get("desc", ""))}',
                    'upgrade_func': lambda st=config['skill_type']: self.skill_system.upgrade_skill(st, True),
                    'icon': config['icon']
                })
        
        # 被动技能选项
        passive_skill_configs = [
            {
                'skill_type': self.skill_system.PASSIVE_PENETRATE,
                'name': '穿透',
                'key': 'Q',
                'icon': '[PEN]',
                'base_desc': '子弹可穿透多个敌人'
            },
            {
                'skill_type': self.skill_system.PASSIVE_SPLIT,
                'name': '分裂',
                'key': 'W',
                'icon': '[SPLIT]',
                'base_desc': '子弹命中后概率分裂'
            },
            {
                'skill_type': self.skill_system.PASSIVE_LIFESTEAL,
                'name': '吸血',
                'key': 'E',
                'icon': '[LIFE]',
                'base_desc': '击败敌人概率恢复生命'
            },
            {
                'skill_type': self.skill_system.PASSIVE_CRITICAL,
                'name': '暴击',
                'key': 'R',
                'icon': '[CRIT]',
                'base_desc': '概率造成额外伤害'
            }
        ]
        
        for config in passive_skill_configs:
            skill = self.skill_system.passive_skills[config['skill_type']]
            if not skill['unlocked']:
                # 未解锁的技能
                self.options.append({
                    'name': config['name'],
                    'key': config['key'],
                    'type': 'skill_unlock',
                    'skill_type': config['skill_type'],
                    'is_active': False,
                    'base_desc': config.get('base_desc', config.get('desc', '')),
                    'desc': f'解锁技能 - {config.get("base_desc", config.get("desc", ""))}',
                    'upgrade_func': lambda st=config['skill_type']: self.skill_system.unlock_skill(st, False),
                    'icon': config['icon']
                })
            else:
                # 已解锁的技能，可以升级
                self.options.append({
                    'name': config['name'],
                    'key': config['key'],
                    'type': 'skill_upgrade',
                    'skill_type': config['skill_type'],
                    'is_active': False,
                    'base_desc': config.get('base_desc', config.get('desc', '')),
                    'desc': f'等级: {skill["level"]} - {config.get("base_desc", config.get("desc", ""))}',
                    'upgrade_func': lambda st=config['skill_type']: self.skill_system.upgrade_skill(st, False),
                    'icon': config['icon']
                })
    
    def _prep_texts(self):
        """准备所有文本图像"""
        self._update_title()
        
        # 提示文字
        self.hint_image = self.desc_font.render(
            "选择要升级的属性或技能（按数字键/字母键或方向键选择，空格键确认）",
            True, self.desc_color
        )
        self.hint_rect = self.hint_image.get_rect()
        self.hint_rect.centerx = self.screen_rect.centerx
        self.hint_rect.top = self.title_rect.bottom + 30
        
        # 选项图像（会在draw时更新）
        self.option_images = []
        self.option_rects = []
        self._update_option_texts()
    
    def _update_title(self):
        """更新标题文本（当玩家等级变化时）"""
        # 标题
        self.title_image = self.title_font.render(
            f"升级！等级 {self.upgrade_system.player_level}", 
            True, self.title_color
        )
        self.title_rect = self.title_image.get_rect()
        self.title_rect.centerx = self.screen_rect.centerx
        self.title_rect.top = 150
    
    def _update_option_texts(self):
        """更新选项文本（当等级变化时）"""
        # 重新构建选项列表（因为技能状态可能变化）
        self._build_options()
        
        self.option_images = []
        self.option_rects = []
        
        start_y = self.hint_rect.bottom + 50
        spacing = 50  # 减小间距以容纳更多选项
        
        for i, option in enumerate(self.options):
            # 更新属性描述
            if option['type'] == 'attribute':
                if option['name'] == '攻击力':
                    option['desc'] = f'当前等级: {self.upgrade_system.attack_level} (+{int((self.upgrade_system.attack_level - 1) * 10)}%伤害)'
                elif option['name'] == '射速':
                    option['desc'] = f'当前等级: {self.upgrade_system.fire_rate_level} (+{int((self.upgrade_system.fire_rate_level - 1) * 5)}%射速)'
                elif option['name'] == '移动速度':
                    option['desc'] = f'当前等级: {self.upgrade_system.speed_level} (+{int((self.upgrade_system.speed_level - 1) * 8)}%速度)'
                elif option['name'] == '生命上限':
                    option['desc'] = f'当前等级: {self.upgrade_system.health_level} (生命+{self.upgrade_system.health_level - 1})'
                elif option['name'] == '子弹数量':
                    option['desc'] = f'当前等级: {self.upgrade_system.bullet_count_level} (上限+{50 * (self.upgrade_system.bullet_count_level - 1)})'
            elif option['type'] == 'skill_upgrade':
                # 更新技能等级信息
                if option['is_active']:
                    skill = self.skill_system.active_skills[option['skill_type']]
                    option['desc'] = f'等级: {skill["level"]} - {option.get("base_desc", option["desc"])}'
                else:
                    skill = self.skill_system.passive_skills[option['skill_type']]
                    option['desc'] = f'等级: {skill["level"]} - {option.get("base_desc", option["desc"])}'
            
            # 选项文本
            key_text = option['key']
            if len(key_text) == 1 and key_text.isalpha():
                key_text = key_text.upper()
            text = f"{key_text}. {option['icon']} {option['name']} - {option['desc']}"
            
            # 根据类型选择颜色
            if i == self.selected_index:
                color = self.highlight_color
            elif option['type'] == 'skill_unlock':
                color = (255, 215, 0)  # 金色 - 未解锁技能
            elif option['type'] == 'skill_upgrade':
                color = (100, 255, 100)  # 浅绿色 - 已解锁技能
            else:
                color = self.option_color
            
            option_image = self.option_font.render(text, True, color)
            option_rect = option_image.get_rect()
            option_rect.centerx = self.screen_rect.centerx
            option_rect.top = start_y + i * spacing
            
            self.option_images.append(option_image)
            self.option_rects.append(option_rect)
    
    def handle_keydown(self, event):
        """
        处理按键事件
        
        Args:
            event: pygame事件对象
            
        Returns:
            bool: 如果选择了升级选项返回True，否则返回False
        """
        # 数字键选择
        if event.key == pygame.K_1:
            return self._select_option_by_key('1')
        elif event.key == pygame.K_2:
            return self._select_option_by_key('2')
        elif event.key == pygame.K_3:
            return self._select_option_by_key('3')
        elif event.key == pygame.K_4:
            return self._select_option_by_key('4')
        elif event.key == pygame.K_5:
            return self._select_option_by_key('5')
        elif event.key == pygame.K_6:
            return self._select_option_by_key('6')
        elif event.key == pygame.K_7:
            return self._select_option_by_key('7')
        elif event.key == pygame.K_8:
            return self._select_option_by_key('8')
        elif event.key == pygame.K_9:
            return self._select_option_by_key('9')
        elif event.key == pygame.K_0:
            return self._select_option_by_key('0')
        # 字母键选择（被动技能）
        elif event.key == pygame.K_q:
            return self._select_option_by_key('Q')
        elif event.key == pygame.K_w:
            return self._select_option_by_key('W')
        elif event.key == pygame.K_e:
            return self._select_option_by_key('E')
        elif event.key == pygame.K_r:
            return self._select_option_by_key('R')
        
        # 方向键选择
        elif event.key == pygame.K_UP:
            self.selected_index = (self.selected_index - 1) % len(self.options)
            self._update_option_texts()
        elif event.key == pygame.K_DOWN:
            self.selected_index = (self.selected_index + 1) % len(self.options)
            self._update_option_texts()
        
        # 空格键确认
        elif event.key == pygame.K_SPACE:
            return self._select_option(self.selected_index)
        
        return False
    
    def _select_option_by_key(self, key):
        """根据按键选择选项"""
        for i, option in enumerate(self.options):
            if option['key'].upper() == key.upper():
                return self._select_option(i)
        return False
    
    def _select_option(self, index):
        """
        选择升级选项
        
        Args:
            index: 选项索引
            
        Returns:
            bool: 总是返回True（表示已选择）
        """
        if 0 <= index < len(self.options):
            option = self.options[index]
            # 执行升级函数
            option['upgrade_func']()
            # 更新选项文本
            self._update_option_texts()
            return True
        return False
    
    def draw(self):
        """绘制升级菜单"""
        # 更新标题（确保显示最新等级）
        self._update_title()
        
        # 绘制半透明背景
        overlay = pygame.Surface(
            (self.settings.screen_width, self.settings.screen_height)
        )
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # 绘制标题
        self.screen.blit(self.title_image, self.title_rect)
        
        # 绘制提示
        self.screen.blit(self.hint_image, self.hint_rect)
        
        # 绘制选项
        for image, rect in zip(self.option_images, self.option_rects):
            self.screen.blit(image, rect)
        
        # 绘制选中指示器
        if self.option_rects:
            selected_rect = self.option_rects[self.selected_index]
            # 绘制高亮框
            highlight_rect = pygame.Rect(
                selected_rect.left - 10,
                selected_rect.top - 5,
                selected_rect.width + 20,
                selected_rect.height + 10
            )
            pygame.draw.rect(self.screen, self.highlight_color, highlight_rect, 3)

