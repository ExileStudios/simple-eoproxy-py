def filter (proxy, packet):
    emote = packet.get_char()
    # Filter AFK emote
    if emote == 8:
        return False
    return True