"""Versioned INTERNAL test tariffs, not a provider invoice or a redeemable balance."""
import math
from fastapi import HTTPException
from agent_schema import MODELS

UNIT = 1_000_000
TARIFF_VERSION = 'internal-test-v1'
MAX_OUTPUT = 1800
MAX_PROMPT_BYTES = 24000
# credits per million input / output tokens. 100 internal CR = 1 reference USD.
RATES = {
    'claude-sonnet-4-5': ('anthropic', 'claude-sonnet-4-5-20250929', 300, 1500),
    'claude-opus-4-5': ('anthropic', 'claude-opus-4-5-20251101', 500, 2500),
    'claude-haiku-4-5': ('anthropic', 'claude-haiku-4-5-20251001', 100, 500),
    'gpt-5.2': ('openai', 'gpt-5.2', 175, 1400),
    'gpt-5-mini': ('openai', 'gpt-5-mini', 25, 200),
    'gemini-3-flash-preview': ('gemini', 'gemini-3-flash-preview', 50, 300),
    'gemini-2.5-pro': ('gemini', 'gemini-2.5-pro', 125, 1000),
}
FREQUENCIES = {'hourly': 1, 'every-6-hours': 6, 'daily': 24, 'weekly': 168}

def catalog():
    return [{**m, 'runnable': m['id'] in RATES,
             'availability': 'Ready' if m['id'] in RATES else 'Provider key required',
             'input_cr_per_million': RATES[m['id']][2] if m['id'] in RATES else None,
             'output_cr_per_million': RATES[m['id']][3] if m['id'] in RATES else None} for m in MODELS]

def cost_units(model, inputs, outputs):
    if model not in RATES:
        raise HTTPException(422, 'Provider model ini belum terhubung. Model tidak akan diganti otomatis.')
    return math.ceil(inputs * RATES[model][2] + outputs * RATES[model][3])

def estimate(model, frequency):
    if frequency not in FREQUENCIES:
        raise HTTPException(422, 'Frekuensi tidak valid.')
    run = cost_units(model, 2500, 800) / UNIT
    maximum = cost_units(model, MAX_PROMPT_BYTES + 256, MAX_OUTPUT) / UNIT
    daily = 24 / FREQUENCIES[frequency]
    return {'model_id': model, 'frequency': frequency, 'per_run': run, 'max_per_run': maximum,
            'daily': round(run * daily, 4), 'weekly': round(run * daily * 7, 4),
            'monthly': round(run * daily * 30, 4), 'runs_per_month': round(daily * 30, 2),
            'input_tokens': 2500, 'output_tokens': 800, 'tool_credits': 0,
            'tariff_version': TARIFF_VERSION, 'unit': 'CR', 'is_estimate': True}