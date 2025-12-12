from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import Product, Review, ProductInsight, ReviewTrend

def dashboard(request):
    """仪表板视图 - 显示演示页面"""
    return render(request, 'review_insights/demo.html')

def reviews_list(request):
    """评论列表视图"""
    # 获取筛选参数
    product_id = request.GET.get('product')
    rating = request.GET.get('rating')
    sentiment = request.GET.get('sentiment')
    search = request.GET.get('search')
    
    # 基础查询集
    reviews = Review.objects.select_related('product').all()
    
    # 应用筛选
    if product_id:
        reviews = reviews.filter(product_id=product_id)
    if rating:
        reviews = reviews.filter(rating=rating)
    if sentiment:
        reviews = reviews.filter(sentiment=sentiment)
    if search:
        reviews = reviews.filter(
            Q(content__icontains=search) |
            Q(product__name__icontains=search) |
            Q(author__icontains=search)
        )
    
    # 分页
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 获取产品列表用于筛选
    products = Product.objects.all()
    current_product_insight = None
    if product_id:
        try:
            product = Product.objects.get(id=product_id)
            current_product_insight, created = ProductInsight.objects.get_or_create(product=product)
            current_product_insight.update_insights()
        except Product.DoesNotExist:
            current_product_insight = None
    risk_list = ['物流','售后','价格','包装','质量','服务']
    
    context = {
        'page_obj': page_obj,
        'products': products,
        'current_filters': {
            'product': product_id,
            'rating': rating,
            'sentiment': sentiment,
            'search': search,
        },
        'current_product_insight': current_product_insight,
        'risk_list': risk_list,
    }
    
    return render(request, 'review_insights/reviews.html', context)

def analytics(request):
    """数据分析视图"""
    # 获取产品列表
    products = Product.objects.all()
    
    # 获取总体统计
    total_reviews = Review.objects.count()
    sentiment_distribution = Review.objects.values('sentiment').annotate(
        count=Count('sentiment')
    )

    from .nlp import build_global_clusters
    global_clusters = build_global_clusters(Review.objects.all(), n_clusters=8, top_tokens=3, evidence_per_cluster=2)
    topic_labels = []
    topic_pos = []
    topic_neg = []
    topic_neu = []
    topic_evidence = []
    for c in global_clusters:
        total = c['positive'] + c['negative'] + c['neutral']
        if total > 0:
            topic_labels.append(c['label'])
            topic_pos.append(c['positive'])
            topic_neg.append(c['negative'])
            topic_neu.append(c['neutral'])
            topic_evidence.append({'label': c['label'], 'samples': c['samples']})

    consumer_advice = []
    def neg_ratio_for_keyword(k):
        for c in global_clusters:
            if k in c['label']:
                t = c['positive'] + c['negative'] + c['neutral']
                if t == 0:
                    continue
                r = c['negative'] / t
                if r > 0.0:
                    return r
        return 0.0
    if neg_ratio_for_keyword('价格') > 0.25:
        consumer_advice.append('关注价格与促销时点，比较同类产品的性价比')
    if neg_ratio_for_keyword('物流') > 0.20:
        consumer_advice.append('选择高评分店铺或付费加急，避免高峰期发货延迟')
    if neg_ratio_for_keyword('售后') > 0.15:
        consumer_advice.append('购买前确认退换货政策与质保流程，保留沟通记录')
    if neg_ratio_for_keyword('包装') > 0.15:
        consumer_advice.append('要求加固包装或当面签收验货，避免运输损伤')
    
    # 获取产品洞察数据，如果不存在则创建空的
    product_insights = []
    for product in products:
        insight, created = ProductInsight.objects.get_or_create(
            product=product,
            defaults={
                'total_reviews': 0,
                'avg_rating': 0.0,
                'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                'common_topics': []
            }
        )
        # 更新洞察数据
        if not created:
            insight.update_insights()
        product_insights.append(insight)

    reputation_guides = []
    for insight in product_insights:
        total = max(insight.total_reviews, 1)
        pos = int(insight.sentiment_distribution.get('positive', 0) or 0)
        neg = int(insight.sentiment_distribution.get('negative', 0) or 0)
        neu = int(insight.sentiment_distribution.get('neutral', 0) or 0)
        pos_ratio = pos / total
        score = int(round((insight.avg_rating / 5.0) * 60 + pos_ratio * 40))
        if score >= 85:
            tier = '强烈推荐'
        elif score >= 70:
            tier = '推荐'
        elif score >= 55:
            tier = '一般'
        elif score >= 40:
            tier = '谨慎'
        else:
            tier = '不推荐'
        from .nlp import extract_product_clusters, pros_cons_from_clusters
        clusters = extract_product_clusters(insight.product.reviews.all())
        pros, cons = pros_cons_from_clusters(clusters, top_n=3)
        reputation_guides.append({
            'product': insight.product,
            'score': score,
            'tier': tier,
            'pros': pros,
            'cons': cons,
            'sentiment': {
                'positive': int(round(pos_ratio * 100)),
                'negative': int(round((neg / total) * 100)),
                'neutral': int(round((neu / total) * 100))
            }
        })
    
    # 获取趋势数据
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=90)  # 最近90天
    
    trends = ReviewTrend.objects.filter(
        date__range=[start_date, end_date]
    ).select_related('product').order_by('-date')
    
    context = {
        'products': products,
        'total_reviews': total_reviews,
        'sentiment_distribution': list(sentiment_distribution),
        'product_insights': product_insights,
        'trends': trends,
        'reputation_guides': reputation_guides,
        'topic_matrix': {
            'labels': topic_labels,
            'pos': topic_pos,
            'neg': topic_neg,
            'neu': topic_neu,
        },
        'topic_evidence': topic_evidence,
        'consumer_advice': consumer_advice,
    }
    
    return render(request, 'review_insights/analytics.html', context)

def review_detail(request, review_id):
    """评论详情视图"""
    try:
        review = Review.objects.select_related('product').get(id=review_id)
        context = {
            'review': review
        }
        return render(request, 'review_insights/review_detail.html', context)
    except Review.DoesNotExist:
        return JsonResponse({'error': '评论不存在'}, status=404)

def product_report(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        insight, created = ProductInsight.objects.get_or_create(product=product)
        insight.update_insights()
        total = max(insight.total_reviews, 1)
        pos = int(insight.sentiment_distribution.get('positive', 0) or 0)
        neg = int(insight.sentiment_distribution.get('negative', 0) or 0)
        neu = int(insight.sentiment_distribution.get('neutral', 0) or 0)
        pos_ratio = pos / total
        score = int(round((insight.avg_rating / 5.0) * 60 + pos_ratio * 40))
        tier = '强烈推荐' if score>=85 else ('推荐' if score>=70 else ('一般' if score>=55 else ('谨慎' if score>=40 else '不推荐')))
        risk_keywords = ['物流','售后','价格','包装','质量','服务']
        cons = []
        for t in insight.common_topics:
            if t in risk_keywords:
                cons.append(t)
            if len(cons) >= 5:
                break
        pros = []
        for t in insight.common_topics:
            if t not in cons:
                pros.append(t)
            if len(pros) >= 5:
                break
        lines = []
        lines.append(f"# 产品口碑总结报告 - {product.name}")
        lines.append("")
        lines.append(f"- 综合口碑分: {score} / 100")
        lines.append(f"- 推荐等级: {tier}")
        lines.append(f"- 平均评分: {insight.avg_rating:.1f} / 5")
        lines.append(f"- 总评论数: {insight.total_reviews}")
        lines.append(f"- 情感分布: 正面 {int(round(pos_ratio*100))}%, 负面 {int(round(neg/total*100))}%, 中性 {int(round(neu/total*100))}%")
        lines.append("")
        lines.append("## 优点")
        if pros:
            for p in pros:
                lines.append(f"- {p}")
        else:
            lines.append("- 暂无明显优点")
        lines.append("")
        lines.append("## 缺点")
        if cons:
            for c in cons:
                lines.append(f"- {c}")
        else:
            lines.append("- 暂无明显缺点")
        lines.append("")
        lines.append("## 购买建议")
        suggestions = []
        if neg/total > 0.2:
            suggestions.append("关注差评集中话题，优先规避该产品的薄弱点")
        suggestions.append("比较同类产品的价格与服务，择优购买")
        if '物流' in cons:
            suggestions.append("选择高评分店铺或加急配送以避免延迟")
        if '售后' in cons or '客服' in cons:
            suggestions.append("确认退换货与质保流程，保留沟通记录")
        if '包装' in cons:
            suggestions.append("要求加固包装或验货签收")
        for s in suggestions:
            lines.append(f"- {s}")
        content = "\n".join(lines)
        resp = HttpResponse(content, content_type='text/markdown; charset=utf-8')
        resp['Content-Disposition'] = f'attachment; filename="{product.name}-口碑报告.md"'
        return resp
    except Product.DoesNotExist:
        return JsonResponse({'error': '产品不存在'}, status=404)

# API视图
@require_http_methods(["GET"])
def api_reviews(request):
    """API: 获取评论列表"""
    # 获取筛选参数
    product_id = request.GET.get('product')
    rating = request.GET.get('rating')
    sentiment = request.GET.get('sentiment')
    search = request.GET.get('search')
    page = int(request.GET.get('page', 1))
    
    # 基础查询集
    reviews = Review.objects.select_related('product').all()
    
    # 应用筛选
    if product_id:
        reviews = reviews.filter(product_id=product_id)
    if rating:
        reviews = reviews.filter(rating=rating)
    if sentiment:
        reviews = reviews.filter(sentiment=sentiment)
    if search:
        reviews = reviews.filter(
            Q(content__icontains=search) |
            Q(product__name__icontains=search) |
            Q(author__icontains=search)
        )
    
    # 分页
    paginator = Paginator(reviews, 10)
    page_obj = paginator.get_page(page)
    
    # 序列化数据
    reviews_data = []
    for review in page_obj:
        reviews_data.append({
            'id': review.id,
            'product_name': review.product.name,
            'author': review.author,
            'content': review.content,
            'rating': review.rating,
            'sentiment': review.sentiment,
            'confidence': review.confidence,
            'created_at': review.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return JsonResponse({
        'reviews': reviews_data,
        'pagination': {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'total_items': paginator.count
        }
    })

@require_http_methods(["GET"])
def api_review_detail(request, review_id):
    """API: 获取评论详情"""
    try:
        review = Review.objects.select_related('product').get(id=review_id)
        
        review_data = {
            'id': review.id,
            'product_name': review.product.name,
            'author': review.author,
            'content': review.content,
            'rating': review.rating,
            'sentiment': review.sentiment,
            'confidence': review.confidence,
            'created_at': review.created_at.strftime('%Y-%m-%d %H:%M')
        }
        
        return JsonResponse(review_data)
    except Review.DoesNotExist:
        return JsonResponse({'error': '评论不存在'}, status=404)

@require_http_methods(["GET"])
def api_dashboard_stats(request):
    """API: 获取仪表板统计数据"""
    total_products = Product.objects.count()
    total_reviews = Review.objects.count()
    avg_rating = Review.objects.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
    
    # 获取情感分布
    sentiment_stats = list(Review.objects.values('sentiment').annotate(
        count=Count('sentiment')
    ).order_by('-count'))
    
    # 获取评分分布
    rating_stats = list(Review.objects.values('rating').annotate(
        count=Count('rating')
    ).order_by('rating'))
    
    return JsonResponse({
        'total_products': total_products,
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 1),
        'sentiment_stats': sentiment_stats,
        'rating_stats': rating_stats
    })

@require_http_methods(["POST"])
def api_reviews_import(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({'error': '无效JSON'}, status=400)
    items = payload if isinstance(payload, list) else payload.get('items')
    if not isinstance(items, list):
        return JsonResponse({'error': '缺少items数组'}, status=400)
    created = 0
    skipped = 0
    errors = 0
    products_updated = set()
    for it in items:
        try:
            product_name = (it.get('product_name') or '').strip()
            if not product_name:
                errors += 1
                continue
            product, _ = Product.objects.get_or_create(name=product_name, defaults={
                'description': it.get('product_description') or '',
                'price': it.get('product_price') or 0,
                'category': it.get('category') or ''
            })
            content = (it.get('content') or '').strip()
            if not content:
                errors += 1
                continue
            author = (it.get('author') or '').strip() or '匿名'
            rating = int(it.get('rating') or 0)
            if rating < 1:
                rating = 1
            if rating > 5:
                rating = 5
            sentiment = (it.get('sentiment') or 'neutral').strip()
            if sentiment not in ['positive', 'negative', 'neutral']:
                sentiment = 'neutral'
            created_at_raw = it.get('created_at')
            dt = None
            if isinstance(created_at_raw, str):
                try:
                    dt = datetime.fromisoformat(created_at_raw)
                except Exception:
                    dt = None
            created_at = dt or timezone.now()
            exists = Review.objects.filter(product=product, author=author, content=content, created_at=created_at).exists()
            if exists:
                skipped += 1
                continue
            Review.objects.create(
                product=product,
                author=author,
                content=content,
                rating=rating,
                sentiment=sentiment,
                confidence=float(it.get('confidence') or 0.0),
                created_at=created_at
            )
            products_updated.add(product.id)
            created += 1
        except Exception:
            errors += 1
    for pid in products_updated:
        try:
            p = Product.objects.get(id=pid)
            insight, _ = ProductInsight.objects.get_or_create(product=p)
            insight.update_insights()
        except Exception:
            pass
    return JsonResponse({'created': created, 'skipped': skipped, 'errors': errors})

def insight_report_ui(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'error': '产品不存在'}, status=404)
    insight, _ = ProductInsight.objects.get_or_create(product=product)
    insight.update_insights()
    total = max(insight.total_reviews, 1)
    pos = int(insight.sentiment_distribution.get('positive', 0) or 0)
    neg = int(insight.sentiment_distribution.get('negative', 0) or 0)
    neu = int(insight.sentiment_distribution.get('neutral', 0) or 0)
    pos_ratio = pos / total
    score100 = int(round((insight.avg_rating / 5.0) * 60 + pos_ratio * 40))
    score10 = round(score100 / 10.0, 1)
    stars = int(round(insight.avg_rating))
    from .nlp import extract_product_clusters, pros_cons_from_clusters
    clusters = extract_product_clusters(product.reviews.all())
    pros, cons = pros_cons_from_clusters(clusters, top_n=3)
    keywords = []
    for c in clusters:
        label = c.get('label') or ''
        s = c.get('positive', 0) + c.get('neutral', 0) + c.get('negative', 0)
        if label:
            keywords.append({'text': label, 'weight': s})
    keywords = sorted(keywords, key=lambda x: x['weight'], reverse=True)[:12]
    recent = list(Review.objects.filter(product=product).order_by('-created_at')[:20])
    reviews精选 = []
    reviews正面 = []
    reviews负面 = []
    for r in recent:
        item = {
            'author': r.author,
            'date': r.created_at.strftime('%Y-%m-%d'),
            'rating': r.rating,
            'sentiment': r.sentiment,
            'content': r.content[:140] + ('…' if len(r.content) > 140 else ''),
            'id': r.id
        }
        if len(reviews精选) < 5:
            reviews精选.append(item)
        if r.sentiment == 'positive' and len(reviews正面) < 5:
            reviews正面.append(item)
        if r.sentiment == 'negative' and len(reviews负面) < 5:
            reviews负面.append(item)
    hours_ago = None
    if insight.last_updated:
        diff = timezone.now() - insight.last_updated
        hours_ago = max(0, int(diff.total_seconds() // 3600))
    sentiment_pct = {
        'positive': int(round(pos / total * 100)),
        'neutral': int(round(neu / total * 100)),
        'negative': int(round(neg / total * 100)),
    }
    advice = '适合追求极致性能的用户。相比上代重量减轻，但发热问题依然存在。建议搭配散热配件使用。'
    context = {
        'product': product,
        'score10': score10,
        'stars': stars,
        'review_count': total,
        'advice': advice,
        'sentiment_pct': sentiment_pct,
        'pros': pros,
        'cons': cons,
        'keywords': keywords,
        'reviews精选': reviews精选,
        'reviews正面': reviews正面,
        'reviews负面': reviews负面,
        'hours_ago': hours_ago,
    }
    return render(request, 'review_insights/insight_report.html', context)
