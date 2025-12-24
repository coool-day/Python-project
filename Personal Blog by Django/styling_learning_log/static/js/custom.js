/**
 * 学习笔记 - 自定义 JavaScript 文件
 * 提供交互增强功能
 */

(function() {
    'use strict';

    // ==================== 删除确认对话框 ====================
    function initDeleteConfirmations() {
        // 为所有删除链接添加确认对话框
        const deleteLinks = document.querySelectorAll('a[href*="delete"]');
        deleteLinks.forEach(function(link) {
            link.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href && href.includes('delete')) {
                    const confirmed = confirm('确定要删除吗？此操作不可恢复！');
                    if (!confirmed) {
                        e.preventDefault();
                        return false;
                    }
                }
            });
        });
    }

    // ==================== 表单验证增强 ====================
    function initFormValidation() {
        const forms = document.querySelectorAll('form[method="post"]:not([data-skip-validation])');
        forms.forEach(function(form) {
            form.addEventListener('submit', function(e) {
                const requiredFields = form.querySelectorAll('[required]');
                let isValid = true;
                
                requiredFields.forEach(function(field) {
                    if (!field.value.trim()) {
                        isValid = false;
                        field.classList.add('is-invalid');
                        
                        // 显示错误消息
                        let errorMsg = field.parentElement.querySelector('.invalid-feedback');
                        if (!errorMsg) {
                            errorMsg = document.createElement('div');
                            errorMsg.className = 'invalid-feedback';
                            errorMsg.textContent = '此字段为必填项';
                            field.parentElement.appendChild(errorMsg);
                        }
                    } else {
                        field.classList.remove('is-invalid');
                        const errorMsg = field.parentElement.querySelector('.invalid-feedback');
                        if (errorMsg) {
                            errorMsg.remove();
                        }
                    }
                });
                
                if (!isValid) {
                    e.preventDefault();
                    // 显示错误提示
                    showNotification('请填写所有必填字段', 'error');
                }
            });
        });
    }

    // ==================== 消息通知 ====================
    function showNotification(message, type) {
        type = type || 'info';
        const alertClass = 'alert-' + (type === 'error' ? 'danger' : type);
        const notification = document.createElement('div');
        notification.className = 'alert ' + alertClass + ' alert-dismissible fade show';
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';
        notification.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
        
        document.body.appendChild(notification);
        
        // 3秒后自动关闭
        setTimeout(function() {
            notification.remove();
        }, 3000);
    }

    // ==================== 自动隐藏消息 ====================
    function initAutoHideMessages() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            setTimeout(function() {
                if (alert.classList.contains('show')) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, 5000); // 5秒后自动关闭
        });
    }

    // ==================== 搜索框增强 ====================
    function initSearchEnhancement() {
        const searchInputs = document.querySelectorAll('input[name="search"]');
        searchInputs.forEach(function(input) {
            // 添加清除按钮
            if (input.value) {
                const clearBtn = document.createElement('button');
                clearBtn.type = 'button';
                clearBtn.className = 'btn btn-sm btn-outline-secondary';
                clearBtn.innerHTML = '✕';
                clearBtn.style.marginLeft = '5px';
                clearBtn.addEventListener('click', function() {
                    input.value = '';
                    input.form.submit();
                });
                input.parentElement.appendChild(clearBtn);
            }
            
            // 回车键搜索
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.form.submit();
                }
            });
        });
    }

    // ==================== 平滑滚动 ====================
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
            anchor.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href !== '#') {
                    const target = document.querySelector(href);
                    if (target) {
                        e.preventDefault();
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                }
            });
        });
    }

    // ==================== 加载状态 ====================
    function initLoadingStates() {
        const forms = document.querySelectorAll('form');
        forms.forEach(function(form) {
            form.addEventListener('submit', function(e) {
                // 对于有 data-skip-validation 的表单，确保不阻止提交
                const submitBtn = form.querySelector('button[type="submit"], button[name="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    const originalText = submitBtn.innerHTML;
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>处理中...';
                    
                    // 如果表单验证失败，恢复按钮状态（延迟恢复，给服务器响应时间）
                    setTimeout(function() {
                        if (submitBtn.disabled) {
                            submitBtn.disabled = false;
                            submitBtn.innerHTML = originalText;
                        }
                    }, 3000);
                }
            });
        });
    }

    // ==================== 卡片悬停效果 ====================
    function initCardHover() {
        const cards = document.querySelectorAll('.card');
        cards.forEach(function(card) {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-2px)';
            });
            
            card.addEventListener('mouseleave', function() {
                this.style.transform = 'translateY(0)';
            });
        });
    }

    // ==================== 响应式导航栏 ====================
    function initResponsiveNavbar() {
        const navbarToggler = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');
        
        if (navbarToggler && navbarCollapse) {
            // 点击外部关闭移动端菜单
            document.addEventListener('click', function(e) {
                if (!navbarToggler.contains(e.target) && 
                    !navbarCollapse.contains(e.target) &&
                    navbarCollapse.classList.contains('show')) {
                    navbarToggler.click();
                }
            });
        }
    }

    // ==================== 键盘快捷键支持 ====================
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + K: 聚焦搜索框
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('input[name="search"]');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }
            
            // Ctrl/Cmd + N: 新建主题/笔记
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                const newTopicLink = document.querySelector('a[href*="new_topic"]');
                const newEntryLink = document.querySelector('a[href*="new_entry"]');
                if (newEntryLink) {
                    window.location.href = newEntryLink.href;
                } else if (newTopicLink) {
                    window.location.href = newTopicLink.href;
                }
            }
            
            // Esc: 清除搜索
            if (e.key === 'Escape') {
                const searchInput = document.querySelector('input[name="search"]');
                if (searchInput && searchInput.value) {
                    searchInput.value = '';
                    const clearBtn = document.querySelector('a[href*="topics"], a[href*="topic"]');
                    if (clearBtn && clearBtn.textContent.includes('清除')) {
                        window.location.href = clearBtn.href;
                    }
                }
            }
            
            // Ctrl/Cmd + Enter: 提交表单
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                const form = document.querySelector('form');
                if (form && form.querySelector('textarea, input[type="text"]')) {
                    const submitBtn = form.querySelector('button[type="submit"]');
                    if (submitBtn && !submitBtn.disabled) {
                        e.preventDefault();
                        form.submit();
                    }
                }
            }
        });
        
        // 显示快捷键提示
        if (document.querySelector('input[name="search"]')) {
            const searchInput = document.querySelector('input[name="search"]');
            if (searchInput && !searchInput.parentElement.querySelector('.shortcut-hint')) {
                const hint = document.createElement('small');
                hint.className = 'shortcut-hint text-muted';
                hint.textContent = '快捷键: Ctrl+K 聚焦搜索';
                hint.style.display = 'block';
                hint.style.marginTop = '5px';
                searchInput.parentElement.appendChild(hint);
            }
        }
    }

    // ==================== Markdown 预览 ====================
    function initMarkdownPreview() {
        const markdownTextarea = document.querySelector('textarea[name="text"]');
        const markdownCheckbox = document.querySelector('input[name="is_markdown"]');
        
        if (markdownTextarea && markdownCheckbox) {
            // 创建预览区域
            const previewArea = document.createElement('div');
            previewArea.className = 'markdown-preview border rounded p-3 mt-2';
            previewArea.style.display = 'none';
            previewArea.style.minHeight = '100px';
            previewArea.style.backgroundColor = '#f8f9fa';
            markdownTextarea.parentElement.appendChild(previewArea);
            
            // 简单的 Markdown 解析函数
            function parseMarkdown(text) {
                if (!text) return '';
                
                // 标题
                text = text.replace(/^### (.*$)/gim, '<h5>$1</h5>');
                text = text.replace(/^## (.*$)/gim, '<h4>$1</h4>');
                text = text.replace(/^# (.*$)/gim, '<h3>$1</h3>');
                
                // 粗体和斜体
                text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
                
                // 代码
                text = text.replace(/`(.*?)`/g, '<code>$1</code>');
                
                // 链接
                text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
                
                // 列表
                text = text.replace(/^\* (.*$)/gim, '<li>$1</li>');
                text = text.replace(/^- (.*$)/gim, '<li>$1</li>');
                text = text.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
                
                // 换行
                text = text.replace(/\n/g, '<br>');
                
                return text;
            }
            
            // 更新预览
            function updatePreview() {
                if (markdownCheckbox.checked && markdownTextarea.value) {
                    previewArea.innerHTML = parseMarkdown(markdownTextarea.value);
                    previewArea.style.display = 'block';
                } else {
                    previewArea.style.display = 'none';
                }
            }
            
            // 监听输入和复选框变化
            markdownTextarea.addEventListener('input', updatePreview);
            markdownCheckbox.addEventListener('change', updatePreview);
            
            // 添加预览切换按钮
            const toggleBtn = document.createElement('button');
            toggleBtn.type = 'button';
            toggleBtn.className = 'btn btn-sm btn-outline-secondary mt-2';
            toggleBtn.textContent = '预览 Markdown';
            toggleBtn.addEventListener('click', function() {
                if (previewArea.style.display === 'none') {
                    updatePreview();
                    this.textContent = '隐藏预览';
                } else {
                    previewArea.style.display = 'none';
                    this.textContent = '预览 Markdown';
                }
            });
            markdownTextarea.parentElement.appendChild(toggleBtn);
        }
    }

    // ==================== 增强加载动画 ====================
    function initEnhancedLoading() {
        // 页面加载动画
        const loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'page-loading-overlay';
        loadingOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.9);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
        `;
        loadingOverlay.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-3 text-muted">正在加载...</p>
            </div>
        `;
        document.body.appendChild(loadingOverlay);
        
        // 表单提交时显示加载动画
        document.querySelectorAll('form').forEach(function(form) {
            form.addEventListener('submit', function() {
                loadingOverlay.style.opacity = '1';
                loadingOverlay.style.pointerEvents = 'all';
            });
        });
        
        // 页面加载完成后隐藏
        window.addEventListener('load', function() {
            setTimeout(function() {
                loadingOverlay.style.opacity = '0';
                setTimeout(function() {
                    loadingOverlay.style.display = 'none';
                }, 300);
            }, 300);
        });
    }

    // ==================== 主题图标与颜色选择器 ====================
    function initTopicEmojiAndColorPicker() {
        const iconInput = document.querySelector('input[name="icon"]');
        const emojiButtons = document.querySelectorAll('.topic-emoji-option');
        const colorSelect = document.querySelector('select[name="color"]');
        const colorPreview = document.getElementById('topic-color-preview');

        // emoji 快速选择
        if (iconInput && emojiButtons.length > 0) {
            emojiButtons.forEach(function(btn) {
                btn.addEventListener('click', function() {
                    const emoji = this.textContent.trim();
                    iconInput.value = emoji;
                    iconInput.focus();
                });
            });
        }

        // 颜色预览
        function updateColorPreview() {
            if (!colorSelect || !colorPreview) return;
            const value = colorSelect.value || 'primary';
            colorPreview.className = 'badge rounded-pill bg-' + value + ' ms-1';
        }

        if (colorSelect && colorPreview) {
            colorSelect.addEventListener('change', updateColorPreview);
            // 初始化时更新一次
            updateColorPreview();
        }
    }

    // ==================== 代码高亮与一键复制 ====================
    function initCodeHighlightAndCopy() {
        // 使用 highlight.js 进行代码高亮（如果已加载）
        if (window.hljs) {
            document.querySelectorAll('pre code').forEach(function(block) {
                window.hljs.highlightElement(block);
            });
        }

        // 为每个代码块添加复制按钮
        const codeBlocks = document.querySelectorAll('.markdown-content pre');
        codeBlocks.forEach(function(pre) {
            // 避免重复添加
            if (pre.querySelector('.code-copy-btn')) {
                return;
            }
            const code = pre.querySelector('code');
            if (!code) return;

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'code-copy-btn';
            btn.textContent = '复制';

            btn.addEventListener('click', function() {
                const text = code.innerText || code.textContent || '';
                if (!text) return;

                // 优先使用 Clipboard API
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(text).then(function() {
                        btn.textContent = '已复制';
                        btn.classList.add('copied');
                        setTimeout(function() {
                            btn.textContent = '复制';
                            btn.classList.remove('copied');
                        }, 1500);
                    }).catch(function() {
                        fallbackCopy(text, btn);
                    });
                } else {
                    fallbackCopy(text, btn);
                }
            });

            pre.appendChild(btn);
        });

        function fallbackCopy(text, btn) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                btn.textContent = '已复制';
                btn.classList.add('copied');
                setTimeout(function() {
                    btn.textContent = '复制';
                    btn.classList.remove('copied');
                }, 1500);
            } catch (e) {
                showNotification('复制失败，请手动选择代码复制。', 'warning');
            } finally {
                document.body.removeChild(textarea);
            }
        }
    }

    // ==================== 笔记分享：复制 Markdown 片段 ====================
    function initEntryShareMarkdown() {
        const buttons = document.querySelectorAll('.entry-copy-markdown-btn');
        if (!buttons.length) return;

        buttons.forEach(function(btn) {
            const rawMarkdown = btn.dataset.markdown || '';
            if (!rawMarkdown) return;

            btn.addEventListener('click', function() {
                const text = rawMarkdown;
                if (!text) return;

                const prefix = `# ${document.title.replace('学习笔记 📚', '').trim() || '学习笔记'}\n\n`;
                const finalText = prefix + text;

                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(finalText).then(function() {
                        btn.textContent = '✅ 已复制 Markdown';
                        setTimeout(function() {
                            btn.textContent = '📋 复制 Markdown';
                        }, 1500);
                    }).catch(function() {
                        fallbackCopyMarkdown(finalText, btn);
                    });
                } else {
                    fallbackCopyMarkdown(finalText, btn);
                }
            });
        });

        function fallbackCopyMarkdown(text, btn) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                btn.textContent = '✅ 已复制 Markdown';
                setTimeout(function() {
                    btn.textContent = '📋 复制 Markdown';
                }, 1500);
            } catch (e) {
                showNotification('复制失败，请手动选择内容复制。', 'warning');
            } finally {
                document.body.removeChild(textarea);
            }
        }
    }

    // ==================== 主题打印导出 ====================
    function initTopicPrint() {
        const btn = document.querySelector('.topic-print-btn');
        if (!btn) return;

        btn.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    }

    // ==================== 初始化所有功能 ====================
    function init() {
        // 等待 DOM 加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }
        
        initDeleteConfirmations();
        initFormValidation();
        initAutoHideMessages();
        initSearchEnhancement();
        initSmoothScroll();
        initLoadingStates();
        initCardHover();
        initResponsiveNavbar();
        initKeyboardShortcuts();
        initMarkdownPreview();
        initEnhancedLoading();
        initTopicEmojiAndColorPicker();
        initCodeHighlightAndCopy();
        initEntryShareMarkdown();
        initTopicPrint();
        
        console.log('学习笔记 - 自定义 JavaScript 已加载');
    }

    // 立即初始化
    init();
})();

