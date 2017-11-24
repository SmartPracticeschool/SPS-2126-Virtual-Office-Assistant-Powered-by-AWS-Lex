from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
        name='Amazon Pollexy Client',
        version='1.5.1',
        packages=['cli', 'input', 'scheduler', 'helpers', 'face', 'cache',
                  'speaker', 'tests', 'time_window', 'lambda_functions',
                  'locator', 'person', 'messages', 'lex'],
        py_modules=['scheduler.scheduler', 'cache.cache_manager',
                    'helpers.speech', 'speaker.speaker', 'messages',
                    'cli.pollexy', 'locator.locator', 'person.person',
                    'messages.message',
                    'messages.message_manager',
                    'face.face',
                    'time_window'],
        install_requires=requirements,
        entry_points={
            'console_scripts': ['pollexy=cli.pollexy:cli']
        }
)
