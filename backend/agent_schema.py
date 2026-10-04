"""Shared creator-form validation; independent of route modules."""
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

MODELS = [
    {'id': 'claude-sonnet-4-5', 'name': 'Claude Sonnet 4.5', 'provider': 'Anthropic', 'type': 'Balanced', 'description': 'Strategy, writing, and community communication.', 'context': '200K', 'recommended': True},
    {'id': 'claude-opus-4-5', 'name': 'Claude Opus 4.5', 'provider': 'Anthropic', 'type': 'Reasoning', 'description': 'Complex research and multi-step analysis.', 'context': '200K'},
    {'id': 'claude-haiku-4-5', 'name': 'Claude Haiku 4.5', 'provider': 'Anthropic', 'type': 'Fast', 'description': 'Fast, lightweight community workflows.', 'context': '200K'},
    {'id': 'gpt-5.2', 'name': 'GPT-5.2', 'provider': 'OpenAI', 'type': 'Versatile', 'description': 'Analysis, creative work, and planning.', 'context': '400K'},
    {'id': 'gpt-5-mini', 'name': 'GPT-5 mini', 'provider': 'OpenAI', 'type': 'Efficient', 'description': 'Focused reasoning with a smaller footprint.', 'context': '400K'},
    {'id': 'gemini-3-flash-preview', 'name': 'Gemini 3 Flash', 'provider': 'Google', 'type': 'Fast', 'description': 'Fast multimodal reasoning with a large context.', 'context': '1M'},
    {'id': 'gemini-2.5-pro', 'name': 'Gemini 2.5 Pro', 'provider': 'Google', 'type': 'Research', 'description': 'Long-context research and understanding.', 'context': '1M'},
    {'id': 'deepseek-reasoner', 'name': 'DeepSeek R1', 'provider': 'DeepSeek', 'type': 'Reasoning', 'description': 'Research and considered strategy.', 'context': '128K'},
    {'id': 'qwen3-235b', 'name': 'Qwen3 235B', 'provider': 'Qwen', 'type': 'Open model', 'description': 'Multilingual reasoning and open-model flexibility.', 'context': '128K'},
    {'id': 'mistral-large', 'name': 'Mistral Large', 'provider': 'Mistral', 'type': 'Multilingual', 'description': 'Multilingual communication and structured analysis.', 'context': '128K'},
]
CAPABILITIES = ['observe', 'research', 'think', 'strategy', 'act', 'monitor', 'learn']

class Allocation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    community: int = Field(default=30, ge=0, le=100, strict=True)
    liquidity: int = Field(default=25, ge=0, le=100, strict=True)
    creative: int = Field(default=20, ge=0, le=100, strict=True)
    buyback: int = Field(default=15, ge=0, le=100, strict=True)
    operations: int = Field(default=10, ge=0, le=100, strict=True)

    @model_validator(mode='after')
    def total(self):
        if sum(self.model_dump().values()) != 100:
            raise ValueError('Allocation must add up to 100%.')
        return self

class AgentProfile(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=60)
    role: Literal['Community steward', 'Market analyst', 'Creative director'] = 'Community steward'
    mission: str = Field(min_length=10, max_length=1200)
    model_id: str = 'claude-sonnet-4-5'
    creativity: float = Field(default=0.7, ge=0, le=1)
    risk: Literal['Conservative', 'Balanced', 'Exploratory'] = 'Conservative'
    instructions: str = Field(default='', max_length=4000)
    capabilities: list[str] = Field(default_factory=lambda: CAPABILITIES.copy(), max_length=7)
    allocation: Allocation | None = Field(default=None, exclude=True)

    @model_validator(mode='after')
    def supported(self):
        if self.model_id not in {m['id'] for m in MODELS}:
            raise ValueError('Choose a model from the catalog.')
        if any(c not in CAPABILITIES for c in self.capabilities) or len(set(self.capabilities)) != len(self.capabilities):
            raise ValueError('Choose unique supported capabilities.')
        return self

class PublicAgentProfile(BaseModel):
    """Deliberately excludes the creator's private operating instructions."""
    name: str
    role: str
    mission: str
    model_id: str
    creativity: float
    risk: str
    capabilities: list[str]