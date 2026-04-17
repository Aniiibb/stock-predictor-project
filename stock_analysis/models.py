from django.db import models
from django.contrib.auth.models import User


class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"

class StockPrediction(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    prediction = models.CharField(max_length=10)  # 'UP' or 'DOWN'
    confidence = models.FloatField()
    prediction_date = models.DateTimeField(auto_now_add=True)
    reasoning = models.TextField()
    chart = models.ImageField(upload_to='prediction_charts/', blank=True, null=True)

    def __str__(self):
        return f"{self.stock.symbol} - {self.prediction} ({self.confidence}%)"

class WatchlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist_items')
    symbol = models.CharField(max_length=10)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'symbol')
        
    def __str__(self):
        return f"{self.user.username} - {self.symbol}"
