import pygame
import os

class SoundManager:
    """管理游戏音效的类"""
    
    def __init__(self):
        """初始化音效管理器"""
        pygame.mixer.init()
        self.sounds = {}
        self._load_sounds()
    
    def _load_sounds(self):
        """加载所有音效文件"""
        # 创建sounds目录（如果不存在）
        if not os.path.exists('sounds'):
            os.makedirs('sounds')
        
        # 尝试加载音效文件，如果不存在则使用None
        sound_files = {
            'shoot': 'sounds/shoot.wav',
            'explosion': 'sounds/explosion.wav',
            'ship_hit': 'sounds/ship_hit.wav',
        }
        
        for sound_name, sound_path in sound_files.items():
            try:
                if os.path.exists(sound_path):
                    self.sounds[sound_name] = pygame.mixer.Sound(sound_path)
                else:
                    # 如果文件不存在，创建一个静默的音效占位符
                    self.sounds[sound_name] = None
            except pygame.error:
                self.sounds[sound_name] = None
    
    def play(self, sound_name):
        """播放指定的音效"""
        if sound_name in self.sounds and self.sounds[sound_name] is not None:
            try:
                self.sounds[sound_name].play()
            except pygame.error:
                pass  # 如果播放失败，静默忽略
    
    def play_shoot(self):
        """播放射击音效"""
        self.play('shoot')
    
    def play_explosion(self):
        """播放爆炸音效"""
        self.play('explosion')
    
    def play_ship_hit(self):
        """播放飞船被击中音效"""
        self.play('ship_hit')

