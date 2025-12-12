// 电商评论洞察系统JavaScript功能

// 全局变量
let currentPage = 1;
let currentFilters = {};
let charts = {}; // 存储图表实例
const API_BASE = '/reviews';

// 初始化函数
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    initializeFilters();
    initializeEventListeners();
});

// 初始化图表
function initializeCharts() {
    const chartElements = document.querySelectorAll('[data-chart]');
    chartElements.forEach(element => {
        const chartType = element.dataset.chart;
        const chartData = JSON.parse(element.dataset.chartData || '{}');
        createChart(element, chartType, chartData);
    });
}

// 创建图表
function createChart(element, type, data) {
    try {
        // 检查元素是否有效
        if (!element) {
            console.warn('图表元素不存在');
            return;
        }
        
        const chartId = element.id;
        
        // 如果图表已存在，先销毁它
        if (charts[chartId]) {
            charts[chartId].destroy();
            delete charts[chartId];
        }
        
        const ctx = element.getContext('2d');
        if (!ctx) {
            console.warn('无法获取canvas上下文');
            return;
        }
        
        const config = getChartConfig(type, data);
        
        // 设置canvas高度
        if (type === 'sentiment') {
            element.style.height = '300px';
        } else if (type === 'rating') {
            element.style.height = '250px';
        } else if (type === 'trend') {
            element.style.height = '200px';
        }
        
        // 确保canvas有明确的宽高
        element.style.width = '100%';
        element.style.maxHeight = '400px';
        
        // 创建图表并存储实例
        charts[chartId] = new Chart(ctx, config);
        
    } catch (error) {
        console.error('创建图表失败:', error);
    }
}

// 获取图表配置 - 统一品牌色彩方案
function getChartConfig(type, data) {
    // 品牌色彩方案
    const brandColors = {
        primary: '#c8d900',
        secondary: '#080604',
        accent: '#c8d900',
        green: '#22c55e',
        greenLight: '#dcfce7',
        red: '#ef4444',
        redLight: '#fee2e2',
        gray: '#6b7280',
        grayLight: '#f3f4f6'
    };

    const configs = {
        sentiment: {
            type: 'doughnut',
            data: {
                labels: ['正面', '负面', '中性'],
                datasets: [{
                    data: data.values || [65, 20, 15],
                    backgroundColor: [brandColors.green, brandColors.red, brandColors.gray],
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: {
                                size: 14,
                                family: 'Noto Sans SC'
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: brandColors.secondary,
                        titleColor: 'white',
                        bodyColor: 'white',
                        cornerRadius: 8,
                        displayColors: true
                    }
                }
            }
        },
        rating: {
            type: 'bar',
            data: {
                labels: ['1星', '2星', '3星', '4星', '5星'],
                datasets: [{
                    label: '评论数量',
                    data: data.values || [10, 25, 45, 120, 200],
                    backgroundColor: [
                        brandColors.red,
                        '#f97316',
                        '#eab308',
                        brandColors.green,
                        '#059669'
                    ],
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        },
                        ticks: {
                            font: {
                                family: 'Noto Sans SC'
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                family: 'Noto Sans SC'
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: brandColors.secondary,
                        titleColor: 'white',
                        bodyColor: 'white',
                        cornerRadius: 8
                    }
                }
            }
        },
        trend: {
            type: 'line',
            data: {
                labels: data.labels || ['1月', '2月', '3月', '4月', '5月', '6月'],
                datasets: [{
                    label: '评论趋势',
                    data: data.values || [120, 150, 180, 220, 280, 320],
                    borderColor: brandColors.primary,
                    backgroundColor: 'rgba(22, 160, 133, 0.1)',
                    fill: true,
                    tension: 0.4,
                    borderWidth: 3,
                    pointBackgroundColor: brandColors.primary,
                    pointBorderColor: 'white',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        },
                        ticks: {
                            font: {
                                family: 'Noto Sans SC'
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        },
                        ticks: {
                            font: {
                                family: 'Noto Sans SC'
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: brandColors.secondary,
                        titleColor: 'white',
                        bodyColor: 'white',
                        cornerRadius: 8,
                        displayColors: false
                    }
                },
                elements: {
                    point: {
                        hoverBackgroundColor: brandColors.accent
                    }
                }
            }
        }
        ,
        topic: {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        label: '正面',
                        data: data.pos || [],
                        backgroundColor: '#22c55e',
                        stack: 'sentiment'
                    },
                    {
                        label: '中性',
                        data: data.neu || [],
                        backgroundColor: '#6b7280',
                        stack: 'sentiment'
                    },
                    {
                        label: '负面',
                        data: data.neg || [],
                        backgroundColor: '#ef4444',
                        stack: 'sentiment'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { stacked: true },
                    y: { stacked: true, beginAtZero: true }
                },
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        backgroundColor: brandColors.secondary,
                        titleColor: 'white',
                        bodyColor: 'white',
                        cornerRadius: 8
                    }
                }
            }
        }
    };
    
    return configs[type] || configs.sentiment;
}

// 初始化筛选器
function initializeFilters() {
    const filterElements = document.querySelectorAll('[data-filter]');
    filterElements.forEach(element => {
        element.addEventListener('change', applyFilters);
    });
}

// 初始化事件监听器
function initializeEventListeners() {
    // 分页按钮
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('page-link')) {
            e.preventDefault();
            const page = e.target.dataset.page;
            if (page) {
                loadPage(parseInt(page));
            }
        }
    });

    // 评论卡片点击
    document.addEventListener('click', function(e) {
        const reviewCard = e.target.closest('.review-card');
        if (reviewCard) {
            const reviewId = reviewCard.dataset.reviewId;
            if (reviewId) {
                showReviewDetail(reviewId);
            }
        }
    });

    // 刷新按钮
    const refreshBtn = document.getElementById('refresh-data');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshData);
    }
}

// 应用筛选器
function applyFilters() {
    const filters = {};
    const filterElements = document.querySelectorAll('[data-filter]');
    
    filterElements.forEach(element => {
        const filterName = element.dataset.filter;
        const filterValue = element.value;
        if (filterValue) {
            filters[filterName] = filterValue;
        }
    });
    
    currentFilters = filters;
    loadFilteredData(filters);
}

// 加载筛选数据
function loadFilteredData(filters) {
    showLoading();
    
    // 模拟API调用
    setTimeout(() => {
        fetch(API_BASE + '/api/reviews/?' + new URLSearchParams(filters))
            .then(response => {
                const ct = response.headers.get('content-type') || '';
                if (!response.ok || !ct.includes('application/json')) {
                    throw new Error('接口返回非JSON');
                }
                return response.json();
            })
            .then(data => {
                updateReviewList(data.reviews);
                updatePagination(data.pagination);
                hideLoading();
            })
            .catch(error => {
                console.error('加载数据失败:', error);
                hideLoading();
                showError('数据加载失败，请重试');
            });
    }, 500);
}

// 加载指定页面
function loadPage(page) {
    currentPage = page;
    const filters = { ...currentFilters, page: page };
    loadFilteredData(filters);
}

// 更新评论列表
function updateReviewList(reviews) {
    const reviewList = document.getElementById('review-list');
    if (!reviewList) return;
    
    reviewList.innerHTML = '';
    
    reviews.forEach(review => {
        const reviewCard = createReviewCard(review);
        reviewList.appendChild(reviewCard);
    });
}

// 创建评论卡片
function createReviewCard(review) {
    const card = document.createElement('div');
    card.className = 'review-card card p-3';
    card.dataset.reviewId = review.id;
    
    const sentimentClass = `sentiment-${review.sentiment}`;
    const sentimentText = {
        'positive': '正面',
        'negative': '负面',
        'neutral': '中性'
    }[review.sentiment] || '未知';
    
    card.innerHTML = `
        <div class="review-header">
            <div>
                <strong>${review.product_name}</strong>
                <div class="review-rating">
                    ${'★'.repeat(review.rating)}${'☆'.repeat(5 - review.rating)}
                </div>
            </div>
            <span class="review-sentiment ${sentimentClass}">${sentimentText}</span>
        </div>
        <p class="review-content mb-2">${review.content}</p>
        <div class="review-meta text-muted small">
            <span><i class="fas fa-user me-1"></i>${review.author}</span>
            <span class="ms-3"><i class="fas fa-clock me-1"></i>${review.created_at}</span>
        </div>
    `;
    
    return card;
}

// 更新分页
function updatePagination(pagination) {
    const paginationElement = document.getElementById('pagination');
    if (!paginationElement) return;
    
    let paginationHTML = '';
    
    // 上一页
    if (pagination.has_previous) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" data-page="${pagination.current_page - 1}">上一页</a>
            </li>
        `;
    }
    
    // 页码
    for (let i = 1; i <= pagination.total_pages; i++) {
        const activeClass = i === pagination.current_page ? 'active' : '';
        paginationHTML += `
            <li class="page-item ${activeClass}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>
        `;
    }
    
    // 下一页
    if (pagination.has_next) {
        paginationHTML += `
            <li class="page-item">
                <a class="page-link" href="#" data-page="${pagination.current_page + 1}">下一页</a>
            </li>
        `;
    }
    
    paginationElement.innerHTML = paginationHTML;
}

// 显示评论详情
function showReviewDetail(reviewId) {
    // 模拟API调用
    fetch(API_BASE + `/api/reviews/${reviewId}/`)
        .then(response => {
            const ct = response.headers.get('content-type') || '';
            if (!response.ok || !ct.includes('application/json')) {
                throw new Error('接口返回非JSON');
            }
            return response.json();
        })
        .then(review => {
            const modal = new bootstrap.Modal(document.getElementById('reviewModal'));
            const modalBody = document.querySelector('#reviewModal .modal-body');
            
            modalBody.innerHTML = `
                <h5>${review.product_name}</h5>
                <div class="review-rating mb-3">
                    ${'★'.repeat(review.rating)}${'☆'.repeat(5 - review.rating)}
                </div>
                <p><strong>评论内容：</strong></p>
                <p>${review.content}</p>
                <hr>
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>作者：</strong> ${review.author}</p>
                        <p><strong>评分：</strong> ${review.rating}/5</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>情感分析：</strong> 
                            <span class="review-sentiment sentiment-${review.sentiment}">
                                ${review.sentiment === 'positive' ? '正面' : 
                                  review.sentiment === 'negative' ? '负面' : '中性'}
                            </span>
                        </p>
                        <p><strong>发布时间：</strong> ${review.created_at}</p>
                    </div>
                </div>
            `;
            
            modal.show();
        })
        .catch(error => {
            console.error('加载评论详情失败:', error);
            showError('加载评论详情失败');
        });
}

// 刷新数据
function refreshData() {
    showLoading();
    
    // 重新加载当前页面数据
    loadFilteredData({ ...currentFilters, page: currentPage });
    
    // 刷新图表前先销毁现有图表
    setTimeout(() => {
        // 销毁所有现有图表
        Object.keys(charts).forEach(chartId => {
            if (charts[chartId]) {
                charts[chartId].destroy();
                delete charts[chartId];
            }
        });
        
        // 重新初始化图表
        initializeCharts();
        hideLoading();
    }, 1000);
}

// 显示加载状态
function showLoading() {
    const loadingElement = document.getElementById('loading-indicator');
    if (loadingElement) {
        loadingElement.style.display = 'block';
    }
}

// 隐藏加载状态
function hideLoading() {
    const loadingElement = document.getElementById('loading-indicator');
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
}

// 显示错误信息
function showError(message) {
    const alertContainer = document.getElementById('alert-container');
    if (alertContainer) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        alertContainer.appendChild(alert);
        
        // 3秒后自动关闭
        setTimeout(() => {
            alert.remove();
        }, 3000);
    }
}

// 工具函数
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatNumber(number) {
    return new Intl.NumberFormat('zh-CN').format(number);
}

// 导出函数供全局使用
window.ReviewInsights = {
    initializeCharts,
    applyFilters,
    refreshData,
    loadPage
};