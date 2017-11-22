from lex.bots import BaseBot


class PollexyEmergencyBot(BaseBot):
    def __init__(self, lexbot):
        self.bot_name = 'PollexyEmergencyBot'
        self.lexbot = lexbot
        super(PollexyEmergencyBot, self).__init__()

    def on_fulfilled(self, last_response):
        print 'All Done!'
        super(PollexyEmergencyBot, self).on_fulfilled(last_response)

    def on_failed(self, last_response):
        print "No help will be provided."
        super(PollexyEmergencyBot, self).on_failed(last_response)

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
        super(PollexyEmergencyBot, self).register()
