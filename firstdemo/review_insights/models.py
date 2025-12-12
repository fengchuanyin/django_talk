from django.db import models
from django.utils import timezone

class Product(models.Model):
    """产品模型"""
    name = models.CharField(max_length=200, verbose_name='产品名称')
    description = models.TextField(blank=True, verbose_name='产品描述')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='价格')
    category = models.CharField(max_length=100, verbose_name='分类')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '产品'
        verbose_name_plural = '产品'
    
    def __str__(self):
        return self.name

class Review(models.Model):
    """评论模型"""
    SENTIMENT_CHOICES = [
        ('positive', '正面'),
        ('negative', '负面'),
        ('neutral', '中性'),
    ]
    
    RATING_CHOICES = [
        (1, '1星'),
        (2, '2星'),
        (3, '3星'),
        (4, '4星'),
        (5, '5星'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name='产品')
    author = models.CharField(max_length=100, verbose_name='评论者')
    content = models.TextField(verbose_name='评论内容')
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name='评分')
    sentiment = models.CharField(max_length=20, choices=SENTIMENT_CHOICES, verbose_name='情感倾向')
    confidence = models.FloatField(default=0.0, verbose_name='情感置信度')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='评论时间')
    
    class Meta:
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.author}"

class ReviewInsight(models.Model):
    """评论洞察模型"""
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name='insight', verbose_name='评论')
    key_topics = models.JSONField(default=list, verbose_name='关键话题')
    emotion_score = models.JSONField(default=dict, verbose_name='情感分数')
    word_count = models.IntegerField(default=0, verbose_name='词数')
    reading_time = models.IntegerField(default=0, verbose_name='阅读时间(分钟)')
    spam_score = models.FloatField(default=0.0, verbose_name='垃圾评论分数')
    helpful_votes = models.IntegerField(default=0, verbose_name='有用投票')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='分析时间')
    
    class Meta:
        verbose_name = '评论洞察'
        verbose_name_plural = '评论洞察'
    
    def __str__(self):
        return f"洞察: {self.review}"

class ProductInsight(models.Model):
    """产品洞察模型"""
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='insight', verbose_name='产品')
    total_reviews = models.IntegerField(default=0, verbose_name='总评论数')
    avg_rating = models.FloatField(default=0.0, verbose_name='平均评分')
    sentiment_distribution = models.JSONField(default=dict, verbose_name='情感分布')
    common_topics = models.JSONField(default=list, verbose_name='常见话题')
    last_updated = models.DateTimeField(auto_now=True, verbose_name='最后更新')
    
    class Meta:
        verbose_name = '产品洞察'
        verbose_name_plural = '产品洞察'
    
    def __str__(self):
        return f"洞察: {self.product.name}"
    
    def update_insights(self):
        """更新产品洞察数据"""
        reviews = self.product.reviews.all()
        self.total_reviews = reviews.count()
        
        if self.total_reviews > 0:
            # 计算平均评分
            self.avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
            
            # 计算情感分布
            sentiment_dist = {
                'positive': reviews.filter(sentiment='positive').count(),
                'negative': reviews.filter(sentiment='negative').count(),
                'neutral': reviews.filter(sentiment='neutral').count(),
            }
            self.sentiment_distribution = sentiment_dist
            
            # 获取常见话题（这里简化处理）
            # 实际应用中可能需要更复杂的NLP处理
            self.common_topics = self.extract_common_topics(reviews)
            
            self.save()
    
    def extract_common_topics(self, reviews):
        from .nlp import extract_product_clusters
        clusters = extract_product_clusters(reviews)
        labels = [c['label'] for c in clusters[:5]]
        return labels

class ReviewTrend(models.Model):
    """评论趋势模型"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='trends', verbose_name='产品')
    date = models.DateField(verbose_name='日期')
    review_count = models.IntegerField(default=0, verbose_name='评论数量')
    avg_rating = models.FloatField(default=0.0, verbose_name='平均评分')
    sentiment_score = models.FloatField(default=0.0, verbose_name='情感分数')
    
    class Meta:
        verbose_name = '评论趋势'
        verbose_name_plural = '评论趋势'
        unique_together = ['product', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.product.name} - {self.date}"
