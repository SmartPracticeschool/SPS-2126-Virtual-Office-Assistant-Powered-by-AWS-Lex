import pprint
class Test():
    def ThisWorks(self):
        print 'THIS WORKED!'

    def loadModules(self):
        import os
        modules = {}
        # check subfolders
        lst = os.listdir("modules")
        for d in lst:
            if d == '__init__.py':
                continue
            modules[d] = __import__("modules." + d, fromlist=["*"])
        pprint.pprint(modules)
        return modules
