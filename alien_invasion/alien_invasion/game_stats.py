class GameStats:
    """跟踪游戏的统计信息"""

    def __init__(self,ai_game):
        """初始化统计信息"""
        self.settings = ai_game.settings
        self.reset_stats()

        # 在任何情况下都不应重置最高分
        self.high_score = self._load_high_score()

    def reset_stats(self):
        """初始化在游戏运行期间可能变化的统计信息"""
        self.ship_left = self.settings.ship_limit
        self.score = 0
        self.level = 1
        self.combo = 0
        self.combo_timer = 0

    def _load_high_score(self):
        """从文件中读取最高分"""
        try:
            with open('high_score.txt', 'r') as f:
                return int(f.read())
        except FileNotFoundError:
            return 0
        except ValueError:
            return 0

    def save_high_score(self):
        """将最高分保存到文件"""
        with open('high_score.txt', 'w') as f:
            f.write(str(self.high_score))
    
    def update_combo(self):
        """更新连击系统"""
        # 增加连击数
        self.combo += 1
        # 重置连击计时器（连击时间窗口）
        self.combo_timer = 180  # 3秒（60帧/秒 * 3秒）
    
    def update_combo_timer(self):
        """更新连击计时器，如果超时则重置连击"""
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            if self.combo > 0:
                self.combo = 0
    
    def get_combo_multiplier(self):
        """获取连击倍数"""
        if self.combo == 0:
            return 1.0
        elif self.combo < 5:
            return 1.2
        elif self.combo < 10:
            return 1.5
        elif self.combo < 20:
            return 2.0
        else:
            return 2.5
