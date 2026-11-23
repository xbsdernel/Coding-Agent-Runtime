"""Tests for model server launcher, mock server, and probe verification."""

from __future__ import annotations

import json
import sys
import threading
import time
from http.server import HTTPServer
from pathlib import Path

# Add scripts directory to sys.path
scripts_dir = str(Path(__file__).resolve().parent.parent / "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from mock_server import MockOpenAIHandler  # noqa: E402
from probe_server import probe_server  # noqa: E402


def test_serve_script_exists_and_executable():
    """Verify scripts/serve.sh exists and contains expected flags."""
    root = Path(__file__).resolve().parent.parent
    serve_sh = root / "scripts" / "serve.sh"
    assert serve_sh.is_file(), f"serve.sh not found at {serve_sh}"

    content = serve_sh.read_text(encoding="utf-8")
    assert "--model" in content
    assert "--max-model-len" in content
    assert "--enable-prefix-caching" in content
    assert "GPU_MEMORY_UTILIZATION" in content
    assert "TENSOR_PARALLEL_SIZE" in content
    assert "vllm" in content
    assert "sglang" in content
    assert "mock" in content


def test_mock_server_and_probe_report(tmp_path: Path):
    """Start mock server on an ephemeral port, run probe_server, and verify artifacts."""
    port = 8912
    server = HTTPServer(("127.0.0.1", port), MockOpenAIHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    time.sleep(0.1)  # allow server thread to bind

    try:
        report_dir = tmp_path / "probe_report"
        success = probe_server(f"http://127.0.0.1:{port}", report_dir)
        assert success is True

        # Verify artifacts
        req_nonstream = report_dir / "request_nonstream.json"
        resp_nonstream = report_dir / "response_nonstream.json"
        req_stream = report_dir / "request_stream.json"
        resp_stream = report_dir / "response_stream.txt"
        startup_log = report_dir / "startup.log"

        assert req_nonstream.is_file()
        assert resp_nonstream.is_file()
        assert req_stream.is_file()
        assert resp_stream.is_file()
        assert startup_log.is_file()

        # Check non-streaming payload
        resp_data = json.loads(resp_nonstream.read_text(encoding="utf-8"))
        assert resp_data["object"] == "chat.completion"
        assert len(resp_data["choices"]) > 0
        assert resp_data["choices"][0]["message"]["role"] == "assistant"
        assert "usage" in resp_data
        assert "prompt_tokens_details" in resp_data["usage"]

        # Check streaming payload
        stream_content = resp_stream.read_text(encoding="utf-8")
        assert "data: " in stream_content
        assert "data: [DONE]" in stream_content
    finally:
        server.shutdown()
        server.server_close()
