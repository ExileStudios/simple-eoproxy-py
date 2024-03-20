# Example Manager usage
def handle(proxy, packet):
    direction = packet.get_char()
    player_id = packet.get_short()
    npc_index = packet.get_short()
    unk1 = packet.get_short()
    damage = packet.get_int()
    unk2 = packet.get_char()

    item = {
        'id': packet.get_short(),
        'power': packet.get_char(),
        'accuracy': packet.get_char(),
        'dexterity': packet.get_char(),
        'defense': packet.get_char(),
        'vitality': packet.get_char(),
        'aura': packet.get_char(),
        'amount': packet.get_three()
    }

    drop_index = packet.get_short()

    coords = {
        'x': packet.get_char(),
        'y': packet.get_char()
    }

    proxy.server.game_manager.item_manager.add_ground_item({
        'index': drop_index,
        'coords': coords,
        'item': item
    })
    
    all_items = proxy.server.game_manager.item_manager.get_ground_items()
    print(f"Ground Items: {all_items}")

    return {
        'player_id': player_id,
        'direction': direction,
        'npc_index': npc_index,
        'unk1': unk1,
        'damage': damage,
        'unk2': unk2,
        'item': item,
        'drop_index': drop_index,
        'coords': coords
    }

