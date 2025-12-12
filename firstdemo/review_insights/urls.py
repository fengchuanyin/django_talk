from django.urls import path
from . import views

app_name = 'review_insights'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('reviews/', views.reviews_list, name='reviews'),
    path('analytics/', views.analytics, name='analytics'),
    path('review/<int:review_id>/', views.review_detail, name='review_detail'),
    path('report/<int:product_id>/', views.product_report, name='product_report'),
    path('insight/<int:product_id>/', views.insight_report_ui, name='insight_report_ui'),
    
    # API endpoints
    path('api/reviews/', views.api_reviews, name='api_reviews'),
    path('api/reviews/<int:review_id>/', views.api_review_detail, name='api_review_detail'),
    path('api/dashboard/stats/', views.api_dashboard_stats, name='api_dashboard_stats'),
    path('api/reviews/import/', views.api_reviews_import, name='api_reviews_import'),
]
