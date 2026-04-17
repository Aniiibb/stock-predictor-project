from django.core.management.base import BaseCommand
from stock_analysis.models import Stock

class Command(BaseCommand):
    help = 'Populates initial stock data'

    def handle(self, *args, **kwargs):
        stocks = [
            {'symbol': 'AAPL', 'name': 'Apple Inc.'},
            {'symbol': 'TSLA', 'name': 'Tesla Inc.'},
            {'symbol': 'NVDA', 'name': 'NVIDIA Corporation'},
            {'symbol': '^IXIC', 'name': 'NASDAQ Composite'},
            {'symbol': '^GSPC', 'name': 'S&P 500'},
            {'symbol': '^DJI', 'name': 'Dow Jones Industrial Average'},
        ]
        
        for stock_data in stocks:
            Stock.objects.get_or_create(**stock_data)
        
        self.stdout.write(self.style.SUCCESS('Successfully populated stocks')) 