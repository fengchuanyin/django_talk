import pandas as pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from review_insights.models import Product, Review, ProductInsight
import math

class Command(BaseCommand):
    help = 'Import reviews from Excel file'

    def handle(self, *args, **options):
        # Look for file in current dir or parent dir
        file_name = 'jd_comments_100283678024.xlsx'
        import os
        if os.path.exists(file_name):
            file_path = file_name
        elif os.path.exists(os.path.join('..', file_name)):
            file_path = os.path.join('..', file_name)
        else:
            # Try absolute path if known
            file_path = r'c:\Users\cby\Desktop\django_talk\jd_comments_100283678024.xlsx'
            
        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading excel: {e}'))
            return

        # Create Product
        # Try to infer product name from first row content or filename
        product_name = 'iQOO 15' 
        # Check if first row has "iQOO"
        if not df.empty and '评价内容' in df.columns:
            first_content = str(df.iloc[0]['评价内容'])
            if 'iQOO 15' in first_content:
                product_name = 'iQOO 15'
        
        product, created = Product.objects.get_or_create(
            name=product_name,
            defaults={
                'description': 'Imported from Excel',
                'price': 0,
                'category': '手机'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created product: {product.name}'))
        else:
            self.stdout.write(f'Using existing product: {product.name}')

        # Keywords for sentiment
        pos_keywords = ['好', '棒', '强', '快', '满意', '惊喜', '顺滑', '喜欢', '不错', '爱', '美', '出色', '稳', '细节', '信赖']
        neg_keywords = ['差', '慢', '卡', '坏', '失望', '不行', '贵', '退', '漏', '旧', '破', '问题', '一般']

        count = 0
        for index, row in df.iterrows():
            content = row['评价内容']
            if not isinstance(content, str) or not content.strip():
                continue

            author = row['用户昵称']
            if not isinstance(author, str) or pd.isna(author):
                author = 'Anonymous'
            
            date_str = row['评价日期']
            # Parse date '12-09'
            try:
                created_at = timezone.now()
                if isinstance(date_str, str) and '-' in date_str:
                    parts = date_str.split('-')
                    if len(parts) == 2:
                        # Assume current year 2025
                        current_year = 2025
                        dt = datetime(current_year, int(parts[0]), int(parts[1]))
                        # If date is in future (e.g. file from 2024 but we assume 2025), subtract a year
                        if dt > datetime.now():
                            dt = datetime(current_year - 1, int(parts[0]), int(parts[1]))
                        
                        created_at = timezone.make_aware(dt)
            except Exception as e:
                # self.stdout.write(f"Date parse error: {e}")
                pass

            # Sentiment logic
            sentiment = 'neutral'
            rating = 5 # Default high for JD usually
            
            # Simple scoring
            pos_score = sum(1 for w in pos_keywords if w in content)
            neg_score = sum(1 for w in neg_keywords if w in content)
            
            if pos_score > neg_score:
                sentiment = 'positive'
                rating = 5
            elif neg_score > pos_score:
                sentiment = 'negative'
                rating = 1 # Or 2/3
            else:
                sentiment = 'neutral'
                rating = 3 # Neutral
                # If content is long and no negative words, maybe positive?
                if len(content) > 20 and neg_score == 0:
                     sentiment = 'positive'
                     rating = 5

            # Avoid duplicates (optional, slow for many reviews but fine here)
            # if Review.objects.filter(product=product, author=author, content=content).exists():
            #     continue

            Review.objects.create(
                product=product,
                author=author,
                content=content,
                rating=rating,
                sentiment=sentiment,
                confidence=0.8 if sentiment != 'neutral' else 0.5,
                created_at=created_at
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {count} reviews.'))

        # Update Insights
        insight, _ = ProductInsight.objects.get_or_create(product=product)
        insight.update_insights()
        insight.save()
        self.stdout.write(self.style.SUCCESS('Updated product insights.'))
