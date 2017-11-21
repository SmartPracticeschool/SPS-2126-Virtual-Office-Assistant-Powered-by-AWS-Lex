import yaml
import boto3
import os
import time
client = boto3.client('lex-models')
for f in os.listdir('slots'):
    config_file = os.path.join('slots', f)
    if not config_file.endswith('yaml') and not config_file.endswith('yml'):
        continue
    with open(config_file, 'r') as stream:
        slots = yaml.load(stream)
    for k in slots.keys():
        if k == 'checksum':
            continue
        slot = slots[k]
        args = {}
        for l in slot.keys():
            args[l] = slots[k][l]
        if 'checksum' in slots and k in slots['checksum']:
            args['checksum'] = slots['checksum'][k]
        print 'Creating/updating slot: {}'.format(slot['name'])
        resp = client.put_slot_type(**args)
        if 'checksum' not in slots:
            slots['checksum'] = {}
        slots['checksum'][k] = str(resp['checksum'])
        with open(config_file, 'w') as yaml_file:
            yaml_file.write(yaml.dump(slots, default_flow_style=False))
        print 'Done'
