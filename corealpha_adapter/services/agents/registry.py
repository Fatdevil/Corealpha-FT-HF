from typing import Dict, Optional

from .base import IAgent
from .fundamental_agent import FundamentalAgent
from .macro_agent import MacroAgent
from .pm_risk_agent import PMRiskAgent
from .sentiment_agent import SentimentAgent
from .technical_agent import TechnicalAgent


class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, IAgent] = {}
        self.register(SentimentAgent())
        self.register(FundamentalAgent())
        self.register(TechnicalAgent())
        self.register(MacroAgent())
        self.register(PMRiskAgent())

    def register(self, agent: IAgent):
        self._agents[getattr(agent, "name")] = agent

    def get(self, name: str) -> Optional[IAgent]:
        return self._agents.get(name)


_reg = AgentRegistry()


def get_agent_registry() -> AgentRegistry:
    return _reg
