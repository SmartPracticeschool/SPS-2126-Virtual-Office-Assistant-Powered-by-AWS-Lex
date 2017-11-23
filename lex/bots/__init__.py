class BaseBot(object):
    def on_fulfilled(self):
        pass

    def on_failed(self):
        pass

    def on_transition_in(self):
        pass

    def on_transition_out(self):
        pass

    def on_cancel(self):
        pass

    def on_misunderstood(self):
        pass

    def register(self):
        print "{}: Bot Registered Successfully".format(self.bot_name)
