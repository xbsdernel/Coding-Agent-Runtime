#!/usr/bin/env bash
# scripts/serve.sh — Launch OpenAI-compatible model server (vLLM, SGLang, or Mock)
# Configured with prefix caching, context length, and tensor parallelism.

set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen2.5-Coder-7B-Instruct}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"
GPU_MEMORY_UTILIZATION="${GPU_MEMORY_UTILIZATION:-0.90}"
TENSOR_PARALLEL_SIZE="${TENSOR_PARALLEL_SIZE:-1}"
ENGINE="${ENGINE:-vllm}"
QUANTIZATION="${QUANTIZATION:-}"
ENABLE_PREFIX_CACHING="${ENABLE_PREFIX_CACHING:-true}"
LOG_FILE="${LOG_FILE:-reports/probe_report/startup.log}"

mkdir -p "$(dirname "$LOG_FILE")"

# Parse optional command-line overrides
while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --max-model-len)
            MAX_MODEL_LEN="$2"
            shift 2
            ;;
        --engine)
            ENGINE="$2"
            shift 2
            ;;
        --mock)
            ENGINE="mock"
            shift
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 1
            ;;
    esac
done

echo "==========================================================" | tee "$LOG_FILE"
echo "Starting Model Server" | tee -a "$LOG_FILE"
echo "  Engine:                  $ENGINE" | tee -a "$LOG_FILE"
echo "  Model:                   $MODEL" | tee -a "$LOG_FILE"
echo "  Host:                    $HOST" | tee -a "$LOG_FILE"
echo "  Port:                    $PORT" | tee -a "$LOG_FILE"
echo "  Max Context Length:      $MAX_MODEL_LEN" | tee -a "$LOG_FILE"
echo "  GPU Memory Utilization:  $GPU_MEMORY_UTILIZATION" | tee -a "$LOG_FILE"
echo "  Tensor Parallel Size:    $TENSOR_PARALLEL_SIZE" | tee -a "$LOG_FILE"
echo "  Prefix Caching Enabled:  $ENABLE_PREFIX_CACHING" | tee -a "$LOG_FILE"
echo "==========================================================" | tee -a "$LOG_FILE"

if [[ "$ENGINE" == "mock" ]]; then
    echo "Running in Mock mode (CPU/offline)..." | tee -a "$LOG_FILE"
    exec python scripts/mock_server.py --host "$HOST" --port "$PORT" --model "$MODEL" --context-length "$MAX_MODEL_LEN"
elif [[ "$ENGINE" == "sglang" ]]; then
    ARGS=(
        python -m sglang.launch_server
        --model-path "$MODEL"
        --host "$HOST"
        --port "$PORT"
        --context-length "$MAX_MODEL_LEN"
        --tp-size "$TENSOR_PARALLEL_SIZE"
    )
    if [[ "$ENABLE_PREFIX_CACHING" == "true" ]]; then
        ARGS+=(--enable-radix-cache)
    fi
    exec "${ARGS[@]}" 2>&1 | tee -a "$LOG_FILE"
else
    # Default to vLLM
    ARGS=(
        python -m vllm.entrypoints.openai.api_server
        --model "$MODEL"
        --host "$HOST"
        --port "$PORT"
        --max-model-len "$MAX_MODEL_LEN"
        --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION"
        --tensor-parallel-size "$TENSOR_PARALLEL_SIZE"
    )
    if [[ "$ENABLE_PREFIX_CACHING" == "true" ]]; then
        ARGS+=(--enable-prefix-caching)
    fi
    if [[ -n "$QUANTIZATION" ]]; then
        ARGS+=(--quantization "$QUANTIZATION")
    fi
    exec "${ARGS[@]}" 2>&1 | tee -a "$LOG_FILE"
fi
