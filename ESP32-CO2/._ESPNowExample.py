import espnow

e = espnow.ESPNow()
packets = []

while True:
    if e:
        packet = e.read()
        packets.append(packet)
        if packet.msg == b'end':
            break

print("packets:", f"length={len(packets)}")
for packet in packets:
    print(packet)
