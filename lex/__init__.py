#!/usr/bin/python
import yaml
import boto3
import os
import time
import pprint
from botocore.exceptions import ClientError


class LexIntentManager:
    def __init__(self, **kwargs):
        self.client = boto3.client('lex-models')
        self.config_path = kwargs.get('ConfigPath')

    def load(self):
        intents = {}
        for f in os.listdir(self.config_path):
            config_file = os.path.join(self.config_path, f)
            if not config_file.endswith('yaml') \
               and not config_file.endswith('yml'):
                continue
            with open(config_file, 'r') as stream:
                intents.update(yaml.load(stream))
            return intents

    def get_intent(self, intentName, version):
        try:
            i = self.client.get_intent(name=intentName, version=version)
            return i

        except ClientError as e:
            if e.response and \
               e.response['Error']['Code'] == 'NotFoundException':
                return None
            else:
                raise

    def create_version(self, intent):
        current_intent = self.get_intent(
            intent['name'],
            '$LATEST'
        )
        if current_intent:
            current_intent['checksum'] = current_intent['checksum']
        print 'Creating new version of intent: {}'.format(intent['name'])
        resp = self.client.create_intent_version(
            name=intent['name'],
            checksum=intent['checksum']
        )
        intent['version'] = str(resp['version'])
        print 'Intent version = {}'.format(intent['version'])
        return intent

    def upsert(self, intent):
        args = {}
        for l in intent.keys():
            args[l] = intent[l]
        print 'Upserting intent: {}'.format(intent['name'])
        current_intent = self.get_intent(
            intent['name'],
            '$LATEST'

        )
        if current_intent:
            args['checksum'] = current_intent['checksum']
        return self.client.put_intent(**args)


class LexBotManager:
    def __init__(self, **kwargs):
        self.client = boto3.client('lex-models')
        self.config_path = kwargs.get('ConfigPath')
        pass

    def get_alias(self, botName, aliasName):
        try:
            print 'get_alias {}:{}'.format(botName, aliasName)
            resp = self.client.get_bot_alias(
                name=aliasName,
                botName=botName
            )
            if resp:
                print 'get_alias checksum = {}'.format(resp['checksum'])
                return resp
        except ClientError as e:
            if e.response and \
               e.response['Error']['Code'] == 'NotFoundException':
                return None
            else:
                raise

    def get_bot(self, **kwargs):
        self.name = kwargs.get('Name')
        self.versionOrAlias = kwargs.get('VersionOrAlias', '$LATEST')
        print 'Getting bot {}:{}'.format(self.name, self.versionOrAlias)
        try:
            client = boto3.client('lex-models')
            resp = client.get_bot(
                name=self.name,
                versionOrAlias=self.versionOrAlias
            )
            if resp:
                print 'get_bot checksum = {}'.format(resp['checksum'])
                return resp
        except ClientError as e:
            if e.response and \
               e.response['Error']['Code'] == 'NotFoundException':
                return None
            else:
                raise

    def load_bots(self):
        bots = {}
        for f in os.listdir(self.config_path):
            config_file = os.path.join(self.config_path, f)
            if not config_file.endswith('yaml') \
               and not config_file.endswith('yml'):
                continue
            with open(config_file, 'r') as stream:
                bots.update(yaml.load(stream))
            return bots

    def upsert(self, bot):
        args = {}
        for l in bot.keys():
            args[l] = bot[l]
        print 'Creating bot: {}'.format(bot['name'])
        current_bot = self.get_bot(
            Name=bot['name']
        )
        if current_bot:
            args['checksum'] = current_bot['checksum']
        resp = self.client.put_bot(**args)
        while resp['status'] == 'BUILDING':
            print 'Bot is building . . .'
            time.sleep(10)
            resp = self.get_bot(Name=bot['name'])
        print 'Status: {}'.format(resp['status'])
        if resp['status'] == 'FAILED':
            pprint.pprint(resp)
        return resp['status'], bot

    def create_version(self, bot):
        current_bot = self.get_bot(
            Name=bot['name']
        )
        if current_bot:
            bot['checksum'] = current_bot['checksum']
        print 'Creating new version'
        resp = self.client.create_bot_version(
            name=bot['name'],
            checksum=bot['checksum']
        )
        bot['version'] = str(resp['version'])
        print 'Version = {}'.format(bot['version'])
        return bot

    def update_alias(self, bot, **kwargs):
        alias = kwargs.get('Alias', 'LATEST')
        print 'Updating alias {} for bot {}:{}' \
              .format(alias, bot['name'], bot['version'])
        current_bot = self.get_alias(bot['name'], alias)
        resp = {}
        if current_bot:
            print 'Alias exists . . . updating.'
            print 'name={}, version={}, checksum={}' \
                  .format(alias,
                          current_bot['botVersion'],
                          current_bot['checksum'])
            resp = self.client.put_bot_alias(
                checksum=current_bot['checksum'],
                name=alias,
                botName=current_bot['botName'],
                botVersion=current_bot['botVersion']
            )
        else:
            print 'Alias does NOT exist . . . creating.'
            try:
                resp = self.client.put_bot_alias(
                   name=alias,
                   botName=bot['name'],
                   botVersion=bot['version']
                )
            except Exception as e:
                pprint.pprint(e)
                print "Error creating bot: {}".format(resp)
        print 'Alias updated'


# bm = BotManager()
# client = boto3.client('lex-models')
# bots = bm.load_bots('bots')
# for k in bots.keys():
#    bot = bots[k]
#    bot = bm.upsert(bot)
#    bot = bm.create_version(bot)
#    bot = bm.update_alias(bot, Version='$LATEST')
