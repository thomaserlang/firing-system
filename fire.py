import constants
import logging
from decorators import new_cursor
import copy
import time

stop = False

def fire(group_id):
    ports = get_group_ports(group_id)
    timelapse = generate_timelapse(ports)
    try:
        import smbus
        bus = smbus.SMBus(1)
    except ImportError:
        bus = None
    reset_chips(bus)
    try:
        try:
            for t in timelapse:
                for d in t:
                    if stop:
                        return
                    logging.info(d)
                    if bus:
                        bus.write_byte_data(
                            d['address'],
                            d['bank'],            
                            int(''.join(d['data']), 2),
                        )
                time.sleep(1)
        except:
            logging.exception('timelapse failed')    
    finally:
        reset_chips(bus)

def reset_chips(bus):
    if not bus:
        return
    for i in range(0, constants.CHIP_COUNT):
        bus.write_byte_data(0x20+i, 0x00, 255)
        bus.write_byte_data(0x20+i, 0x01, 255)

def get_group_ports(group_id):
    with new_cursor() as c:
        rows = c.execute(
            'SELECT * FROM ports WHERE group_id=?',
            (group_id,)
        ).fetchall()
        data = []
        for row in rows:
            data.append({
                'port': row['port'],
                'connection': row['connection'],
                'enabled': True if row['enabled'] == 'Y' else False,
                'delay': row['delay'],
            })
        return data

def generate_chip_data():
    chip_data = []
    for i in range(0, constants.CHIP_COUNT):
        for k in range(0, 2):
            chip_data.append({
                'address': 0x20 + i,
                'bank': 0x00 + k,
                'data': ['1']*8,
            })
    return chip_data

def generate_timelapse(ports):
    chip_data = generate_chip_data()
    timelapse = []
    for a in range(0, max(ports, key=lambda x:x['delay'])['delay']+1):
        c_d = copy.deepcopy(chip_data)
        timelapse.append(c_d)
        for d in ports:
            if a != d['delay']:
                continue
            if not d['enabled']:
                continue
            chip = int((((d['port']-1)*constants.CONNECTIONS_PER_PORT)) / \
                constants.CONNECTIONS_PER_CHIP)
            _b = ((d['port'] - (chip * constants.CONNECTIONS_PER_PORT))) * \
                constants.CONNECTIONS_PER_PORT
            bank = int((_b-1)/constants.CONNECTIONS_PER_CHIP_BANK)
            o = c_d[(chip*2)+bank]
            pos = d['connection']
            if not d['port'] % 2:
                pos += 4
            o['data'][constants.CONNECTIONS_PER_CHIP_BANK-pos] = '0'
    return timelapse