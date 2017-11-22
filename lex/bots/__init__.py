class BaseBot(object):
    def on_fulfilled(self, last_response):
        pass

    def on_failed(self, last_response):
        pass

    def on_transition_in(self, last_response):
        pass

    def on_transition_out(self, last_response):
        pass

    def on_cancel(self, last_response):
        pass

    def on_misunderstood(self, last_response):
        pass

    def register(self):
        print "{}: Bot Registered Successfully".format(self.bot_name)
