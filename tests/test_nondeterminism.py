"""Tests for ISS-017: sampling config schema validation and nondeterminism characterisation.

Covers:
- ExperimentConfig validates out-of-range temperature, top_p, top_k, seed
- characterise_nondeterminism script exists and is importable
- reports/nondeterminism.md report file exists with required sections
- Core helper functions (_tokenise, _first_diverging_token) behave correctly
- run_characterisation logic works end-to-end via an in-process mock
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from codeagent.schemas import ExperimentConfig

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "characterise_nondeterminism.py"
REPORT_PATH = REPO_ROOT / "reports" / "nondeterminism.md"


# ---------------------------------------------------------------------------
# Helper: load the script as a module without executing main()
# ---------------------------------------------------------------------------


def _load_script() -> ModuleType:
    """Import characterise_nondeterminism.py as a module."""
    spec = importlib.util.spec_from_file_location("characterise_nondeterminism", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# Schema validation — ExperimentConfig sampling fields
# ---------------------------------------------------------------------------


BASE_CONFIG = {
    "experiment_id": "test-exp",
    "model_name": "mock-model",
}


class TestSamplingSchemaValidation:
    """Out-of-range values must be rejected; in-range values must be accepted."""

    # temperature -----------------------------------------------------------

    def test_temperature_zero_valid(self) -> None:
        cfg = ExperimentConfig(**{**BASE_CONFIG, "temperature": 0.0})
        assert cfg.temperature == 0.0

    def test_temperature_max_valid(self) -> None:
        cfg = ExperimentConfig(**{**BASE_CONFIG, "temperature": 2.0})
        assert cfg.temperature == 2.0

    def test_temperature_negative_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ExperimentConfig(**{**BASE_CONFIG, "temperature": -0.1})

    def test_temperature_above_two_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ExperimentConfig(**{**BASE_CONFIG, "temperature": 2.001})

    # top_p -----------------------------------------------------------------

    def test_top_p_one_valid(self) -> None:
        cfg = ExperimentConfig(**{**BASE_CONFIG, "top_p": 1.0})
        assert cfg.top_p == 1.0

    def test_top_p_small_positive_valid(self) -> None:
        cfg = ExperimentConfig(**{**BASE_CONFIG, "top_p": 0.01})
        assert cfg.top_p == pytest.approx(0.01)

    def test_top_p_zero_rejected(self) -> None:
        """top_p must be strictly > 0."""
        with pytest.raises(ValidationError):
            ExperimentConfig(**{**BASE_CONFIG, "top_p": 0.0})

    def test_top_p_above_one_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ExperimentConfig(**{**BASE_CONFIG, "top_p": 1.001})

    # top_k -----------------------------------------------------------------

    def test_top_k_disabled_valid(self) -> None:
        """top_k = -1 means disabled; must be accepted."""
        cfg = ExperimentConfig(**{**BASE_CONFIG, "top_k": -1})
        assert cfg.top_k == -1

    def test_top_k_positive_valid(self) -> None:
        cfg = ExperimentConfig(**{**BASE_CONFIG, "top_k": 50})
        assert cfg.top_k == 50

    # seed ------------------------------------------------------------------

    def test_seed_none_valid(self) -> None:
        cfg = ExperimentConfig(**{**BASE_CONFIG, "seed": None})
        assert cfg.seed is None

    def test_seed_integer_valid(self) -> None:
        cfg = ExperimentConfig(**{**BASE_CONFIG, "seed": 42})
        assert cfg.seed == 42

    def test_seed_zero_valid(self) -> None:
        cfg = ExperimentConfig(**{**BASE_CONFIG, "seed": 0})
        assert cfg.seed == 0


# ---------------------------------------------------------------------------
# Script existence and importability
# ---------------------------------------------------------------------------


class TestScriptExists:
    def test_script_file_exists(self) -> None:
        assert SCRIPT_PATH.exists(), f"Script not found: {SCRIPT_PATH}"

    def test_script_is_importable(self) -> None:
        mod = _load_script()
        assert hasattr(mod, "run_characterisation")
        assert hasattr(mod, "main")
        assert hasattr(mod, "_first_diverging_token")
        assert hasattr(mod, "_tokenise")
        assert hasattr(mod, "_build_report")


# ---------------------------------------------------------------------------
# Helper function unit tests
# ---------------------------------------------------------------------------


class TestHelpers:
    def _get_helpers(self):
        mod = _load_script()
        return mod._tokenise, mod._first_diverging_token

    def test_tokenise_basic(self) -> None:
        tokenise, _ = self._get_helpers()
        assert tokenise("hello world") == ["hello", "world"]

    def test_tokenise_empty(self) -> None:
        tokenise, _ = self._get_helpers()
        assert tokenise("") == []

    def test_first_diverging_token_all_identical(self) -> None:
        _, first_div = self._get_helpers()
        responses = ["foo bar baz"] * 5
        assert first_div(responses) is None

    def test_first_diverging_token_diverge_at_zero(self) -> None:
        _, first_div = self._get_helpers()
        responses = ["apple orange", "banana orange"]
        assert first_div(responses) == 0

    def test_first_diverging_token_diverge_at_one(self) -> None:
        _, first_div = self._get_helpers()
        responses = ["same apple", "same banana"]
        assert first_div(responses) == 1

    def test_first_diverging_token_different_lengths(self) -> None:
        _, first_div = self._get_helpers()
        responses = ["foo bar", "foo"]
        # Second response is shorter; at index 1 it has <END> vs "bar"
        assert first_div(responses) == 1

    def test_first_diverging_token_empty_list(self) -> None:
        _, first_div = self._get_helpers()
        assert first_div([]) is None

    def test_first_diverging_token_single_response(self) -> None:
        _, first_div = self._get_helpers()
        assert first_div(["only one"]) is None


# ---------------------------------------------------------------------------
# Report file
# ---------------------------------------------------------------------------


class TestReportFile:
    REQUIRED_SECTIONS = [
        "# Nondeterminism Characterisation Report",
        "## Experiment Setup",
        "## Results",
        "## Analysis",
        "## Conclusions",
        "Recommended repeats",
    ]

    def test_report_exists(self) -> None:
        assert REPORT_PATH.exists(), f"Report not found: {REPORT_PATH}"

    def test_report_contains_required_sections(self) -> None:
        content = REPORT_PATH.read_text(encoding="utf-8")
        for section in self.REQUIRED_SECTIONS:
            assert section in content, f"Missing section: {section!r}"

    def test_report_has_results_table(self) -> None:
        content = REPORT_PATH.read_text(encoding="utf-8")
        # Must have the results table header
        assert "Distinct outputs" in content or "distinct_count" in content or "distinct" in content

    def test_report_mentions_temperature(self) -> None:
        content = REPORT_PATH.read_text(encoding="utf-8")
        assert "temperature" in content.lower()

    def test_report_mentions_repeats_recommendation(self) -> None:
        content = REPORT_PATH.read_text(encoding="utf-8")
        # Should discuss how many repeats are needed
        assert "repeat" in content.lower() or "run" in content.lower()


# ---------------------------------------------------------------------------
# run_characterisation — integration test via in-process mock
# ---------------------------------------------------------------------------


class TestRunCharacterisation:
    """Test the core experiment loop using an in-process mock HTTP client."""

    def _make_mock_response(self, text: str) -> MagicMock:
        """Build a mock httpx response returning *text* as the assistant message."""
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        return resp

    async def test_all_identical_responses(self) -> None:
        """When the server always returns the same text, distinct count should be 1."""
        mod = _load_script()
        fixed_text = "Mock response: Processed query regarding 'Write a Python function'."
        mock_response = self._make_mock_response(fixed_text)

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)

            results = await mod.run_characterisation(
                base_url="http://mock:9999",
                prompt="Write a Python function",
                model="mock-model",
                n=5,
                chosen_temperature=0.8,
                seed=42,
            )

        assert results["n"] == 5
        greedy = results["conditions"]["greedy"]
        sampled = results["conditions"]["sampled"]
        assert greedy["distinct_count"] == 1
        assert sampled["distinct_count"] == 1
        assert greedy["first_diverging_token_idx"] is None
        assert sampled["first_diverging_token_idx"] is None

    async def test_diverging_responses_detected(self) -> None:
        """When responses alternate between two texts, distinct count should be 2."""
        mod = _load_script()
        texts = ["Response A is unique", "Response B is different"]

        call_count = 0

        async def _side_effect(*args, **kwargs):
            nonlocal call_count
            text = texts[call_count % 2]
            call_count += 1
            return self._make_mock_response(text)

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = _side_effect

            results = await mod.run_characterisation(
                base_url="http://mock:9999",
                prompt="Hello",
                model="mock-model",
                n=4,
                chosen_temperature=1.0,
                seed=None,
            )

        # Both conditions see alternating responses → 2 distinct outputs each
        assert results["conditions"]["greedy"]["distinct_count"] == 2
        assert results["conditions"]["sampled"]["distinct_count"] == 2

    async def test_result_structure(self) -> None:
        """Results dict has the expected top-level keys and nested structure."""
        mod = _load_script()
        mock_response = self._make_mock_response("hello world")

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)

            results = await mod.run_characterisation(
                base_url="http://mock:9999",
                prompt="test",
                model="m",
                n=2,
                chosen_temperature=0.5,
                seed=1,
            )

        assert set(results.keys()) >= {"prompt", "model", "n", "seed", "conditions"}
        assert set(results["conditions"].keys()) == {"greedy", "sampled"}
        for cond in ("greedy", "sampled"):
            c = results["conditions"][cond]
            assert "distinct_count" in c
            assert "first_diverging_token_idx" in c
            assert "responses" in c
            assert len(c["responses"]) == 2


# ---------------------------------------------------------------------------
# CLI argument validation — _parse_args
# ---------------------------------------------------------------------------


class TestCLIParsing:
    def test_default_args(self) -> None:
        mod = _load_script()
        args = mod._parse_args([])
        assert args.n == 20
        assert args.temperature == 0.8
        assert args.seed is None
        assert "127.0.0.1" in args.base_url

    def test_custom_args(self) -> None:
        mod = _load_script()
        args = mod._parse_args(["--n", "5", "--temperature", "1.2", "--seed", "99"])
        assert args.n == 5
        assert args.temperature == pytest.approx(1.2)
        assert args.seed == 99

    def test_main_rejects_bad_temperature(self) -> None:
        mod = _load_script()
        # main() should return 1 without calling run_characterisation
        rc = mod.main(["--temperature", "9.9", "--n", "1"])
        assert rc == 1

    def test_main_rejects_zero_n(self) -> None:
        mod = _load_script()
        rc = mod.main(["--n", "0"])
        assert rc == 1
