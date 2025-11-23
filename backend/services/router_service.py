from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.config.settings import RouterRule, Settings, get_settings


@dataclass
class RouterDecision:
    rule: RouterRule
    strategy: str
    chain: str


class RouterService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.rules = self.settings.router_rules

    def route(self, question: str) -> RouterDecision:
        normalized = question.lower()
        for rule in self.rules:
            if any(keyword.lower() in normalized for keyword in rule.keywords):
                return RouterDecision(rule=rule, strategy=rule.strategy, chain=rule.chain)
        default_rule = RouterRule(name="default", keywords=[], strategy=self.settings.retrieval.strategy, chain="standard")
        return RouterDecision(rule=default_rule, strategy=default_rule.strategy, chain=default_rule.chain)

    def should_route(self, chain_type: str | None, requested_strategy: str | None) -> bool:
        if chain_type and chain_type.lower() == "router":
            return True
        if requested_strategy and requested_strategy.lower() == "router":
            return True
        return self.settings.retrieval.router_enabled
