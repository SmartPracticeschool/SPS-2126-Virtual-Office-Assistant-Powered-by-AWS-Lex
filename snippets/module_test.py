def loadModule(name):
    # check subfolders
    module = __import__('modules.'+name, fromlist=["*"])
    return module


m = loadModule('mod1')
c = getattr(m, 'Test')
i = c()
i.ThisWorks()
