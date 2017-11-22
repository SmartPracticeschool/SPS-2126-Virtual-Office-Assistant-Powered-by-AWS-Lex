from lex.bots import BaseBot


class PollexySetAlarmBot(BaseBot):
    def __init__(self, lexbot):
        self.bot_name = 'SetAlarmBot'
        self.lexbot = lexbot
        super(PollexySetAlarmBot, self).__init__()

    def on_fulfilled(self):
        t = self.lexbot.slots['TimeSlot']
        self.lexbot.speak(
            Message='Your alarm has been scheduled for {}.'.format(t))
        super(PollexySetAlarmBot, self).on_fulfilled(1)

    def on_failed(self, last_response):
        print "No help will be provided."
        super(PollexySetAlarmBot, self).on_failed(last_response)

    def on_transition_in(self):
        pass

    def on_transition_out(self):
        pass

    def on_cancel(self):
        pass

    def on_needs_intent(self):
        pass

    def on_response(self, text, last_response):
        pass

    def register(self):
        super(PollexySetAlarmBot, self).register()
