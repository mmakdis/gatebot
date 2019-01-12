from setuptools import setup

setup(
    name="GateBot",
    version="0.2.0",
    description="A gate bot for your Telegram groups",
    author="Mario",
    author_email="mario@dizaztor.com",
    packages=["GateBot"],
    install_requires=["feedparser", "redis", "python-telegram-bot"]
)
