"""Iteration9 Gemini-only compute regression using isolated creator fixture over real /compute/runs flow."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parent))

from compute_catalog import MAX_OUTPUT, TARIFF_VERSION, cost_units
from test_compute_supplemental_iteration8 import (
    BASE_URL,
    UNIT,
    _poll_run,
)

pytest_plugins = ['test_compute_supplemental_iteration8']


# compute runner regression: verify both Gemini mappings complete with metered usage and consistent charging.
def test_gemini_creator_fixture_full_run_regression_iteration9(isolated_creator_fixture, mongo_db, api_client):
    mint = isolated_creator_fixture["mint"]
    owner_headers = isolated_creator_fixture["owner_headers"]
    models = ["gemini-3-flash-preview", "gemini-2.5-pro"]

    results = []

    for model_id in models:
        mongo_db.agents.update_one(
            {"token": mint},
            {
                "$set": {
                    "profile.model_id": model_id,
                    "profile.mission": "Berikan ringkasan riset singkat berbasis data konteks.",
                    "profile.instructions": "Instruksi privat iteration9 untuk verifikasi regresi Gemini.",
                }
            },
        )
        mongo_db.compute_accounts.update_one(
            {"token": mint},
            {
                "$set": {
                    "active_run": None,
                    "paused": False,
                    "day_runs": 0,
                    "day_spent": 0,
                    "balance": 300 * UNIT,
                    "reserved": 0,
                    "spent": 0,
                    "funded": 300 * UNIT,
                    "per_run_limit": 100 * UNIT,
                    "daily_limit": 300 * UNIT,
                }
            },
        )

        request_id = f"it9-gem-{model_id.replace('.', '-').replace('_', '-')[:20]}-{uuid.uuid4().hex[:10]}"
        create = api_client.post(
            f"{BASE_URL}/api/tokens/{mint}/compute/runs",
            headers=owner_headers,
            json={"request_id": request_id},
        )
        assert create.status_code == 202, f"Run create failed for {model_id}: {create.status_code} {create.text}"
        run_id = create.json()["id"]

        terminal = _poll_run(api_client, mint, run_id, timeout_sec=220)
        assert terminal is not None, f"No terminal response for {model_id}"
        assert terminal.get("status") == "completed", (
            f"Gemini run must complete for {model_id}. "
            f"Got status={terminal.get('status')} error={terminal.get('error')}"
        )

        usage = terminal.get("usage") or {}
        input_tokens = int(usage.get("input_tokens", 0))
        output_tokens = int(usage.get("output_tokens", 0))
        total_tokens = int(usage.get("total_tokens", 0))
        finish_reason = (usage.get("finish_reason") or "").strip()

        assert (terminal.get("output") or "").strip(), f"Empty output for {model_id}"
        assert input_tokens > 0, f"input_tokens not positive for {model_id}"
        assert output_tokens > 0, f"output_tokens not positive for {model_id}"
        assert total_tokens > 0, f"total_tokens not positive for {model_id}"
        assert finish_reason, f"finish_reason missing for {model_id}"
        assert output_tokens <= MAX_OUTPUT, f"output_tokens exceeded cap for {model_id}: {output_tokens} > {MAX_OUTPUT}"

        run_doc = mongo_db.compute_runs.find_one({"token": mint, "id": run_id}, {"_id": 0})
        assert run_doc is not None
        assert run_doc.get("tariff_version") == TARIFF_VERSION

        expected_cost = int(cost_units(model_id, input_tokens, output_tokens))
        assert int(run_doc.get("charged", -1)) == expected_cost, (
            f"charged mismatch for {model_id}: charged={run_doc.get('charged')} expected={expected_cost}"
        )
        assert expected_cost <= int(run_doc.get("reserved", -1))

        acc = mongo_db.compute_accounts.find_one({"token": mint}, {"_id": 0})
        assert acc is not None
        funded = int(acc.get("funded", 0))
        balance = int(acc.get("balance", 0))
        reserved = int(acc.get("reserved", 0))
        spent = int(acc.get("spent", 0))
        assert funded == balance + reserved + spent, (
            f"funding invariant broken for {model_id}: "
            f"funded={funded} balance={balance} reserved={reserved} spent={spent}"
        )

        results.append(
            {
                "model_id": model_id,
                "run_id": run_id,
                "terminal": terminal.get("status"),
                "finish_reason": finish_reason,
                "truncated": finish_reason.lower() in {"length", "max_tokens"} or output_tokens >= MAX_OUTPUT,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                },
                "charged": int(run_doc.get("charged", 0)),
                "reserved": int(run_doc.get("reserved", 0)),
                "tariff_version": run_doc.get("tariff_version"),
                "funded_balance_reserved_spent": {
                    "funded": funded,
                    "balance": balance,
                    "reserved": reserved,
                    "spent": spent,
                },
            }
        )

    with open("/app/test_reports/iteration9_gemini_results.json", "w", encoding="utf-8") as f:
        json.dump({"results": results}, f, indent=2, ensure_ascii=False)

    assert len(results) == 2
    assert {r["model_id"] for r in results} == {"gemini-3-flash-preview", "gemini-2.5-pro"}
