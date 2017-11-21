#!/usr/bin/python
import yaml
import boto3
import os
import time
client = boto3.client('lex-models')
for f in os.listdir('intents'):
    config_file = os.path.join('intents', f)
    if not config_file.endswith('yaml') and not config_file.endswith('yml'):
        continue
    with open(config_file, 'r') as stream:
        intents = yaml.load(stream)
    for k in intents.keys():
        if k == 'checksum':
            continue
        intent = intents[k]
        args = {}
        for l in intent.keys():
            args[l] = intent[l]
        if 'checksum' in intents and k in intents['checksum']:
            args['checksum'] = intents['checksum'][k]
        print 'Creating/updating intent: {}'.format(intent['name'])
        resp = client.put_intent(**args)
        if 'checksum' not in intents:
            intents['checksum'] = {}
        intents['checksum'][k] = str(resp['checksum'])
        with open(config_file, 'w') as yaml_file:
            yaml_file.write(yaml.dump(intents, default_flow_style=False))
        print 'Done'
