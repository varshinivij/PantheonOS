from .agent import Agent


class Chat:
    def __init__(self, agent: Agent):
        self.agent = agent
        self.history = []

    def run(self, message: str):
        pass
