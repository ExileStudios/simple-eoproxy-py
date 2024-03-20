class ItemManager:
    def __init__(self, proxy):
        self.proxy = proxy
        self.ground_items = []

    def get_ground_items(self):
        return self.ground_items

    def set_ground_items(self, items):
        self.ground_items = items

    def add_ground_item(self, ground_item):
        self.ground_items.append(ground_item)

    def get_ground_item(self, index):
        for item in self.ground_items:
            if item.index == index:
                return item
        return None

    def remove_ground_item(self, index):
        self.ground_items = [item for item in self.ground_items if item.index != index]
