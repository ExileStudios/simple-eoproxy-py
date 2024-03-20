

from managers.ItemManager import ItemManager

class GameManager:
    def __init__(self, proxy):
        self.proxy = proxy
        self.item_manager = ItemManager(proxy)
      
    def item_manager(self):
        return self.item_manager
    
    def shutdown(self):
        self.item_manager = None
        self.proxy = None
        self = None