import os
import time
import hashlib
from collections import OrderedDict
from typing import List, Dict, Any, Optional

import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from search_gallery import load_gallery, cosine_topk
from dinov2_numpy import Dinov2Numpy
from preprocess_image import resize_short_side
from weight_stabilize import stabilize_weights

app = FastAPI(title="以图搜图")

BASE_DIR = os.path.dirname(__file__)
GALLERY_DIR = os.path.join(BASE_DIR, "gallery")
IMAGES_DIR = os.path.join(BASE_DIR, "gallery_images")

# 静态文件：用于浏览器直接访问图片
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# 全局变量，用于存储加载的图库特征和元数据
GALLERY_FEATS: np.ndarray
GALLERY_METAS: List[Dict[str, Any]]


def _load_gallery_data():
    """从文件加载图库数据到全局变量。"""
    global GALLERY_FEATS, GALLERY_METAS
    try:
        GALLERY_FEATS, GALLERY_METAS = load_gallery(GALLERY_DIR)
        return len(GALLERY_METAS)
    except FileNotFoundError:
        GALLERY_FEATS = np.array([])
        GALLERY_METAS = []
        return 0


@app.on_event("startup")
def startup_event():
    """服务器启动时执行，加载初始图库。"""
    count = _load_gallery_data()
    print(f"初始图库加载完成，共 {count} 张图片")


# 启动时加载模型（含权重稳定化）
# 改进：使用与 build_gallery.py 相同的 max_norm=2.0，确保特征一致性
STABILIZE_MAX_NORM = 2.0  # 与 build_gallery.py 保持一致
WEIGHTS = np.load(os.path.join(BASE_DIR, "vit-dinov2-base.npz"))
WEIGHTS = stabilize_weights(WEIGHTS, layer_idx=8, max_norm=STABILIZE_MAX_NORM)
VIT = Dinov2Numpy(WEIGHTS)


# 查询特征缓存：只缓存“上传图片 -> 特征向量”，避免重复跑模型
_FEATURE_CACHE_MAX_ITEMS = 256
_FEATURE_CACHE_TTL_SEC = 3600
_FEATURE_CACHE: "OrderedDict[str, tuple[float, np.ndarray]]" = OrderedDict()


def _feature_cache_get(key: str) -> Optional[np.ndarray]:
    item = _FEATURE_CACHE.get(key)
    if item is None:
        return None
    ts, feat = item
    if time.time() - ts > _FEATURE_CACHE_TTL_SEC:
        _FEATURE_CACHE.pop(key, None)
        return None
    # LRU: 触碰则移动到末尾
    _FEATURE_CACHE.move_to_end(key)
    return feat


def _feature_cache_set(key: str, feat: np.ndarray) -> None:
    _FEATURE_CACHE[key] = (time.time(), feat)
    _FEATURE_CACHE.move_to_end(key)
    while len(_FEATURE_CACHE) > _FEATURE_CACHE_MAX_ITEMS:
        _FEATURE_CACHE.popitem(last=False)


def extract_feature_from_upload(file_bytes: bytes, use_multi_scale: bool = False) -> np.ndarray:
    """提取查询图片特征，支持多尺度特征融合（提升准确率）。
    
    参数:
        file_bytes: 图片文件字节
        use_multi_scale: 是否使用多尺度特征（默认 True，更准确但稍慢）
    
    返回:
        (D,) 特征向量
    """
    tmp_dir = os.path.join(BASE_DIR, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, "query.jpg")
    with open(tmp_path, "wb") as f:
        f.write(file_bytes)

    if use_multi_scale:
        # 多尺度特征提取（最准确）
        try:
            from multi_scale_features import extract_multi_scale_features
            feat = extract_multi_scale_features(
                VIT, tmp_path,
                scales=[224, 336, 448],  # 三个尺度
                feature_mode="fused"
            )
            return feat
        except ImportError:
            # 如果模块不存在，回退到单尺度
            pass
    
    # 单尺度特征提取（快速）
    pixel_values = resize_short_side(tmp_path, target_size=224)
    feat = VIT(pixel_values, feature_mode="fused")[0].astype(np.float32)
    return feat


@app.get("/", response_class=HTMLResponse)
def index():
    return """<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>以图搜图</title>
  <style>
    * { box-sizing: border-box; }
    body { 
      font-family: -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif; 
      margin: 0; 
      padding: 24px; 
      background: #f5f5f5;
      min-height: 100vh;
    }
    .wrap { max-width: 1200px; margin: 0 auto; }
    .header { 
      display: flex; 
      justify-content: space-between; 
      align-items: center; 
      margin-bottom: 24px; 
      background: rgba(255,255,255,0.95);
      padding: 20px 24px;
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.1);
      backdrop-filter: blur(10px);
    }
    .header h1 { margin: 0; font-size: 28px; color: #111827; font-weight: 600; }
    .card { 
      border: none; 
      border-radius: 16px; 
      padding: 24px; 
      background: rgba(255,255,255,0.95);
      box-shadow: 0 8px 32px rgba(0,0,0,0.1);
      backdrop-filter: blur(10px);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .card:hover { transform: translateY(-2px); box-shadow: 0 12px 40px rgba(0,0,0,0.15); }
    .layout { display: grid; grid-template-columns: minmax(0, 3fr) minmax(280px, 1fr); gap: 20px; margin-top: 20px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; margin-top: 20px; }
    img { max-width: 100%; border-radius: 12px; display: block; transition: transform 0.3s ease; }
    img:hover { transform: scale(1.02); }
    .muted { color: #6b7280; font-size: 13px; }
    .row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    button { 
      padding: 10px 20px; 
      border-radius: 10px; 
      border: none; 
      background: #3b82f6;
      color: #fff; 
      cursor: pointer; 
      font-size: 14px;
      font-weight: 500;
      transition: all 0.3s ease;
      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    button:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5); }
    button:active:not(:disabled) { transform: translateY(0); }
    button:disabled { opacity: 0.5; cursor: default; transform: none; }
    input[type=number] { width: 80px; padding: 8px 12px; border: 2px solid #e5e7eb; border-radius: 8px; font-size: 14px; transition: border-color 0.2s; }
    input[type=number]:focus { outline: none; border-color: #667eea; }
    input[type=file] { font-size: 14px; padding: 8px; border: 2px dashed #d1d5db; border-radius: 8px; background: #f9fafb; transition: all 0.2s; }
    input[type=file]:hover { border-color: #667eea; background: #f3f4f6; }
    a { color: #667eea; text-decoration: none; transition: color 0.2s; }
    a:hover { color: #764ba2; text-decoration: underline; }

    .pagination { display: flex; align-items: center; justify-content: flex-end; gap: 12px; margin-top: 20px; font-size: 14px; }
    .score-bar-outer { width: 100%; height: 8px; border-radius: 999px; background: #e5e7eb; overflow: hidden; margin-top: 8px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1); }
    .score-bar-inner { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #10b981, #059669, #047857); transition: width 0.5s ease; box-shadow: 0 2px 8px rgba(16, 185, 129, 0.4); }

    .preview-pane { position: fixed; right: 24px; bottom: 24px; width: 280px; max-height: 300px; border-radius: 16px; background: linear-gradient(135deg, rgba(17,24,39,0.95), rgba(31,41,55,0.95)); color: #fff; padding: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.5); display: none; z-index: 50; backdrop-filter: blur(10px); animation: slideUp 0.3s ease; }
    @keyframes slideUp { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
    .preview-pane img { max-width: 100%; max-height: 220px; border-radius: 12px; margin-bottom: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    .preview-caption { font-size: 13px; color: #e5e7eb; max-height: 3.4em; overflow: hidden; line-height: 1.5; }

    .recent-list { list-style: none; padding: 0; margin: 12px 0 0; max-height: 300px; overflow-y: auto; }
    .recent-item { padding: 10px 12px; border-radius: 12px; cursor: pointer; display: flex; align-items: center; gap: 12px; transition: all 0.2s ease; margin-bottom: 4px; }
    .recent-item:hover { background: #f3f4f6; transform: translateX(4px); }
    .recent-thumb { width: 48px; height: 48px; border-radius: 10px; object-fit: cover; background: #e5e7eb; flex-shrink: 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .recent-meta { display: flex; flex-direction: column; flex: 1; min-width: 0; }
    .recent-title { font-size: 14px; color: #111827; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .recent-sub { font-size: 12px; color: #6b7280; margin-top: 2px; }

    .query-preview { margin-top: 16px; padding: 16px; background: #f0f9ff; border-radius: 12px; display: none; border: 2px solid #bae6fd; animation: fadeIn 0.3s ease; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
    .query-preview img { max-width: 220px; max-height: 220px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .query-preview-label { font-size: 13px; color: #0369a1; font-weight: 500; margin-bottom: 10px; }

    .result-img-link { display: block; cursor: pointer; transition: all 0.3s ease; }
    .result-img-link:hover { opacity: 0.9; transform: scale(1.02); }
    .search-this-btn { margin-top: 10px; padding: 8px 16px; font-size: 13px; background: #3b82f6; border: none; border-radius: 8px; color: white; font-weight: 500; transition: all 0.2s ease; width: 100%; }
    .search-this-btn:hover { background: #2563eb; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4); }
    
    /* 加载动画 */
    .loading { display: inline-block; width: 20px; height: 20px; border: 3px solid rgba(255,255,255,0.3); border-radius: 50%; border-top-color: #fff; animation: spin 0.8s linear infinite; margin-right: 8px; }
    @keyframes spin { to { transform: rotate(360deg); } }
    
    /* 图片占位符 */
    .img-placeholder { width: 100%; aspect-ratio: 1; background: #f3f4f6; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size: 14px; }
    
    /* 响应式设计 */
    @media (max-width: 768px) {
      body { padding: 12px; }
      .layout { grid-template-columns: 1fr; }
      .grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }
      .header { flex-direction: column; gap: 12px; align-items: flex-start; }
      .header h1 { font-size: 24px; }
    }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"header\">
      <h1>以图搜图（本地 Demo）</h1>
      <button id=\"reload-btn\">刷新图库</button>
    </div>
    <div class=\"muted\">提示：可批量选择多张图片进行检索；也可以访问 <a href=\"/docs\">/docs</a> 使用 Swagger 上传图片测试。</div>

    <div class=\"layout\">
      <div>
        <div class=\"card\">
          <form id=\"f\">
            <div class=\"row\">
              <input id=\"file-input\" type=\"file\" name=\"file\" accept=\"image/*\" multiple required />
              <label>TopK: <input type=\"number\" name=\"topk\" value=\"20\" min=\"1\" max=\"100\" /></label>
              <button type=\"submit\">🔍 开始搜索</button>
            </div>
            <div class=\"row\" style=\"margin-top:12px;\">
              <label><input type=\"checkbox\" id=\"use-rerank\" checked /> 启用重排序（更准确）</label>
              <label><input type=\"checkbox\" id=\"sort-by-score\" /> 按相似度排序</label>
            </div>
          </form>
          <div id=\"query-preview\" class=\"query-preview\">
            <div class=\"query-preview-label\">查询图片：</div>
            <img id=\"query-img\" src=\"\" alt=\"查询图片\" />
          </div>
          <div id=\"status\" class=\"muted\" style=\"margin-top:16px; padding: 12px; background: #f0f9ff; border-radius: 8px; border-left: 4px solid #3b82f6;\"></div>
          <div id=\"filter-bar\" style=\"margin-top:16px; padding:12px; background:#fff3cd; border-radius:8px; border-left:4px solid #ffc107; display:none;\">
            <div class=\"row\">
              <label style=\"flex:1;\">相似度阈值: <input type=\"range\" id=\"score-threshold\" min=\"0\" max=\"1\" step=\"0.01\" value=\"0\" style=\"width:200px;\" /></label>
              <span id=\"threshold-value\" style=\"min-width:50px; font-weight:600; color:#856404;\">0.00</span>
              <button id=\"clear-filter\" style=\"padding:6px 12px; font-size:12px; background:#ffc107; border:none; border-radius:6px; cursor:pointer;\">清除筛选</button>
            </div>
          </div>
          <div id=\"results\" class=\"grid\"></div>
          <div id=\"pagination\" class=\"pagination\" style=\"display:none\">
            <span id=\"page-info\"></span>
            <button id=\"prev-page\">上一页</button>
            <button id=\"next-page\">下一页</button>
          </div>
        </div>
      </div>

      <div>
        <div class=\"card\">
          <div class=\"muted\">最近搜索（点击可快速切换结果）</div>
          <ul id=\"recent-list\" class=\"recent-list\"></ul>
        </div>
      </div>
    </div>
  </div>

  <div id=\"preview\" class=\"preview-pane\">
    <img id=\"preview-img\" src=\"\" alt=\"preview\" />
    <div id=\"preview-score\" class=\"muted\" style=\"color:#a3e635\"></div>
    <div id=\"preview-caption\" class=\"preview-caption\"></div>
  </div>

<script>
const form = document.getElementById('f');
const fileInput = document.getElementById('file-input');
const statusEl = document.getElementById('status');
const resultsEl = document.getElementById('results');
const reloadBtn = document.getElementById('reload-btn');
const paginationEl = document.getElementById('pagination');
const pageInfoEl = document.getElementById('page-info');
const prevBtn = document.getElementById('prev-page');
const nextBtn = document.getElementById('next-page');
const recentListEl = document.getElementById('recent-list');
const previewEl = document.getElementById('preview');
const previewImg = document.getElementById('preview-img');
const previewScore = document.getElementById('preview-score');
const previewCaption = document.getElementById('preview-caption');
const queryPreviewEl = document.getElementById('query-preview');
const queryImgEl = document.getElementById('query-img');

let allResults = [];        // 当前展示的结果列表
let filteredResults = [];  // 筛选后的结果
let currentPage = 1;
const pageSize = 10;
let recentSearches = [];    // {id, title, time, thumb, results}
let recentId = 0;
let useRerank = true;      // 是否使用重排序
let sortByScore = false;    // 是否按相似度排序

function normalizeScore(score) {
  // 余弦相似度一般在 [-1,1]，这里简单做 0–1 归一并限制最小宽度
  const norm = (score + 1) / 2;
  return Math.max(0.05, Math.min(1, norm || 0));
}

function renderPage() {
  resultsEl.innerHTML = '';
  
  // 应用筛选和排序
  let displayResults = filteredResults.length > 0 ? filteredResults : allResults;
  
  if (sortByScore) {
    displayResults = [...displayResults].sort((a, b) => b.score - a.score);
  }
  
  if (!displayResults.length) {
    paginationEl.style.display = 'none';
    resultsEl.innerHTML = '<div class="card" style="text-align:center; padding:40px; color:#6b7280;">暂无结果</div>';
    return;
  }
  
  const totalPages = Math.max(1, Math.ceil(displayResults.length / pageSize));
  if (currentPage > totalPages) currentPage = totalPages;

  const start = (currentPage - 1) * pageSize;
  const end = Math.min(start + pageSize, displayResults.length);
  const slice = displayResults.slice(start, end);

  for (const item of slice) {
    const div = document.createElement('div');
    div.className = 'card';
    const imgUrl = item.image ? `http://127.0.0.1:8000${item.image}` : null;
    const originalUrl = item.url || '';
    const widthPercent = normalizeScore(item.score) * 100;
    
    // 图片可点击跳转到原始 URL
    let imgHtml = '';
    if (imgUrl) {
      if (originalUrl) {
        imgHtml = `<a href=\"${originalUrl}\" target=\"_blank\" class=\"result-img-link\"><img src=\"${imgUrl}\" class=\"result-img\" data-image=\"${imgUrl}\" data-score=\"${item.score}\" data-caption=\"${item.caption ?? ''}\" data-url=\"${item.image}\" /></a>`;
      } else {
        imgHtml = `<img src=\"${imgUrl}\" class=\"result-img\" data-image=\"${imgUrl}\" data-score=\"${item.score}\" data-caption=\"${item.caption ?? ''}\" data-url=\"${item.image}\" />`;
      }
    }
    
    div.innerHTML = `
      ${imgUrl ? `<div class="img-container" style="position:relative; overflow:hidden; border-radius:12px; background:#f3f4f6;">${imgHtml}</div>` : '<div class="img-placeholder">暂无图片</div>'}
      <div class=\"muted\" style=\"margin-top:8px; font-weight:500;\">相似度: <span style=\"color:#059669; font-weight:600;\">${item.score.toFixed(4)}</span></div>
      <div class=\"score-bar-outer\"><div class=\"score-bar-inner\" style=\"width:${widthPercent}%;\"></div></div>
      <div class=\"muted\" style=\"margin-top:8px; line-height:1.5;\">${item.caption || '无描述'}</div>
      ${imgUrl ? `<button class=\"search-this-btn\" data-image-url=\"${item.image}\">🔍 搜这张图</button>` : ''}
    `;
    resultsEl.appendChild(div);
    
    // 图片懒加载
    if (imgUrl) {
      const img = div.querySelector('img');
      if (img) {
        img.loading = 'lazy';
        img.onerror = function() {
          this.style.display = 'none';
          const placeholder = document.createElement('div');
          placeholder.className = 'img-placeholder';
          placeholder.textContent = '图片加载失败';
          this.parentElement.appendChild(placeholder);
        };
      }
    }
    
    // 绑定"搜这张图"按钮事件
    const searchBtn = div.querySelector('.search-this-btn');
    if (searchBtn) {
      searchBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const imageUrl = searchBtn.dataset.imageUrl;
        if (!imageUrl) return;
        
        const fullUrl = `http://127.0.0.1:8000${imageUrl}`;
        statusEl.textContent = '正在加载图片并搜索...';
        
        try {
          // 从服务器获取图片并转换为 File 对象
          const imgResp = await fetch(fullUrl);
          if (!imgResp.ok) throw new Error(`加载图片失败: ${imgResp.status}`);
          const blob = await imgResp.blob();
          const fileName = imageUrl.split('/').pop() || 'image.jpg';
          const file = new File([blob], fileName, { type: blob.type });
          
          // 使用该图片进行搜索
          const topk = parseInt(document.querySelector('input[name=\"topk\"]').value) || 20;
          const data = await searchForFile(file, topk, true, true);  // rerank=true, multiScale=true
          const thumb = data[0]?.image ? `http://127.0.0.1:8000${data[0].image}` : null;
          pushRecentSearch(`搜图: ${fileName}`, thumb, data);
          allResults = data.slice();
          currentPage = 1;
          renderPage();
          statusEl.textContent = `搜索完成，找到 ${data.length} 条结果`;
        } catch (err) {
          console.error(err);
          statusEl.textContent = `搜索失败: ${err.message}`;
        }
      });
    }
  }

  // 绑定悬停预览事件
  const imgs = resultsEl.querySelectorAll('.result-img');
  imgs.forEach(img => {
    img.addEventListener('mouseenter', () => {
      const src = img.dataset.image;
      const score = Number(img.dataset.score || 0);
      const caption = img.dataset.caption || '';
      previewImg.src = src;
      previewScore.textContent = `score: ${score.toFixed(4)}`;
      previewCaption.textContent = caption;
      previewEl.style.display = 'block';
    });
    img.addEventListener('mouseleave', () => {
      previewEl.style.display = 'none';
    });
  });

  const totalCount = filteredResults.length > 0 ? filteredResults.length : allResults.length;
  pageInfoEl.textContent = `第 ${currentPage} / ${totalPages} 页（共 ${totalCount} 条${filteredResults.length > 0 ? '，已筛选' : ''}）`;
  paginationEl.style.display = totalPages > 1 ? 'flex' : 'none';
  prevBtn.disabled = currentPage <= 1;
  nextBtn.disabled = currentPage >= totalPages;
}

prevBtn.addEventListener('click', () => {
  if (currentPage > 1) {
    currentPage -= 1;
    renderPage();
  }
});

nextBtn.addEventListener('click', () => {
  const totalPages = Math.max(1, Math.ceil(allResults.length / pageSize));
  if (currentPage < totalPages) {
    currentPage += 1;
    renderPage();
  }
});

function pushRecentSearch(title, thumb, results) {
  const now = new Date();
  const item = {
    id: ++recentId,
    title,
    time: now.toLocaleTimeString('zh-CN', { hour12: false }),
    thumb,
    results,
  };
  recentSearches.unshift(item);
  if (recentSearches.length > 5) recentSearches.pop();

  recentListEl.innerHTML = '';
  for (const s of recentSearches) {
    const li = document.createElement('li');
    li.className = 'recent-item';
    li.dataset.id = String(s.id);
    li.innerHTML = `
      ${s.thumb ? `<img src=\"${s.thumb}\" class=\"recent-thumb\" />` : `<div class=\"recent-thumb\"></div>`}
      <div class=\"recent-meta\">
        <div class=\"recent-title\" title=\"${s.title}\">${s.title}</div>
        <div class=\"recent-sub\">${s.time} · ${s.results.length} 条结果</div>
      </div>
    `;
    li.addEventListener('click', () => {
      allResults = s.results.slice();
      currentPage = 1;
      statusEl.textContent = `已切换至历史搜索：「${s.title}」`;
      renderPage();
    });
    recentListEl.appendChild(li);
  }
}

async function searchForFile(file, topk, rerank = true, multiScale = true) {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('topk', topk);

  const resp = await fetch(`/search?topk=${encodeURIComponent(topk)}&rerank=${rerank}&multi_scale=${multiScale}`, {
    method: 'POST',
    body: fd,
  });

  if (!resp.ok) {
    throw new Error(`请求失败: ${resp.status}`);
  }
  return await resp.json();
}

// 获取复选框和筛选控件
const rerankCheckbox = document.getElementById('use-rerank');
const sortCheckbox = document.getElementById('sort-by-score');
const thresholdSlider = document.getElementById('score-threshold');
const thresholdValue = document.getElementById('threshold-value');
const filterBar = document.getElementById('filter-bar');
const clearFilterBtn = document.getElementById('clear-filter');

// 重排序复选框事件
if (rerankCheckbox) {
  rerankCheckbox.addEventListener('change', (e) => {
    useRerank = e.target.checked;
  });
}

// 排序复选框事件
if (sortCheckbox) {
  sortCheckbox.addEventListener('change', (e) => {
    sortByScore = e.target.checked;
    renderPage();
  });
}

// 相似度阈值滑块事件
if (thresholdSlider && thresholdValue) {
  thresholdSlider.addEventListener('input', (e) => {
    const threshold = parseFloat(e.target.value);
    thresholdValue.textContent = threshold.toFixed(2);
    applyFilter(threshold);
  });
}

// 清除筛选按钮事件
if (clearFilterBtn) {
  clearFilterBtn.addEventListener('click', () => {
    thresholdSlider.value = 0;
    thresholdValue.textContent = '0.00';
    filteredResults = [];
    filterBar.style.display = 'none';
    currentPage = 1;
    renderPage();
  });
}

// 应用筛选函数
function applyFilter(threshold) {
  if (threshold <= 0) {
    filteredResults = [];
    filterBar.style.display = 'none';
  } else {
    filteredResults = allResults.filter(r => r.score >= threshold);
    filterBar.style.display = 'block';
  }
  currentPage = 1;
  renderPage();
}

// 文件选择时显示查询图片预览
fileInput.addEventListener('change', (e) => {
  const files = e.target.files;
  if (files && files.length > 0) {
    const firstFile = files[0];
    const reader = new FileReader();
    reader.onload = (event) => {
      queryImgEl.src = event.target.result;
      queryPreviewEl.style.display = 'block';
    };
    reader.readAsDataURL(firstFile);
  } else {
    queryPreviewEl.style.display = 'none';
  }
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const files = fileInput.files;
  if (!files || !files.length) {
    statusEl.textContent = '请先选择图片';
    return;
  }

  const fd = new FormData(form);
  const topk = fd.get('topk') || '20';
  useRerank = rerankCheckbox ? rerankCheckbox.checked : true;

  resultsEl.innerHTML = '';
  allResults = [];
  filteredResults = [];
  currentPage = 1;
  filterBar.style.display = 'none';
  statusEl.innerHTML = `<span class="loading"></span>正在检索 ${files.length} 张图片...`;

  // 逐张图片串行请求，避免一次性塞太多请求
  for (let i = 0; i < files.length; i++) {
    const f = files[i];
    statusEl.innerHTML = `<span class="loading"></span>正在检索 (${i + 1}/${files.length})：${f.name}`;
    try {
            const data = await searchForFile(f, topk, useRerank, false);  // 默认关闭多尺度以提升速度
      const thumb = data[0]?.image ? `http://127.0.0.1:8000${data[0].image}` : null;
      pushRecentSearch(f.name, thumb, data);
      // 默认展示最新一次搜索的结果
      allResults = data.slice();
      filteredResults = [];
      currentPage = 1;
      filterBar.style.display = 'none';
      renderPage();
    } catch (err) {
      console.error(err);
      statusEl.textContent = `请求失败: ${err}`;
      break;
    }
  }

  statusEl.innerHTML = `✅ 完成 ${files.length} 个搜索（点击右侧"最近搜索"可切换查看历史结果）`;
});

reloadBtn.addEventListener('click', async () => {
  statusEl.innerHTML = '<span class="loading"></span>正在刷新图库...';
  reloadBtn.disabled = true;
  const resp = await fetch('/reload_gallery', { method: 'POST' });
  if (!resp.ok) {
    statusEl.innerHTML = `❌ 刷新失败: ${resp.status}`;
    reloadBtn.disabled = false;
    return;
  }
  const data = await resp.json();
  statusEl.innerHTML = `✅ 图库刷新成功，当前共 ${data.count} 张图片。`;
  reloadBtn.disabled = false;
});
</script>
</body>
</html>"""


@app.post("/search")
async def search_api(file: UploadFile = File(...), topk: int = 10, rerank: bool = True, multi_scale: bool = False) -> List[Dict[str, Any]]:
    content = await file.read()

    # --- 特征缓存逻辑 ---
    content_hash = hashlib.sha1(content).hexdigest()
    q = _feature_cache_get(content_hash)

    if q is None:
        # 缓存未命中：提取特征并存入缓存
        q = extract_feature_from_upload(content, use_multi_scale=multi_scale)
        _feature_cache_set(content_hash, q)
        print(f"[Cache] MISS for hash: {content_hash}")
    else:
        # 缓存命中
        print(f"[Cache] HIT for hash: {content_hash}")
    # --- 特征缓存逻辑结束 ---

    # 如果启用重排序，使用两阶段检索
    if rerank and topk <= 100:
        # 速度优先：用 FAISS 先做粗召回，再在候选集合上做重排序
        topk_coarse = min(200, len(GALLERY_METAS))
        idx_coarse, sims_coarse = cosine_topk(q, GALLERY_FEATS, k=topk_coarse)

        try:
            from search_enhancements import rerank_topk_enhanced

            # 在 coarse 候选上 rerank，避免全库扫描
            feats_coarse = GALLERY_FEATS[idx_coarse]
            idx_in_coarse, sims = rerank_topk_enhanced(
                q,
                feats_coarse,
                topk_coarse=min(topk_coarse, feats_coarse.shape[0]),
                topk_final=min(topk, feats_coarse.shape[0]),
                use_hybrid=True,
            )
            idx = idx_coarse[idx_in_coarse]
        except ImportError:
            idx, sims = idx_coarse[: min(topk, len(idx_coarse))], sims_coarse[: min(topk, len(idx_coarse))]
    else:
        idx, sims = cosine_topk(q, GALLERY_FEATS, k=min(topk, len(GALLERY_METAS)))

    results: List[Dict[str, Any]] = []
    for i, s in zip(idx.tolist(), sims.tolist()):
        m = GALLERY_METAS[i]
        img_path = m.get("path") or m.get("local_path")
        img_url = None
        if img_path:
            img_url = "/images/" + os.path.basename(img_path)

        results.append(
            {
                "score": float(s),
                "url": m.get("url"),
                "caption": m.get("caption", ""),
                "image": img_url,
            }
        )

    return results


@app.post("/reload_gallery")
def reload_gallery_api():
    """重新从文件加载图库特征和元数据。"""
    count = _load_gallery_data()
    return JSONResponse({"message": "图库刷新成功", "count": count})
