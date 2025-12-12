from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from review_insights.models import Product, Review, ProductInsight

class Command(BaseCommand):
    help = '创建示例评论数据用于演示'

    def add_arguments(self, parser):
        parser.add_argument(
            '--products',
            type=int,
            default=5,
            help='要创建的产品数量'
        )
        parser.add_argument(
            '--reviews',
            type=int,
            default=50,
            help='每个产品的评论数量'
        )

    def handle(self, *args, **options):
        products_count = options['products']
        reviews_per_product = options['reviews']
        
        self.stdout.write(self.style.SUCCESS(f'开始创建 {products_count} 个产品，每个产品 {reviews_per_product} 条评论...'))
        
        # 产品数据
        product_data = [
            {'name': 'iPhone 15 Pro', 'category': '手机', 'price': 7999},
            {'name': 'MacBook Air M2', 'category': '笔记本', 'price': 8999},
            {'name': 'AirPods Pro', 'category': '耳机', 'price': 1999},
            {'name': 'iPad Air', 'category': '平板', 'price': 4399},
            {'name': 'Apple Watch Series 9', 'category': '智能手表', 'price': 2999},
        ]
        
        # 正面评论模板
        positive_reviews = [
            "产品质量非常好，超出预期！",
            "物流很快，包装精美，非常满意。",
            "性价比很高，推荐购买。",
            "用了一段时间，感觉很不错。",
            "外观设计很漂亮，功能也很强大。",
            "客服态度很好，解决问题很及时。",
            "这个品牌值得信赖，会继续支持。",
            "朋友推荐买的，确实不错。",
            "细节处理得很好，看得出很用心。",
            "整体体验很棒，会回购的。"
        ]
        
        # 负面评论模板
        negative_reviews = [
            "质量一般，有点失望。",
            "价格偏高，性价比不太好。",
            "物流太慢了，等了很久。",
            "产品有些小问题，不太满意。",
            "客服响应速度有待提高。",
            "和描述的不太一样。",
            "用起来不太顺手。",
            "包装有些破损。",
            "感觉不值这个价钱。",
            "有些功能不太实用。"
        ]
        
        # 中性评论模板
        neutral_reviews = [
            "产品还可以，符合预期。",
            "价格合理，质量一般。",
            "物流速度正常。",
            "整体感觉还行。",
            "功能基本够用。",
            "外观还可以。",
            "用了一段时间，没什么特别的感觉。",
            "中规中矩的产品。",
            "满足基本需求。",
            "一般般吧。"
        ]
        
        created_products = []
        
        # 创建产品
        for i in range(min(products_count, len(product_data))):
            data = product_data[i]
            product = Product.objects.create(
                name=data['name'],
                description=f"这是 {data['name']} 的详细描述",
                price=data['price'],
                category=data['category']
            )
            created_products.append(product)
            self.stdout.write(f'  创建产品: {product.name}')
        
        # 为每个产品创建评论
        for product in created_products:
            for i in range(reviews_per_product):
                # 随机选择评论类型（60%正面，25%中性，15%负面）
                rand = random.randint(1, 100)
                if rand <= 60:
                    sentiment = 'positive'
                    content = random.choice(positive_reviews)
                    rating = random.randint(4, 5)
                    confidence = random.randint(70, 95)
                elif rand <= 85:
                    sentiment = 'neutral'
                    content = random.choice(neutral_reviews)
                    rating = random.randint(3, 4)
                    confidence = random.randint(40, 70)
                else:
                    sentiment = 'negative'
                    content = random.choice(negative_reviews)
                    rating = random.randint(1, 3)
                    confidence = random.randint(60, 90)
                
                # 随机生成作者名
                authors = ['张三', '李四', '王五', '赵六', '钱七', '孙八', '周九', '吴十']
                author = random.choice(authors)
                
                # 随机生成时间（最近30天内）
                days_ago = random.randint(0, 30)
                created_at = timezone.now() - timedelta(days=days_ago)
                
                review = Review.objects.create(
                    product=product,
                    author=author,
                    content=content,
                    rating=rating,
                    sentiment=sentiment,
                    confidence=confidence,
                    created_at=created_at
                )
        
        # 创建或更新产品洞察
        for product in created_products:
            insight, created = ProductInsight.objects.get_or_create(product=product)
            insight.update_insights()
            
            if created:
                self.stdout.write(f'  创建产品洞察: {product.name}')
            else:
                self.stdout.write(f'  更新产品洞察: {product.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'成功创建 {len(created_products)} 个产品，共 {len(created_products) * reviews_per_product} 条评论！'
            )
        )