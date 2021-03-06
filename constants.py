CHIP_COUNT = 4
CONNECTIONS_PER_CHIP = 16
CONNECTIONS_PER_CHIP_BANK = 8
CONNECTIONS_PER_PORT = 4
PORTS_NUM = int((CHIP_COUNT * CONNECTIONS_PER_CHIP) / CONNECTIONS_PER_PORT)
PER_GROUP = 8
PORTS = list(range(1, PORTS_NUM+1))
GROUPED_PORTS = [PORTS[i:i+PER_GROUP] for i in range(0, len(PORTS), PER_GROUP)]
PORT_COLORS = {
    1: '#3137DA',
    2: '#00C841',
    3: '#9A451E',
    4: '#FF4F00',
}
DATABASE_FILE = 'settings.db'
