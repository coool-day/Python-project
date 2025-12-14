# ============================================================================
# Iris Flower Classification & Visualization (Academic Standard - Optimized)
# 完美解决中文字体、布局重叠、3D点云杂乱问题
# ============================================================================

# 1. IMPORTS + 中文字体配置
# ============================================================================
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os

# === 1. 先设置 Seaborn 样式 (必须在字体设置之前！) ===
# Seaborn 会重置 rcParams，所以必须先运行这一行
sns.set_style('whitegrid')

# === 2. 强制加载中文字体文件 (终极方案) ===
# Windows 字体路径 (微软雅黑)
font_path = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts', 'msyh.ttc')

if os.path.exists(font_path):
    # 强制将字体文件添加到 Matplotlib 管理器
    fm.fontManager.addfont(font_path)
    # 获取字体的准确内部名称
    custom_font = fm.FontProperties(fname=font_path)
    custom_font_name = custom_font.get_name()
    
    # 设置 Matplotlib 优先使用该字体
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = [custom_font_name, 'sans-serif']
    print(f"✅ 已强制加载字体文件: {font_path} (名称: {custom_font_name})")
else:
    # 回退方案
    print("⚠️ 未找到字体文件，尝试使用名称回退")
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']

# === 3. 其他通用配置 ===
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示异常
plt.rcParams['font.size'] = 10

# === 4. Plotly 字体配置 ===
CHINESE_FONT_FAMILY = "Microsoft YaHei, SimHei, sans-serif"
PLOTLY_FONT = dict(family=CHINESE_FONT_FAMILY, color='black')
PLOTLY_TITLE_FONT = dict(family=CHINESE_FONT_FAMILY, size=18, color='black')

# 定义Set1调色板颜色（学术标准配色）
SET1_COLORS = sns.color_palette("Set1", 3).as_hex()  # Setosa, Versicolor, Virginica

# 中文特征名映射
FEATURE_NAMES_CN = {
    'sepal length (cm)': '萼片长度 (cm)',
    'sepal width (cm)': '萼片宽度 (cm)',
    'petal length (cm)': '花瓣长度 (cm)',
    'petal width (cm)': '花瓣宽度 (cm)'
}

# ============================================================================
# 2. DATA LOADING AND EXPLORATORY VISUALIZATION
# ============================================================================
# 加载Iris数据集
iris = load_iris()
X = iris.data
y = iris.target
feature_names = iris.feature_names
target_names = iris.target_names

# 创建DataFrame便于可视化
df = pd.DataFrame(X, columns=[FEATURE_NAMES_CN[f] for f in feature_names])
df['物种'] = pd.Categorical.from_codes(y, target_names)

print("=" * 80)
print("数据集基本信息")
print("=" * 80)
print(f"样本数量: {len(X)}")
print(f"特征数量: {X.shape[1]}")
print(f"类别: {target_names}")
print(f"各类别样本数: {np.bincount(y)}")
print()

# --- 2.1 箱线图矩阵：展示4个特征×3个物种的分布 ---
fig, axes = plt.subplots(2, 2, figsize=(14, 12), 
                         gridspec_kw={'hspace': 0.4, 'wspace': 0.3, 'top': 0.92, 'bottom': 0.08})
fig.suptitle('鸢尾花特征分布箱线图', fontsize=18, fontweight='bold', y=0.96)

feature_names_cn = list(FEATURE_NAMES_CN.values())
for idx, feature in enumerate(feature_names_cn):
    ax = axes[idx // 2, idx % 2]
    
    # 为每个物种绘制箱线图
    data_by_species = [df[df['物种'] == species][feature] for species in target_names]
    bp = ax.boxplot(data_by_species, labels=target_names, patch_artist=True,
                    medianprops=dict(color='black', linewidth=2),
                    boxprops=dict(linewidth=1.5),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5))
    
    # 设置颜色
    for patch, color in zip(bp['boxes'], SET1_COLORS):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # 智能文本缩放
    ax.set_title(feature.replace(' (cm)', ''), fontsize=14, fontweight='bold')
    ax.set_ylabel('数值 (cm)', fontsize=12)
    ax.tick_params(axis='both', which='major', labelsize=10)
    ax.grid(True, alpha=0.3)

plt.tight_layout(pad=3.0, rect=[0, 0, 1, 0.95])
plt.savefig('iris_boxplots.png', dpi=300, bbox_inches='tight')
plt.show()

# --- 2.2 散点图矩阵：特征关系可视化 ---
pairplot_fig = sns.pairplot(df, hue='物种', palette=SET1_COLORS, 
                             diag_kind='kde', plot_kws={'alpha': 0.6, 's': 50, 'edgecolor': 'black'},
                             height=2.5)
pairplot_fig.fig.suptitle('鸢尾花特征关系散点图矩阵', y=1.02, fontsize=18, fontweight='bold')
plt.savefig('iris_pairplot.png', dpi=300, bbox_inches='tight')
plt.show()

# --- 2.3 特征相关性热力图 ---
fig, ax = plt.subplots(figsize=(10, 8))
correlation_matrix = df.drop('物种', axis=1).corr()
sns.heatmap(correlation_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
            square=True, linewidths=1, cbar_kws={'shrink': 0.8}, ax=ax,
            vmin=-1, vmax=1)
ax.set_title('鸢尾花特征相关性热力图', fontsize=18, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig('iris_correlation.png', dpi=300, bbox_inches='tight')
plt.show()

# --- 2.4 KDE分布曲线叠加 ---
fig, axes = plt.subplots(2, 2, figsize=(14, 12),
                         gridspec_kw={'hspace': 0.4, 'wspace': 0.3, 'top': 0.92, 'bottom': 0.08})
fig.suptitle('鸢尾花特征KDE分布曲线', fontsize=18, fontweight='bold', y=0.96)

for idx, feature in enumerate(feature_names_cn):
    ax = axes[idx // 2, idx % 2]
    
    for i, (species, color) in enumerate(zip(target_names, SET1_COLORS)):
        data = df[df['物种'] == species][feature]
        data.plot.kde(ax=ax, color=color, linewidth=2.5, label=species, alpha=0.8)
    
    ax.set_title(feature.replace(' (cm)', ''), fontsize=14, fontweight='bold')
    ax.set_xlabel('数值 (cm)', fontsize=12)
    ax.set_ylabel('密度', fontsize=12)
    ax.tick_params(axis='both', which='major', labelsize=10)
    ax.legend(loc='best', frameon=True, shadow=True)
    ax.grid(True, alpha=0.3)

plt.tight_layout(pad=3.0, rect=[0, 0, 1, 0.95])
plt.savefig('iris_kde.png', dpi=300, bbox_inches='tight')
plt.show()

# ============================================================================
# 3. TASK 1: 2D CLASSIFIER COMPARISON (2x2 subplots)
# ============================================================================
print("=" * 80)
print("任务1: 2D分类器决策边界比较 (花瓣长度 vs 花瓣宽度)")
print("=" * 80)

# 使用花瓣长度和花瓣宽度（索引2和3）进行2D分类
X_2d = X[:, [2, 3]]  # petal length, petal width

# 划分训练集和测试集
X_2d_train, X_2d_test, y_train, y_test = train_test_split(
    X_2d, y, test_size=0.2, random_state=42, stratify=y
)

# 初始化4种分类器
classifiers_2d = {
    'K-近邻 (K=5)': KNeighborsClassifier(n_neighbors=5),
    '支持向量机 (RBF核)': SVC(kernel='rbf', gamma='scale'),
    '决策树 (最大深度=3)': DecisionTreeClassifier(max_depth=3, random_state=42),
    '逻辑回归': LogisticRegression(max_iter=200, random_state=42)
}

# 训练所有分类器
for name, clf in classifiers_2d.items():
    clf.fit(X_2d_train, y_train)
    accuracy = accuracy_score(y_test, clf.predict(X_2d_test))
    print(f"{name}: 测试准确率 = {accuracy:.3f}")

print()

# 创建2x2子图（优化布局）
fig, axes = plt.subplots(2, 2, figsize=(14, 12),
                         gridspec_kw={'hspace': 0.45, 'wspace': 0.3, 'top': 0.90, 'bottom': 0.08})
fig.suptitle('鸢尾花2D分类器决策边界比较 (花瓣长度 vs 花瓣宽度)', 
             fontsize=18, fontweight='bold', y=0.98)

# 创建决策边界网格（精细网格0.01步长）
x_min, x_max = X_2d[:, 0].min() - 0.5, X_2d[:, 0].max() + 0.5
y_min, y_max = X_2d[:, 1].min() - 0.5, X_2d[:, 1].max() + 0.5
xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.01),
                     np.arange(y_min, y_max, 0.01))

# 为每个分类器绘制决策边界（使用等高线替代点云）
for idx, (name, clf) in enumerate(classifiers_2d.items()):
    ax = axes[idx // 2, idx % 2]
    
    # 预测网格点
    Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)
    
    # 使用contourf填充决策区域（专业等高线）
    contour = ax.contourf(xx, yy, Z, alpha=0.3, levels=np.arange(4) - 0.5, 
                          colors=SET1_COLORS, antialiased=True)
    
    # 绘制决策边界线
    ax.contour(xx, yy, Z, levels=np.arange(4) - 0.5, colors='black', 
               linewidths=1.5, linestyles='--', alpha=0.5)
    
    # 绘制原始数据点（仅150个，size=80）
    for i, (species, color) in enumerate(zip(target_names, SET1_COLORS)):
        mask = y == i
        ax.scatter(X_2d[mask, 0], X_2d[mask, 1], c=[color], label=species,
                  s=80, edgecolors='black', linewidth=1.2, alpha=0.8)
    
    # 智能文本缩放
    ax.set_title(name, fontsize=13, fontweight='bold', pad=8)
    ax.set_xlabel('花瓣长度 (cm)', fontsize=12)
    ax.set_ylabel('花瓣宽度 (cm)', fontsize=12)
    ax.tick_params(axis='both', which='major', labelsize=10)
    ax.legend(loc='upper left', frameon=True, shadow=True, fontsize=10)
    ax.grid(True, alpha=0.3)

plt.tight_layout(pad=3.0, rect=[0, 0, 1, 0.96])
plt.savefig('task1_2d_classifiers.png', dpi=300, bbox_inches='tight')
plt.show()

# ============================================================================
# 4. TASK 2: 3D BOUNDARY (Two-class, Isosurface-based)
# ============================================================================
print("=" * 80)
print("任务2: 3D决策边界可视化 (Setosa vs 非Setosa)")
print("=" * 80)

# 使用3个特征：花瓣长度、花瓣宽度、萼片长度
X_3d = X[:, [2, 3, 0]]  # petal length, petal width, sepal length

# 创建二分类标签：Setosa (0) vs 非Setosa (1)
y_binary = (y != 0).astype(int)

# 数据标准化
scaler_3d = StandardScaler()
X_3d_scaled = scaler_3d.fit_transform(X_3d)

# 划分训练集和测试集
X_3d_train, X_3d_test, y_binary_train, y_binary_test = train_test_split(
    X_3d_scaled, y_binary, test_size=0.2, random_state=42, stratify=y_binary
)

# 训练SVM分类器（二分类）
svm_binary = SVC(kernel='rbf', gamma='scale', probability=True)
svm_binary.fit(X_3d_train, y_binary_train)
accuracy = accuracy_score(y_binary_test, svm_binary.predict(X_3d_test))
print(f"SVM二分类准确率: {accuracy:.3f}")
print()

# 创建3D决策边界可视化（使用Isosurface等值面）
def create_3d_boundary_isosurface():
    """创建3D决策边界等值面可视化（非点云）"""
    
    # 创建网格（25点/特征，优化性能）
    petal_length_range = np.linspace(X_3d_scaled[:, 0].min() - 0.5, 
                                      X_3d_scaled[:, 0].max() + 0.5, 25)
    petal_width_range = np.linspace(X_3d_scaled[:, 1].min() - 0.5, 
                                     X_3d_scaled[:, 1].max() + 0.5, 25)
    sepal_length_range = np.linspace(X_3d_scaled[:, 2].min() - 0.5, 
                                      X_3d_scaled[:, 2].max() + 0.5, 25)
    
    # 创建3D网格
    xx, yy, zz = np.meshgrid(petal_length_range, petal_width_range, sepal_length_range)
    grid_points = np.c_[xx.ravel(), yy.ravel(), zz.ravel()]
    
    # 计算决策函数值（到决策边界的距离）
    decision_values = svm_binary.decision_function(grid_points).reshape(xx.shape)
    
    # 创建图形
    fig = go.Figure()
    
    # 添加等值面（仅显示决策边界：value=0）
    fig.add_trace(go.Isosurface(
        x=xx.flatten(),
        y=yy.flatten(),
        z=zz.flatten(),
        value=decision_values.flatten(),
        isomin=0,
        isomax=0,
        surface_count=1,
        opacity=0.6,
        colorscale='RdBu',
        caps=dict(x_show=False, y_show=False, z_show=False),
        name='决策边界'
    ))
    
    # 添加实际数据点（二分类）
    binary_colors = ['#E41A1C', '#377EB8']  # Setosa: 红色, 非Setosa: 蓝色
    binary_names = ['Setosa', '非Setosa']
    
    for i, (name, color) in enumerate(zip(binary_names, binary_colors)):
        mask = y_binary == i
        fig.add_trace(go.Scatter3d(
            x=X_3d_scaled[mask, 0],
            y=X_3d_scaled[mask, 1],
            z=X_3d_scaled[mask, 2],
            mode='markers',
            marker=dict(
                size=8,
                color=color,
                opacity=0.85,
                line=dict(width=1, color='black'),
                symbol='diamond' if i == 0 else 'circle'
            ),
            name=name,
            hovertemplate=f'<b>{name}</b><br>' +
                         '花瓣长度: %{x:.2f}<br>' +
                         '花瓣宽度: %{y:.2f}<br>' +
                         '萼片长度: %{z:.2f}<extra></extra>'
        ))
    
    # 更新布局（Plotly中文字体配置）
    fig.update_layout(
        title=dict(
            text='鸢尾花3D决策边界可视化 (Setosa vs 非Setosa)',
            font=PLOTLY_TITLE_FONT,
            x=0.5
        ),
        scene=dict(
            xaxis_title='花瓣长度 (标准化)',
            yaxis_title='花瓣宽度 (标准化)',
            zaxis_title='萼片长度 (标准化)',
            bgcolor='white',
            xaxis=dict(backgroundcolor='white', gridcolor='lightgray'),
            yaxis=dict(backgroundcolor='white', gridcolor='lightgray'),
            zaxis=dict(backgroundcolor='white', gridcolor='lightgray'),
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        width=950,
        height=750,
        hovermode='closest',
        font=PLOTLY_FONT
    )
    
    return fig

# 显示3D边界图
fig_task2 = create_3d_boundary_isosurface()
fig_task2.show()

# ============================================================================
# 5. TASK 3: 3D PROBABILITY MAP (Setosa Probability - Threshold Surface)
# ============================================================================
print("=" * 80)
print("任务3: 3D概率分布图 (Setosa概率)")
print("=" * 80)

def create_3d_probability_threshold():
    """创建3D概率分布图（仅显示P=0.5等概率曲面）"""
    
    # 创建网格（25点/特征）
    petal_length_range = np.linspace(X_3d_scaled[:, 0].min() - 0.5, 
                                      X_3d_scaled[:, 0].max() + 0.5, 25)
    petal_width_range = np.linspace(X_3d_scaled[:, 1].min() - 0.5, 
                                     X_3d_scaled[:, 1].max() + 0.5, 25)
    sepal_length_range = np.linspace(X_3d_scaled[:, 2].min() - 0.5, 
                                      X_3d_scaled[:, 2].max() + 0.5, 25)
    
    # 创建3D网格
    xx, yy, zz = np.meshgrid(petal_length_range, petal_width_range, sepal_length_range)
    grid_points = np.c_[xx.ravel(), yy.ravel(), zz.ravel()]
    
    # 计算Setosa概率
    probabilities = svm_binary.predict_proba(grid_points)[:, 0]
    
    # 仅显示关键概率曲面（P=0.5附近）
    threshold_mask = np.abs(probabilities - 0.5) < 0.05
    threshold_points = grid_points[threshold_mask]
    threshold_probs = probabilities[threshold_mask]
    
    # 创建图形
    fig = go.Figure()
    
    # 添加P=0.5等概率曲面
    fig.add_trace(go.Scatter3d(
        x=threshold_points[:, 0],
        y=threshold_points[:, 1],
        z=threshold_points[:, 2],
        mode='markers',
        marker=dict(
            size=3,
            color=threshold_probs,
            colorscale='Viridis',
            opacity=0.6,
            colorbar=dict(
                title=dict(text='Setosa概率', font=dict(size=14)),
                len=0.8,
                y=0.5
            ),
            showscale=True,
            cmin=0,
            cmax=1
        ),
        name='P=0.5决策边界',
        hovertemplate='概率: %{marker.color:.3f}<br>' +
                     '花瓣长度: %{x:.2f}<br>' +
                     '花瓣宽度: %{y:.2f}<br>' +
                     '萼片长度: %{z:.2f}<extra></extra>'
    ))
    
    # 添加实际数据点（采样75个：50个Setosa + 25个非Setosa）
    binary_colors = ['#E41A1C', '#377EB8']
    binary_names = ['Setosa', '非Setosa']
    
    # Setosa: 50个样本
    setosa_indices = np.where(y_binary == 0)[0][:50]
    non_setosa_indices = np.where(y_binary == 1)[0][:25]
    
    for i, (name, color, indices) in enumerate(zip(binary_names, binary_colors, 
                                                     [setosa_indices, non_setosa_indices])):
        fig.add_trace(go.Scatter3d(
            x=X_3d_scaled[indices, 0],
            y=X_3d_scaled[indices, 1],
            z=X_3d_scaled[indices, 2],
            mode='markers',
            marker=dict(
                size=10,
                color=color,
                opacity=0.85,
                line=dict(width=2, color='black'),
                symbol='diamond' if i == 0 else 'circle'
            ),
            name=name,
            hovertemplate=f'<b>{name}</b><br>' +
                         '花瓣长度: %{x:.2f}<br>' +
                         '花瓣宽度: %{y:.2f}<br>' +
                         '萼片长度: %{z:.2f}<extra></extra>'
        ))
    
    # 更新布局
    fig.update_layout(
        title=dict(
            text='SVM概率分布图 (Setosa)',
            font=PLOTLY_TITLE_FONT,
            x=0.5
        ),
        scene=dict(
            xaxis_title='花瓣长度 (标准化)',
            yaxis_title='花瓣宽度 (标准化)',
            zaxis_title='萼片长度 (标准化)',
            bgcolor='white',
            xaxis=dict(backgroundcolor='white', gridcolor='lightgray'),
            yaxis=dict(backgroundcolor='white', gridcolor='lightgray'),
            zaxis=dict(backgroundcolor='white', gridcolor='lightgray'),
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2))
        ),
        width=950,
        height=750,
        hovermode='closest',
        font=PLOTLY_FONT
    )
    
    return fig

# 显示3D概率图
fig_task3 = create_3d_probability_threshold()
fig_task3.show()

# ============================================================================
# 6. TASK 4: INTERACTIVE DASHBOARD
# ============================================================================
print("=" * 80)
print("任务4: 交互式仪表板 (集成可视化)")
print("=" * 80)

def create_interactive_dashboard():
    """创建交互式仪表板：2D边界+分布直方图+3D概率"""
    
    # 创建子图（2行2列）
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{'type': 'xy', 'rowspan': 2}, {'type': 'xy'}],
               [None, {'type': 'scatter3d'}]],
        subplot_titles=('2D决策边界 (支持向量机 - 花瓣特征)', 
                        '花瓣长度分布直方图',
                        '3D概率分布 (Setosa)'),
        vertical_spacing=0.12,
        horizontal_spacing=0.1,
        column_widths=[0.5, 0.5],
        row_heights=[0.5, 0.5]
    )
    
    # ========== 左侧：2D决策边界（使用等高线）==========
    svm_2d = SVC(kernel='rbf', gamma='scale')
    svm_2d.fit(X_2d_train, y_train)
    
    # 创建网格
    x_min, x_max = X_2d[:, 0].min() - 0.5, X_2d[:, 0].max() + 0.5
    y_min, y_max = X_2d[:, 1].min() - 0.5, X_2d[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.02),
                         np.arange(y_min, y_max, 0.02))
    
    # 预测
    Z = svm_2d.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)
    
    # 添加决策边界等高线
    fig.add_trace(go.Contour(
        x=xx[0],
        y=yy[:, 0],
        z=Z,
        colorscale=[[0, SET1_COLORS[0]], [0.5, SET1_COLORS[1]], [1, SET1_COLORS[2]]],
        opacity=0.3,
        showscale=False,
        hoverinfo='skip'
    ), row=1, col=1)
    
    # 添加数据点
    for i, (species, color) in enumerate(zip(target_names, SET1_COLORS)):
        mask = y == i
        fig.add_trace(go.Scatter(
            x=X_2d[mask, 0],
            y=X_2d[mask, 1],
            mode='markers',
            marker=dict(
                size=10,
                color=color,
                opacity=0.8,
                line=dict(width=1, color='black')
            ),
            name=species,
            hovertemplate=f'<b>{species}</b><br>' +
                         '花瓣长度: %{x:.2f}<br>' +
                         '花瓣宽度: %{y:.2f}<extra></extra>'
        ), row=1, col=1)
    
    # ========== 右上：花瓣长度分布直方图 ==========
    for i, (species, color) in enumerate(zip(target_names, SET1_COLORS)):
        mask = y == i
        fig.add_trace(go.Histogram(
            x=X_2d[mask, 0],
            name=species,
            marker=dict(color=color, opacity=0.7, line=dict(width=1, color='black')),
            showlegend=False,
            hovertemplate=f'<b>{species}</b><br>' +
                         '花瓣长度: %{x:.2f}<br>' +
                         '计数: %{y}<extra></extra>'
        ), row=1, col=2)
    
    # ========== 右下：3D概率分布（采样）==========
    # 创建网格
    petal_length_range = np.linspace(X_3d_scaled[:, 0].min() - 0.5, 
                                      X_3d_scaled[:, 0].max() + 0.5, 20)
    petal_width_range = np.linspace(X_3d_scaled[:, 1].min() - 0.5, 
                                     X_3d_scaled[:, 1].max() + 0.5, 20)
    sepal_length_range = np.linspace(X_3d_scaled[:, 2].min() - 0.5, 
                                      X_3d_scaled[:, 2].max() + 0.5, 20)
    
    xx_3d, yy_3d, zz_3d = np.meshgrid(petal_length_range, petal_width_range, sepal_length_range)
    grid_points_3d = np.c_[xx_3d.ravel(), yy_3d.ravel(), zz_3d.ravel()]
    
    # 计算概率（采样1500点）
    sample_indices = np.random.choice(len(grid_points_3d), size=1500, replace=False)
    sampled_points_3d = grid_points_3d[sample_indices]
    probabilities_3d = svm_binary.predict_proba(sampled_points_3d)[:, 0]
    
    # 添加3D概率分布
    fig.add_trace(go.Scatter3d(
        x=sampled_points_3d[:, 0],
        y=sampled_points_3d[:, 1],
        z=sampled_points_3d[:, 2],
        mode='markers',
        marker=dict(
            size=4,
            color=probabilities_3d,
            colorscale='Viridis',
            opacity=0.7,
            colorbar=dict(
                title=dict(text='Setosa概率', font=dict(size=12)),
                len=0.5,
                y=0.25,
                x=1.02
            ),
            showscale=True,
            cmin=0,
            cmax=1
        ),
        showlegend=False,
        hovertemplate='概率: %{marker.color:.3f}<extra></extra>'
    ), row=2, col=2)
    
    # 添加数据点到3D图
    binary_colors = ['#E41A1C', '#377EB8']
    binary_names = ['Setosa', '非Setosa']
    
    for i, (name, color) in enumerate(zip(binary_names, binary_colors)):
        mask = y_binary == i
        fig.add_trace(go.Scatter3d(
            x=X_3d_scaled[mask, 0],
            y=X_3d_scaled[mask, 1],
            z=X_3d_scaled[mask, 2],
            mode='markers',
            marker=dict(
                size=6,
                color=color,
                opacity=0.8,
                line=dict(width=1, color='black')
            ),
            showlegend=False,
            hovertemplate=f'<b>{name}</b><extra></extra>'
        ), row=2, col=2)
    
    # 更新布局
    fig.update_xaxes(title_text='花瓣长度 (cm)', row=1, col=1)
    fig.update_yaxes(title_text='花瓣宽度 (cm)', row=1, col=1)
    fig.update_xaxes(title_text='花瓣长度 (cm)', row=1, col=2)
    fig.update_yaxes(title_text='计数', row=1, col=2)
    
    fig.update_scenes(
        xaxis_title='花瓣长度',
        yaxis_title='花瓣宽度',
        zaxis_title='萼片长度',
        bgcolor='white',
        xaxis=dict(backgroundcolor='white', gridcolor='lightgray'),
        yaxis=dict(backgroundcolor='white', gridcolor='lightgray'),
        zaxis=dict(backgroundcolor='white', gridcolor='lightgray'),
        camera=dict(eye=dict(x=1.3, y=1.3, z=1.1)),
        row=2, col=2
    )
    
    fig.update_layout(
        title=dict(
            text='鸢尾花分类交互式仪表板',
            font=PLOTLY_TITLE_FONT,
            x=0.5,
            y=0.98  # 主标题向上移动，避免与子图标题重叠
        ),
        width=1800,
        height=900,  # 增加高度，留出更多空间
        margin=dict(t=100, b=50, l=50, r=50),  # 增加顶部边距
        hovermode='closest',
        barmode='overlay',
        font=PLOTLY_FONT
    )
    
    # 调整子图标题字体大小，避免重叠
    for annotation in fig['layout']['annotations']:
        annotation['font'] = dict(size=13, family=CHINESE_FONT_FAMILY)
    
    return fig

# 显示交互式仪表板
fig_task4 = create_interactive_dashboard()
fig_task4.show()

print("=" * 80)
print("所有可视化完成！")
print("=" * 80)