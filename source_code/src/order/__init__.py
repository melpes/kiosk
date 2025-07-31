"""
주문 관리 모듈
"""

from .menu import Menu, MenuSearchResult

__all__ = ['Menu', 'MenuSearchResult']

# OrderManager는 지연 import
def get_order_manager():
    from .order import OrderManager
    return OrderManager