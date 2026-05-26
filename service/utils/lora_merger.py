import sys
import os
import argparse
import traceback
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LoRA_Merger")


def _read_mem_available_gib() -> int | None:
    """Read available system memory in GiB from /proc/meminfo."""
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as meminfo:
            for line in meminfo:
                if line.startswith("MemAvailable:"):
                    available_kib = int(line.split()[1])
                    available_gib = max(1, available_kib // (1024 * 1024))
                    return available_gib
    except (OSError, ValueError, IndexError):
        return None
    return None


def _resolve_device_map(offload_folder: str | None, requested_device_map: str | None) -> str:
    """Resolve merge device placement.

    With `offload_folder` present, default to CPU merge for stability because
    `device_map="auto"` aggressively fills available GPU memory before using
    CPU/disk, which often OOMs during `merge_and_unload()`.
    """
    if requested_device_map:
        return requested_device_map

    if offload_folder:
        return "cpu"

    return "auto"


def _build_max_memory(device_map: str, offload_folder: str | None) -> dict[int | str, str] | None:
    """Build conservative max_memory only for bounded auto-offload mode."""
    if device_map != "auto" or not offload_folder:
        return None

    max_memory: dict[int | str, str] = {}

    if torch.cuda.is_available():
        max_memory[0] = os.getenv("LORA_MERGE_GPU_MAX_MEMORY", "256MiB")

    cpu_max_memory = os.getenv("LORA_MERGE_CPU_MAX_MEMORY")
    if cpu_max_memory:
        max_memory["cpu"] = cpu_max_memory
    else:
        available_gib = _read_mem_available_gib()
        if available_gib is not None:
            reserved_gib = 4 if available_gib > 8 else 1
            max_memory["cpu"] = f"{max(1, available_gib - reserved_gib)}GiB"

    return max_memory or None


def _normalize_no_split_modules(model) -> None:
    """Normalize nested `_no_split_modules` entries to a flat string list.

    Some MoE models expose nested sets/lists in `_no_split_modules`, which
    causes `accelerate` internals to raise `unhashable type: 'set'` when PEFT
    loads adapters.
    """
    no_split_modules = getattr(model, "_no_split_modules", None)
    if no_split_modules is None:
        return

    flattened: list[str] = []
    for item in no_split_modules:
        if isinstance(item, (set, list, tuple)):
            flattened.extend(str(value) for value in item)
        else:
            flattened.append(str(item))

    model._no_split_modules = flattened

def merge_lora(base_model_path, adapter_path, output_path, offload_folder=None, device_map=None):
    logger.info(f"Loading base model from {base_model_path}")

    resolved_device_map = _resolve_device_map(offload_folder, device_map)
    logger.info(f"Using device_map={resolved_device_map} for LoRA merge")
    
    load_kwargs = {
        "device_map": resolved_device_map,
        "trust_remote_code": True,
        "low_cpu_mem_usage": True,
    }

    if offload_folder:
        logger.info(f"Enabling disk offloading to: {offload_folder}")
        load_kwargs["offload_folder"] = offload_folder
        load_kwargs["offload_state_dict"] = True

    max_memory = _build_max_memory(resolved_device_map, offload_folder)
    if max_memory:
        load_kwargs["max_memory"] = max_memory
        logger.info(f"Using bounded max_memory for merge: {max_memory}")

    if resolved_device_map == "cpu":
        logger.info("LoRA merge is running in CPU mode to avoid GPU OOM during merge_and_unload()")

    try:
        # Load base model
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            **load_kwargs
        )

        _normalize_no_split_modules(base_model)

        logger.info(f"Loading LoRA adapter from {adapter_path}")
        model = PeftModel.from_pretrained(base_model, adapter_path)
        
        logger.info("Merging weights...")
        # merge_and_unload 會將 LoRA 權重合併進 base model 並移除 adapter layers
        # 對於 offload 的模型，accelerate 會自動處理權重的載入與儲存
        model = model.merge_and_unload()
        
        logger.info(f"Saving merged model to {output_path}")
        # max_shard_size="10GB" 確保儲存時自動分片，避免產生單一超大檔案
        if hasattr(model, "to"):
            model = model.to("cpu")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        model.save_pretrained(output_path, safe_serialization=True, max_shard_size="10GB")
        
        # Also save tokenizer
        tokenizer = AutoTokenizer.from_pretrained(base_model_path)
        tokenizer.save_pretrained(output_path)
        
        logger.info("Merge completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during merge: {e}\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge LoRA adapter into base model")
    parser.add_argument("base_model_path", help="Path to the base model")
    parser.add_argument("adapter_path", help="Path to the LoRA adapter")
    parser.add_argument("output_path", help="Path to save the merged model")
    parser.add_argument("--offload", help="Path to offload folder for low memory merging", default=None)
    parser.add_argument(
        "--device-map",
        choices=["auto", "cpu"],
        default=os.getenv("LORA_MERGE_DEVICE_MAP"),
        help="Override merge device placement. Default: cpu when --offload is set, otherwise auto.",
    )
    
    args = parser.parse_args()
    
    merge_lora(
        args.base_model_path,
        args.adapter_path,
        args.output_path,
        args.offload,
        args.device_map,
    )
