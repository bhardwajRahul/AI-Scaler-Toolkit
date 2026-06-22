---
type: overview
title: Wiki Index
created: 2026-04-29
updated: 2026-04-29
tags: [index]
related: []
sources: ["inference_manual.html"]
---
# Wiki Index

## Overview

*   [[trusta-ast-overview]] — TRUSTA-AST 整體概覽：高性能 LLM 推理服務後端的核心介紹

## Entities

*   [[trusta-ast-inference-service]] — High-performance LLM inference server core component.
*   [[model-manager]] — Singleton coordinator for model lifecycle and IPC.
*   [[worker-process]] — Isolated subprocess for model inference and memory management.

## Concepts

*   [[multi-process-isolation]] — Architectural pattern separating API and inference for stability.
*   [[qwen3-5-inference-optimization]] — Specific parameter overrides for Qwen3.5 model stability.
*   [[inference-engine-comparison]] — Comparison of Transformers, vLLM, and llama-server engines.
*   [[openai-api-compatibility]] — Adherence to OpenAI standard for chat endpoints.
*   [[model-aware-parameter-adjustment]] — Logic for automatically tuning parameters based on model type.
*   [[kv-cache-cleanup]] — Mechanism to free memory without unloading models.
*   [[gpu-offload-mechanism]] — **DRAM/SSD offload 機制，大幅減少 GPU 依賴與成本，整合 fine-tuning 能力**

## Sources

*   [[inference_manual]] — Trusta AST Inference Service Manual.

## Queries

## Comparisons

*   [[legacy-vs-openai-api]] — Migration guide from legacy endpoints to OpenAI standard.
*   [[trusta-ast-vs-market-solutions]] — **深度對比 Trusta AST 與 Ollama、LM Studio、vLLM，突顯 offload 機制和 fine-tuning 整合優勢**

## Synthesis

## Methodology
