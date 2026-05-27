# GitHub AST

GitHub AST 是一個以 FastAPI 為核心的 LLM 後端服務，提供：

- 模型載入 / 卸載
- OpenAI 相容聊天介面
- 推論與串流回應
- 訓練工作啟動與狀態查詢
- 模型下載
- 前端靜態頁面掛載

本文件涵蓋 Linux 與 Windows 兩種平台；初始化快速流程放在最前面，更多細節請往後看。

> Linux 範例路徑：`/home/test/project/AI-Scaler-Toolkit`
>
> Windows 範例路徑：`C:\Users\<user>\project\AI-Scaler-Toolkit`

---

## 1. 第一次初始化快速流程

### Linux（建議先走 CUDA）

```bash
mkdir -p /home/test/project
cd /home/test/project
git clone --recursive <YOUR_GITHUB_REPOSITORY_URL> AI-Scaler-Toolkit
cd AI-Scaler-Toolkit

mkdir -p logs .cache/huggingface runtime_data/inference_offload runtime_data/finetune_output
cp .env.example .env
# 編輯 .env，優先修改 HF_HOME、LOG_DIR、SERVICE_HOST、SERVICE_PORT

TRUSTA_ACCEL=xpu bash deploy/linux/setup_env.sh
bash deploy/linux/run_service.sh
```

啟動成功後，直接用瀏覽器開啟：

- `http://127.0.0.1:8000/`

若要改走 NVIDIA CUDA，將 `TRUSTA_ACCEL=xpu` 改成 `TRUSTA_ACCEL=cuda`。

### Windows（建議先走 XPU）

```powershell
mkdir C:\Users\<user>\project
cd C:\Users\<user>\project
git clone --recursive <YOUR_GITHUB_REPOSITORY_URL> AI-Scaler-Toolkit
cd AI-Scaler-Toolkit

New-Item -ItemType Directory -Force logs, .cache\huggingface, runtime_data\inference_offload, runtime_data\finetune_output
Copy-Item .env.example .env
notepad .env

.\deploy\windows\setup_env.ps1 -Accel xpu
.\deploy\windows\run_service.bat
```

啟動成功後，直接用瀏覽器開啟：

- `http://127.0.0.1:8000/`

若要改走 NVIDIA CUDA，將 `-Accel xpu` 改成 `-Accel cuda`。

> 詳細安裝需求、`.env` 說明、模型載入方式與驗證方式，請看後續章節。

---

## 2. 專案結構

```text
AI-Scaler-Toolkit/
├─ deploy/
│  ├─ linux/
│  │  ├─ run_service.sh
│  │  └─ setup_env.sh
│  ├─ windows/
│  │  ├─ run_service.bat
│  │  └─ setup_env.ps1
│  └─ docker/
├─ docs/
├─ dataset/
├─ service/
│  ├─ app.py
│  ├─ settings.py
│  ├─ pyproject.toml
│  └─ configs/
├─ tests/
├─ Trusta-AST-Frontend/
│  ├─ dist/
│  └─ dist_client/
├─ .env.example
└─ README.md
```

---

## 3. 系統需求

### 基本需求（兩平台共同）

| 工具 | 說明 |
|------|------|
| Git | 含 submodule 支援 |
| Python 3.12+ | 執行服務本體 |
| `uv` | Python 套件 / 環境管理 |
| C/C++ 編譯工具鏈 | 編譯 llama.cpp 時需要 |
| cmake | 編譯 llama.cpp 時需要 |

### Linux（Ubuntu / Debian）

```bash
sudo apt update
sudo apt install -y git curl build-essential cmake python3 python3-pip
curl -LsSf https://astral.sh/uv/install.sh | sh
```

安裝完成後重新登入 shell，或手動載入 `uv`：

```bash
source "$HOME/.local/bin/env"
```

### Windows

1. **Git for Windows**：<https://git-scm.com/download/win>
2. **Python 3.12+**：<https://www.python.org/downloads/windows/>
  - 安裝時勾選 **Add Python to PATH**
3. **uv**（PowerShell）：
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
4. **Visual Studio Build Tools 2022**（僅編譯 llama.cpp 時需要）
5. 若使用 Intel XPU / iGPU，建議安裝 Intel oneAPI Runtime / Toolkit

### 選配需求

- NVIDIA GPU：需安裝對應驅動與 CUDA 執行環境
- Intel XPU / iGPU：Linux / Windows 皆可，需安裝對應驅動與執行環境
- 私有 Hugging Face 模型：需準備 `HF_TOKEN`

> **注意**：vLLM 僅支援 **Linux + CUDA**；Windows 平台無法使用 vLLM engine。
>
> 前端靜態檔已包含在專案內，不需要另外安裝 Node.js 或重新建置前端。

---

## 4. 從 GitHub 下載專案

本專案含 Git submodule，**clone 時請加上 `--recursive`**。

#### Linux

```bash
mkdir -p /home/test/project
cd /home/test/project
git clone --recursive <YOUR_GITHUB_REPOSITORY_URL> AI-Scaler-Toolkit
cd AI-Scaler-Toolkit
```

#### Windows（PowerShell）

```powershell
mkdir C:\Users\<user>\project
cd C:\Users\<user>\project
git clone --recursive <YOUR_GITHUB_REPOSITORY_URL> AI-Scaler-Toolkit
cd AI-Scaler-Toolkit
```

> 如果已用一般方式 clone，補執行：
> ```bash
> git submodule update --init --recursive
> ```

---

## 5. 第一次下載後必做設定

### 5.1 建立必要資料夾

#### Linux

```bash
mkdir -p logs .cache/huggingface runtime_data/inference_offload runtime_data/finetune_output
```

#### Windows（PowerShell）

```powershell
New-Item -ItemType Directory -Force logs, .cache\huggingface, runtime_data\inference_offload, runtime_data\finetune_output
```

### 5.2 建立 `.env`

專案啟動時，`service/settings.py` 會優先讀取專案根目錄的 `.env`；如果 `.env` 不存在，才會退回 `.env.example`。

**原則：請優先修改 `.env`，不要直接改 `service/settings.py`。**

#### Linux

```bash
cp .env.example .env
```

#### Windows（PowerShell）

```powershell
Copy-Item .env.example .env
```

接著用文字編輯器開啟 `.env`，至少建議確認以下內容：

#### Linux 範例

```dotenv
SERVICE_HOST=127.0.0.1
SERVICE_PORT=8000
UVICORN_RELOAD=false

HF_HOME=/home/test/project/AI-Scaler-Toolkit/.cache/huggingface
TIKTOKEN_RS_CACHE_DIR=/home/test/project/AI-Scaler-Toolkit
LOG_DIR=/home/test/project/AI-Scaler-Toolkit/logs

LOG_TO_FILE=true
LOG_FILE_NAME=service.log
LOG_BACKUP_COUNT=14
UVICORN_ACCESS_LOG=true
UVICORN_USE_COLORS=true
```

#### Windows 範例

```dotenv
SERVICE_HOST=127.0.0.1
SERVICE_PORT=8000
UVICORN_RELOAD=false

HF_HOME=C:\Users\<user>\project\AI-Scaler-Toolkit\.cache\huggingface
TIKTOKEN_RS_CACHE_DIR=C:\Users\<user>\project\AI-Scaler-Toolkit
LOG_DIR=C:\Users\<user>\project\AI-Scaler-Toolkit\logs

LOG_TO_FILE=true
LOG_FILE_NAME=service.log
LOG_BACKUP_COUNT=14
UVICORN_ACCESS_LOG=true
UVICORN_USE_COLORS=true
```

若要啟用 `.env.example` 中原本被註解掉的選配設定，請把行首的 `#` 拿掉，再填入實際值。例如：

```dotenv
HF_TOKEN=hf_xxxxxxxxxxxxx
LLAMA_SERVER_URL=http://127.0.0.1:5001
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
```

若已經編譯好 llama.cpp，也可在 `.env` 補上：

```dotenv
LLAMA_SERVER_BINARY=./service/utils/llama.cpp/build/bin/llama-server
```

Windows 範例：

```dotenv
LLAMA_SERVER_BINARY=./service/utils/llama.cpp/build/bin/Release/llama-server.exe
```

> 路徑可以用正斜線 `/` 或反斜線 `\`，Python 的 `pathlib` 兩者皆支援。

### 5.3 常見需要手動調整的路徑設定

| 變數 | 用途 | 預設值 |
|------|------|--------|
| `HF_HOME` | Hugging Face 模型與快取 | `<project>/.cache/huggingface` |
| `TIKTOKEN_RS_CACHE_DIR` | TikToken / GPT-OSS 快取 | 專案根目錄 |
| `LOG_DIR` | 日誌輸出目錄 | `<project>/logs` |
| `LLAMA_SERVER_BINARY` | llama-server 可執行檔路徑 | 自動尋找 build 輸出 |
| `VLLM_SERVER_PROJECT_DIR` | vLLM 隔離環境目錄 | `service/inference/engines/vllm_server` |

### 5.4 dmidecode 權限設定（Linux 選配）

後端 `/system/resources` API 呼叫 `dmidecode` 取得 DRAM 規格。非 root 環境下若要完整資訊，可設定 sudoers 規則：

```bash
sudo visudo -f /etc/sudoers.d/ast-dmidecode
```

加入以下一行（將 `<user>` 替換成實際執行服務的帳號）：

```
<user> ALL=(root) NOPASSWD: /usr/sbin/dmidecode -t memory
```

若跳過此步驟，API 仍可正常運作，DRAM 規格欄位可能顯示為空。

## 6. 建立 Python 環境

### Linux

#### 建議：使用自動腳本

```bash
cd /home/test/project/AI-Scaler-Toolkit
TRUSTA_ACCEL=xpu bash deploy/linux/setup_env.sh
```

若要改用 CUDA：

```bash
cd /home/test/project/AI-Scaler-Toolkit
TRUSTA_ACCEL=cuda bash deploy/linux/setup_env.sh
```

跳過 vLLM 環境建置：

```bash
cd /home/test/project/AI-Scaler-Toolkit
TRUSTA_ACCEL=cuda TRUSTA_SETUP_VLLM=0 bash deploy/linux/setup_env.sh
```

腳本會在 `service/.venv` 建立環境；**不需要另外手動啟動虛擬環境**。

### Windows

```powershell
cd C:\Users\<user>\project\AI-Scaler-Toolkit
.\deploy\windows\setup_env.ps1 -Accel xpu
```

若要改用 CUDA：

```powershell
cd C:\Users\<user>\project\AI-Scaler-Toolkit
.\deploy\windows\setup_env.ps1 -Accel cuda
```

腳本會在 `service\.venv` 建立環境；**不需要另外手動啟動虛擬環境**。

### 6.1 若要使用 llama-server

`llama.cpp` 來源在 submodule `service/utils/llama.cpp`，需自行編譯。

#### Linux

```bash
cd /home/test/project/AI-Scaler-Toolkit/service/utils/llama.cpp
cmake -B build
cmake --build build -j
```

若有 CUDA GPU 可加上：

```bash
cmake -B build -DGGML_CUDA=ON
cmake --build build -j
```

#### Windows（PowerShell，需 Visual Studio Build Tools 2022）

```powershell
cd C:\Users\<user>\project\AI-Scaler-Toolkit\service\utils\llama.cpp
cmake -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release -j
```

若有 CUDA GPU：

```powershell
cmake -B build -G "Visual Studio 17 2022" -A x64 -DGGML_CUDA=ON
cmake --build build --config Release -j
```

編譯完成後，在 `.env` 設定 `LLAMA_SERVER_BINARY` 指向實際輸出路徑。

官方編譯說明：<https://github.com/ggml-org/llama.cpp#build>

### 6.2 若要使用 vLLM engine（僅 Linux + CUDA）

`setup_env.sh` 在 CUDA 主機上會自動建立 vLLM 隔離環境；Windows 不支援 vLLM engine。

## 7. 啟動服務

### Linux

```bash
cd /home/test/project/AI-Scaler-Toolkit
bash deploy/linux/run_service.sh
```

若需要讓 `/system/resources` API 透過 `dmidecode` 讀取完整 DRAM 資訊，可改用具備權限的方式啟動：

```bash
cd /home/test/project/AI-Scaler-Toolkit
sudo bash deploy/linux/run_service.sh
```

> 建議優先依照前文設定 `sudoers`，只授權特定 `dmidecode` 指令；除非必要，不建議長期以 root 執行整個服務。


### Windows

```powershell
cd C:\Users\<user>\project\AI-Scaler-Toolkit
.\deploy\windows\run_service.bat
```

啟動腳本會直接使用 `service/.venv` 內的 Python；**不需要手動啟動虛擬環境**。

### 預設服務位址

| 位址 | 說明 |
|------|------|
| `http://127.0.0.1:8000/` | 前端首頁（若前端檔案存在，會自動轉到 `/frontend/`） |
| `http://127.0.0.1:8000/health` | 健康檢查 |
| `http://127.0.0.1:8000/docs` | Swagger UI |
| `http://127.0.0.1:8000/redoc` | ReDoc |

---

## 8. 啟動後如何驗證

### 8.1 健康檢查

#### Linux

```bash
curl http://127.0.0.1:8000/health
```

#### Windows（PowerShell）

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### 8.2 查看可用模型列表

#### Linux

```bash
curl http://127.0.0.1:8000/config/models
```

#### Windows（PowerShell）

```powershell
Invoke-RestMethod http://127.0.0.1:8000/config/models
```

### 8.3 先載入模型，再送出聊天請求

聊天前請先呼叫 `/inference/load_model` 載入模型；若模型尚未載入完成，聊天請求可能會回傳模型未就緒。

#### Linux

```bash
curl http://127.0.0.1:8000/inference/load_model \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "Qwen/Qwen3-4B"
  }'
```

#### Windows（PowerShell）

```powershell
Invoke-RestMethod http://127.0.0.1:8000/inference/load_model `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"model_name":"Qwen/Qwen3-4B"}'
```

確認模型載入完成後，再送聊天請求：

#### Linux

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "trusta-ast-default",
    "messages": [{"role": "user", "content": "你好，請簡單自我介紹"}],
    "stream": false
  }'
```

#### Windows（PowerShell）

```powershell
Invoke-RestMethod http://127.0.0.1:8000/v1/chat/completions `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"model":"trusta-ast-default","messages":[{"role":"user","content":"你好"}],"stream":false}'
```

---

## 9. 常用 API 路由

### 基本

- `GET /`
- `GET /health`
- `GET /v1/models`
- `POST /v1/chat/completions`

`/v1/models` returns the completion alias `trusta-ast-default` when a model is loaded. Use the same alias in `/v1/chat/completions` requests.

### 推論管理

- `POST /inference/load_model`
- `POST /inference/unload_model`
- `GET /inference/status`
- `POST /inference/estimate_memory`
- `POST /inference/stop_generation`

### 訓練管理

- `POST /training/start`
- `GET /training/status`
- `POST /training/stop`

### 模型設定與下載

- `GET /config/models`
- `POST /config/models/download`
- `GET /config/models/download/{task_id}`

### 系統資訊

- `GET /system/resources`

---

## 10. 前端說明

專案已內含前端靜態檔：

- `Trusta-AST-Frontend/dist`
- `Trusta-AST-Frontend/dist_client`

目前後端會掛載 `Trusta-AST-Frontend/dist` 到 `/frontend/`，根路徑 `/` 會在 `index.html` 存在時自動轉址到 `/frontend/`。

因此：

- 不需要安裝 Node.js
- 不需要另外執行前端 build
- 只要服務啟動成功，直接開 `http://127.0.0.1:8000/` 即可

---

## 11. 日誌設定

```dotenv
LOG_TO_FILE=true
LOG_DIR=<project>/logs
LOG_FILE_NAME=service.log
LOG_BACKUP_COUNT=14
```

啟用後會產生：

- `service.log`
- `service.log.YYYY-MM-DD`（日切輪替）

---

## 12. 維護更新

每次從 GitHub 拉新版本後，建議重新同步依賴。

### Linux

```bash
cd /home/test/project/AI-Scaler-Toolkit
TRUSTA_ACCEL=xpu bash deploy/linux/setup_env.sh
```

若改用 CUDA：

```bash
cd /home/test/project/AI-Scaler-Toolkit
TRUSTA_ACCEL=cuda bash deploy/linux/setup_env.sh
```

### Windows

```powershell
cd C:\Users\<user>\project\AI-Scaler-Toolkit
.\deploy\windows\setup_env.ps1 -Accel xpu
```

若改用 CUDA：

```powershell
cd C:\Users\<user>\project\AI-Scaler-Toolkit
.\deploy\windows\setup_env.ps1 -Accel cuda
```

---

## 13. 常見問題

### Q1. 執行啟動腳本時出現找不到 `.venv`

代表尚未建立 Python 環境，請先執行：

- Linux：`TRUSTA_ACCEL=xpu bash deploy/linux/setup_env.sh`
- Windows：`.\deploy\windows\setup_env.ps1 -Accel xpu`

### Q2. 新機器下載後，模型快取還指到舊路徑

請優先檢查 `.env`：

```dotenv
HF_HOME=<你的快取路徑>
TIKTOKEN_RS_CACHE_DIR=<你的專案根目錄>
```

### Q3. API 已經啟動，但首頁沒有前端畫面

請先確認專案內的前端資料夾已有檔案：

- `Trusta-AST-Frontend/dist/index.html`
- `Trusta-AST-Frontend/dist/assets/`

若 `dist` 內已有檔案，直接重新開啟 `http://127.0.0.1:8000/` 即可。

### Q4. 只需要後端 API，不需要前端

直接使用以下路徑即可：

- `/docs`
- `/health`
- `/v1/chat/completions`

### Q5. Windows 上 `setup_env.ps1` 執行失敗

先確認：

- 已安裝 Python 3.12+
- 已安裝 `uv`
- 若使用 XPU，已安裝 Intel oneAPI

必要時可先調整 PowerShell 執行原則：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q6. Windows 上 `-Accel cuda` 建環境失敗

請確認已安裝 CUDA Toolkit，且驅動版本相容。若不是 NVIDIA GPU，請改用：

```powershell
.\deploy\windows\setup_env.ps1 -Accel xpu
```

### Q7. 用 DeepSpeed 做 fine-tune 時出現 offload / buffer / swapper 類錯誤怎麼辦？

本專案內建的 DeepSpeed profile 位於：

- `service/configs/deepspeed/zero3_offload_cpu_cpu.json`
- `service/configs/deepspeed/zero3_offload_cpu_disk.json`
- `service/configs/deepspeed/zero3_offload_disk_cpu.json`
- `service/configs/deepspeed/zero3_offload_disk_disk.json`

若錯誤訊息提到 `buffer`、`swapper`、NVMe offload、aio / offload queue 類問題，最常見的第一步是調高 `zero_optimization.offload_param.buffer_count`。

例如：

```json
"offload_param": {
  "device": "nvme",
  "buffer_count": 6
}
```

若仍不穩，再逐步調到 `8`，不要一次改太大。

如果 `offload_optimizer.device` 也是 `nvme`，也可以一併調整 `zero_optimization.offload_optimizer.buffer_count`。

> 實務上若看到類似「buffer 0 / swapper 1」錯誤，通常先從 `offload_param.buffer_count` 開始調最有效。

#### DeepSpeed 常見可調參數

| 參數 | 位置 | 何時調整 | 常見效果 / 取捨 |
|------|------|----------|------------------|
| `buffer_count` | `zero_optimization.offload_param.buffer_count` | NVMe/CPU offload 過程出現 buffer、swapper、queue 類錯誤 | 增加可用緩衝數，通常可改善 offload 穩定性，但會多吃記憶體 / 主記憶體 |
| `buffer_count` | `zero_optimization.offload_optimizer.buffer_count` | optimizer offload 到 NVMe 時出現類似錯誤 | 與上面類似，但作用在 optimizer state |
| `buffer_size` | `zero_optimization.offload_param.buffer_size` | 磁碟 I/O 過碎、吞吐不穩、頻繁 offload | 調大可減少切片次數，但會增加單次緩衝占用 |
| `max_in_cpu` | `zero_optimization.offload_param.max_in_cpu` | NVMe 太慢、希望多保留一部分參數在 RAM | 提高可減少磁碟讀寫，但會增加系統 RAM 使用 |
| `pin_memory` | `zero_optimization.offload_param.pin_memory` / `zero_optimization.offload_optimizer.pin_memory` | CPU RAM 夠、希望改善 CPU↔GPU 傳輸 | 可能提升傳輸效率，但也可能增加 RAM 壓力；記憶體吃緊時可關掉 |
| `stage3_prefetch_bucket_size` | `zero_optimization.stage3_prefetch_bucket_size` | ZeRO-3 prefetch 過大導致顯存 / RAM 壓力，或 I/O 不順 | 調小較保守、較穩；調大可能提升吞吐 |
| `reduce_bucket_size` | `zero_optimization.reduce_bucket_size` | 通訊或聚合過程吃太多顯存 | 調小可降瞬時記憶體壓力，但可能影響速度 |
| `stage3_param_persistence_threshold` | `zero_optimization.stage3_param_persistence_threshold` | 參數頻繁搬移造成效能不穩 | 調整可改變常駐策略，需配合模型大小實測 |
| `sub_group_size` | `zero_optimization.sub_group_size` | 超大模型分組處理時記憶體或效能不理想 | 調小較保守，調大可能提升效率 |
| `contiguous_gradients` | `zero_optimization.contiguous_gradients` | 梯度碎片化或記憶體配置問題 | 通常維持 `true`；若遇特殊相容性問題可測試切換 |
| `overlap_comm` | `zero_optimization.overlap_comm` | 通訊重疊造成不穩、記憶體尖峰、效能異常 | 關閉可提升穩定性，但可能變慢 |

#### 不只 DeepSpeed config，也常一起調整的訓練參數

若單改 DeepSpeed 仍不穩，通常也要一起降低訓練壓力：

| 參數 | 位置 | 建議方向 |
|------|------|----------|
| `per_device_train_batch_size` | 訓練請求 body | 顯存不足時先往下調 |
| `gradient_accumulation_steps` | 訓練請求 body 或 DeepSpeed config | batch size 降低後，可往上補回有效 batch |
| `max_seq_length` | 訓練請求 body | 序列太長時先降，例如 `4096 -> 2048` |
| `gradient_checkpointing` | 訓練請求 body | 記憶體不足時建議保持啟用 |

#### 建議調整順序

1. 先確認使用的是哪個 profile（CPU offload / NVMe offload）。
2. 若錯誤含 `buffer` / `swapper`，先調 `offload_param.buffer_count`。
3. 若 NVMe offload 仍不穩，再調 `offload_optimizer.buffer_count`、`buffer_size`、`max_in_cpu`。
4. 若是顯存 / RAM 不足，再降低 `per_device_train_batch_size`、`max_seq_length`。
5. 若是吞吐或穩定性問題，再微調 `stage3_prefetch_bucket_size`、`reduce_bucket_size`、`overlap_comm`。

若使用 NVMe offload，另外也建議確認：

- `nvme_path` 所在磁碟空間足夠
- 盡量使用 SSD / NVMe，不要放在慢速 HDD
- 避免與其他高 I/O 工作共用同一顆磁碟
