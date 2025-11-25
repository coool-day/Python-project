```markdown
# Alien Invasion 👾

> Python 版「外星人入侵」2D 射击小游戏 —— 60 FPS 连击 & 爆炸特效

---

## 🎮 游戏亮点
- **60 FPS** 主循环，帧率稳定
- **连击系统**：2 秒内连续击杀得分 4× 封顶
- **爆炸特效** + 音效，实时同步
- **本地高分**自动保存/读取
- **XeLaTeX 实验报告**与源码同仓，一键编译

---

## 🚀 快速开始
1. 克隆/下载本仓库
2. 安装依赖  
   ```bash
   pip install -r requirements.txt
   ```
3. 运行游戏  
   ```bash
   python main.py
   ```

---

## 📁 目录结构
```
alien_invasion/          # 游戏主程序
├── alien_invasion.py    # 入口
├── alien.py             # 外星人
├── alien_bullet.py      # 外星人的子弹
├── bullet.py            # 玩家的子弹
├── button.py            # 生成按钮
├── explosion.py         # 爆炸特效
├── game_stats.py        # 游戏数据统计
├── high_score.py        # 历史最高成绩存储
├── scoreboard.py        # 记分板
├── settings.py          # 基础设置
├── ship.py              # 玩家飞船
└── sound_manager        # 声效

report/                  # 实验报告（XeLaTeX）
├── main.tex             # 源文件
├── module.png           # 模块划分图
├── sequence.png         # 时序图
├── text.png             # 实机演示图
└── 外星人入侵_小游戏.pdf  # 已生成 PDF
```

---

## 🧪 实验报告
报告含模块划分、时序图、性能测试与心得体会，**可直接编译**：
```bash
cd report
xelatex main.tex          # 得到 main.pdf
```

---

## 📊 实测数据
- 平均帧率：60.0 ± 0.2 FPS
- 最高连击：32×
- 单场最高分：12 340

---

## 🤝 后续计划（也许......）
- [ ] Boss 关卡
- [ ] 网络排行榜
- [ ] 道具掉落系统

---

## 📄 许可
课程项目，仅供学习交流。  
提交：深圳大学人工智能学院 · Python 程序设计

---  
喜欢请  Star ！