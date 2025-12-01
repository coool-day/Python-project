# Mermaid 图表说明

本项目包含三个 Mermaid 图表文件，用于展示游戏系统的类关系、系统交互和架构设计。

## 文件说明

### 1. `class_diagram.mmd` - 类关系图

**用途**：展示所有类的详细结构、属性和方法，以及类之间的继承、组合和依赖关系。

**包含内容**：
- 所有类的定义（属性、方法）
- 继承关系（Sprite 子类）
- 组合关系（AlienInvasion 包含其他类）
- 依赖关系（类之间的使用关系）

**使用方法**：
```bash
# 在支持 Mermaid 的编辑器中打开（如 VS Code + Mermaid 插件）
# 或使用在线工具：https://mermaid.live/
```

### 2. `system_flow.mmd` - 系统交互流程图

**用途**：展示游戏主循环中关键方法的调用流程和系统交互。

**包含内容**：
- 游戏初始化流程
- 主循环中的更新流程
- 碰撞检测和事件处理
- 系统间的交互（升级、技能、道具等）
- 关卡完成和宝箱奖励流程

**关键流程**：
- 击中外星人 → 获得经验 → 升级 → 显示升级菜单
- 拾取道具 → 激活效果
- 关卡完成 → 宝箱奖励

### 3. `system_architecture.mmd` - 系统架构图

**用途**：以分层架构的方式展示系统模块及其依赖关系。

**包含内容**：
- 核心控制器层（AlienInvasion）
- 配置层（Settings, GameStats）
- 游戏实体层（Ship, Alien, Bullet 等）
- 游戏系统层（升级、技能、装备、大招、道具）
- UI界面层（记分牌、菜单、界面）
- 工具层（音效、装备类）

## 如何生成图片

### 方法1：使用 Mermaid Live Editor（推荐）

1. 访问 https://mermaid.live/
2. 复制 `.mmd` 文件内容
3. 粘贴到编辑器中
4. 点击 "Actions" → "Download PNG/SVG"

### 方法2：使用 VS Code 插件

1. 安装 "Markdown Preview Mermaid Support" 插件
2. 打开 `.mmd` 文件
3. 使用预览功能查看图表
4. 右键导出为图片

### 方法3：使用命令行工具

```bash
# 安装 mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# 生成 PNG 图片
mmdc -i class_diagram.mmd -o class_diagram.png

# 生成 SVG 图片
mmdc -i class_diagram.mmd -o class_diagram.svg
```

### 方法4：在 LaTeX 中使用

如果需要在 LaTeX 报告中插入这些图表，可以使用 `mermaid` 包：

```latex
\usepackage{mermaid}
\begin{mermaid}
    %% 粘贴 mermaid 代码
\end{mermaid}
```

或者先生成图片，然后在 LaTeX 中插入：

```latex
\includegraphics[width=0.9\linewidth]{class_diagram.png}
```

## 图表说明

### 类关系图关键点

- **红色核心类**：`AlienInvasion` 是游戏的主控制器
- **蓝色系统类**：升级、技能、装备等游戏系统
- **绿色UI类**：界面相关的类
- **橙色实体类**：游戏中的实体对象

### 流程图关键点

- **绿色节点**：开始节点
- **粉色节点**：结束节点
- **黄色节点**：重要事件（击中外星人）
- **蓝色节点**：UI显示（升级菜单）
- **紫色节点**：奖励系统（宝箱）
- **橙色节点**：技能系统

### 架构图关键点

- **红色**：核心控制器
- **青色**：配置层
- **绿色**：游戏系统层
- **黄色**：UI界面层

## 建议

1. **类关系图**适合展示代码结构和设计模式
2. **流程图**适合展示游戏逻辑和系统交互
3. **架构图**适合展示整体系统设计和模块划分

可以根据需要选择合适的图表插入到实验报告中。

