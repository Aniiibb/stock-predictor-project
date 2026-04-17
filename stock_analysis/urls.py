from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/company-news/', views.company_news, name='company_news'),
    path('api/search-stock/', views.search_stock, name='search_stock'),
    path('api/popular-stocks/', views.popular_stocks, name='popular_stocks'),
    path('api/signup/', views.signup_view, name='signup'),
    path('api/login/', views.login_view, name='login'),
    path('api/watchlist/', views.watchlist, name='watchlist'),
    path('api/predict-stock/', views.predict_stock, name='predict_stock'),
]