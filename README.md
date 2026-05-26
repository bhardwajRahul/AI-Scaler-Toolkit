# Trusta AST Backend

Trusta AST Backend 是一個以 FastAPI 為核心的 LLM 後端服務，提供：

- 模型載入 / 卸載
- OpenAI 相容聊天介面
- 推論與串流回應
- 訓練工作啟動與狀態查詢
- 模型下載與轉換
- RAG 文件管理與檢索
- 前端靜態頁面掛載

本文件同時涵蓋 **Linux** 與 **Windows** 兩種平台，步驟有差異的地方會分開說明。

> **Linux 範例路徑**：`/home/test/project/Trusta_AST_Backend`
> **Windows 範例路徑**：`C:\Users\<user>\project\Trusta_AST_Backend`（可自行選擇）

---

## 1. 專案結構

```text
Trusta_AST_Backend/
├─ deploy/
│  ├─ linux/
│  │  ├─ run_service.sh
│  │  └─ setup_env.sh
│  └─ docker/
├─ docs/
├─ logs/
├─ runtime_data/
├─ Trusta-AST-Frontend/
│  ├─ dist/                 # Trusta 風格前端靜態檔
│  └─ dist_client/          # ADATA 風格前端靜態檔
├─ service/
│  ├─ app.py
│  ├─ settings.py
│  ├─ pyproject.toml
│  └─ .venv/                # 建立後會出現在這裡
├─ tests/
├─ .env.example
└─ README.md
```

---

## 2. 系統需求

### 基本需求（兩平台共同）

| 工具 | 說明 |
|------|------|
| Git | 含 submodule 支援 |
| Python 3.12+ | 執行服務本體 |
| `uv` | Python 套件 / 虛擬環境管理 |
| C/C++ 編譯工具鏈 | 編譯 llama.cpp（選配，僅 llama-server 需要）|
| cmake | 同上 |

### Linux（Ubuntu / Debian）

```bash
sudo apt update
sudo apt install -y git curl build-essential cmake python3 python3-venv python3-pip
curl -LsSf https://astral.sh/uv/install.sh | sh
```

安裝完成後重新登入 shell，或手動載入 `uv`：

```bash
source "$HOME/.local/bin/env"
```

### Windows

1. **Git for Windows**：<https://git-scm.com/download/win>（或 `winget install Git.Git`）
2. **Python 3.12+**：<https://www.python.org/downloads/windows/>（或 `winget install Python.Python.3.12`）
   - 安裝時勾選 **Add Python to PATH**
3. **uv**（PowerShell）：
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
4. **Visual Studio Build Tools 2022**（僅需編譯 llama.cpp 時）：
   - 下載：<https://visualstudio.microsoft.com/visual-cpp-build-tools/>
   - 勾選工作負載：**Desktop development with C++**
   - cmake 已內含於上述工具，或單獨安裝：`winget install Kitware.CMake`

### 選配需求（兩平台）

- NVIDIA GPU：需安裝對應驅動與 CUDA 執行環境
- Intel XPU / iGPU（僅 Linux）：需安裝對應驅動與 XPU 執行環境
- 前端建置：需安裝 Node.js 18+
- 私有 Hugging Face 模型：需準備 `HF_TOKEN`

> **注意**：vLLM 僅支援 **Linux + CUDA**，Windows 平台無法使用 vLLM engine。

---

## 3. 從 GitLab 下載專案

本專案含 Git submodule（`service/utils/llama.cpp`），**clone 時必須加上 `--recursive`**。

#### Linux

```bash
mkdir -p /home/test/project
cd /home/test/project
git clone --recursive <YOUR_GITLAB_REPOSITORY_URL> Trusta_AST_Backend
cd Trusta_AST_Backend
```

#### Windows（PowerShell）

```powershell
mkdir C:\Users\<user>\project
cd C:\Users\<user>\project
git clone --recursive <YOUR_GITLAB_REPOSITORY_URL> Trusta_AST_Backend
cd Trusta_AST_Backend
```

> 如果已用一般方式 clone，補執行：
> ```bash
> git submodule update --init --recursive
> ```

---

## 4. 第一次下載後必做設定

### 4.1 建立必要資料夾

#### Linux

```bash
mkdir -p logs .cache/huggingface runtime_data/inference_offload runtime_data/finetune_output
```

#### Windows（PowerShell）

```powershell
New-Item -ItemType Directory -Force logs, .cache\huggingface, runtime_data\inference_offload, runtime_data\finetune_output
```

### 4.2 建立 `.env`

專案啟動時讀取根目錄的 `.env`（不讀 `.env.example`）。先複製範本：

#### Linux

```bash
cp .env.example .env
```

#### Windows（PowerShell）

```powershell
Copy-Item .env.example .env
```

接著用文字編輯器開啟 `.env`，**至少建議設定以下內容**：

#### Linux 範例

```dotenv
# ===== 基本服務設定 =====
# SERVICE_HOST：127.0.0.1 僅允許本機連線（建議）；0.0.0.0 允許外部連入（需搭配反向代理）
SERVICE_HOST=127.0.0.1
SERVICE_PORT=8000
UVICORN_RELOAD=false

# ===== 快取與執行資料 =====
HF_HOME=/home/test/project/Trusta_AST_Backend/.cache/huggingface
TIKTOKEN_RS_CACHE_DIR=/home/test/project/Trusta_AST_Backend
LOG_DIR=/home/test/project/Trusta_AST_Backend/logs

# ===== 日誌 =====
LOG_TO_FILE=true
LOG_FILE_NAME=service.log
LOG_BACKUP_COUNT=14
UVICORN_ACCESS_LOG=true
UVICORN_USE_COLORS=true

# ===== 選配：Hugging Face 私有模型 =====
# HF_TOKEN=hf_xxxxxxxxxxxxx

# ===== 選配：llama.cpp server =====
# LLAMA_SERVER_BINARY=/home/test/project/Trusta_AST_Backend/service/utils/llama.cpp/build/bin/llama-server
# LLAMA_SERVER_URL=http://127.0.0.1:5001

# ===== 選配：Redis =====
# REDIS_HOST=127.0.0.1
# REDIS_PORT=6379
# REDIS_DB=0
```

#### Windows 範例

```dotenv
SERVICE_HOST=127.0.0.1
SERVICE_PORT=8000
UVICORN_RELOAD=false

HF_HOME=C:\Users\<user>\project\Trusta_AST_Backend\.cache\huggingface
TIKTOKEN_RS_CACHE_DIR=C:\Users\<user>\project\Trusta_AST_Backend
LOG_DIR=C:\Users\<user>\project\Trusta_AST_Backend\logs

LOG_TO_FILE=true
LOG_FILE_NAME=service.log
LOG_BACKUP_COUNT=14
UVICORN_ACCESS_LOG=true
UVICORN_USE_COLORS=true

# HF_TOKEN=hf_xxxxxxxxxxxxx

# Windows llama-server 二進位通常在 build\bin\Release\
# LLAMA_SERVER_BINARY=C:\Users\<user>\project\Trusta_AST_Backend\service\utils\llama.cpp\build\bin\Release\llama-server.exe
# LLAMA_SERVER_URL=http://127.0.0.1:5001
```

> 路徑可以用正斜線 `/` 或反斜線 `\`，Python 的 `pathlib` 兩者皆支援。

### 4.3 如果 Hugging Face 快取路徑要更換

在 `.env` 修改 `HF_HOME` 即可：

```dotenv
# Linux
HF_HOME=/data/huggingface-cache

# Windows
HF_HOME=D:\huggingface-cache
```

修改後重新啟動服務生效。

### 4.4 常見需要手動調整的路徑設定

| 變數 | 用途 | 預設值 |
|------|------|--------|
| `HF_HOME` | Hugging Face 模型與快取 | `<project>/.cache/huggingface` |
| `TIKTOKEN_RS_CACHE_DIR` | TikToken / GPT-OSS 快取 | 專案根目錄 |
| `LOG_DIR` | 日誌輸出目錄 | `<project>/logs` |
| `LLAMA_SERVER_BINARY` | llama-server 可執行檔路徑 | 自動尋找 build 輸出 |
| `VLLM_SERVER_PROJECT_DIR` | vLLM 隔離環境目錄（僅 Linux）| `service/inference/engines/vllm_server` |

原則：**先改 `.env`**；只有在要改整個專案預設值時，才修改 `service/settings.py`。

### 4.5 dmidecode 權限設定（Linux 選配）

後端 `/system/resources` API 呼叫 `dmidecode` 取得 DRAM 規格。非 root 環境下需要 sudo 權限。

**建議做法：設定 sudoers 規則，免密碼執行特定指令**

```bash
sudo visudo -f /etc/sudoers.d/trusta-dmidecode
```

加入以下一行（將 `<user>` 替換成實際執行服務的帳號）：

```
<user> ALL=(root) NOPASSWD: /usr/sbin/dmidecode -t memory
```

若跳過此步驟，API 仍可正常運作，DRAM 規格欄位會顯示為空。

> Windows 平台不需要此設定，`dmidecode` 相關功能會自動略過。

---

## 5. 建立 Python 環境

Python 虛擬環境建立在 `service/.venv`。

### Linux

#### 作法 A：自動偵測腳本（建議）

腳本會自動選擇 `cuda` 或 `xpu`，CUDA 環境下同時建立 vLLM 隔離環境：

```bash
cd /home/test/project/Trusta_AST_Backend
bash deploy/linux/setup_env.sh
```

手動指定加速後端：

```bash
TRUSTA_ACCEL=cuda bash deploy/linux/setup_env.sh
# 或
TRUSTA_ACCEL=xpu bash deploy/linux/setup_env.sh
```

跳過 vLLM 環境建置：

```bash
TRUSTA_SETUP_VLLM=0 bash deploy/linux/setup_env.sh
```

#### 作法 B：手動建立

```bash
cd /home/test/project/Trusta_AST_Backend/service
uv sync --extra cuda    # NVIDIA GPU
# 或
uv sync --extra xpu     # Intel XPU
```

#### 啟用虛擬環境

```bash
source /home/test/project/Trusta_AST_Backend/service/.venv/bin/activate
```

---

### Windows

Windows 沒有 `setup_env.sh`，請直接用 `uv sync`：

```powershell
cd C:\Users\<user>\project\Trusta_AST_Backend\service
uv sync --extra cuda
```

> 若無 NVIDIA GPU，改用：
> ```powershell
> uv sync
> ```
> vLLM 不支援 Windows，不需要額外的 vLLM 環境。

#### 啟用虛擬環境（PowerShell）

```powershell
C:\Users\<user>\project\Trusta_AST_Backend\service\.venv\Scripts\Activate.ps1
```

若出現執行原則錯誤，先執行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 啟用虛擬環境（cmd）

```cmd
C:\Users\<user>\project\Trusta_AST_Backend\service\.venv\Scripts\activate.bat
```

---

### 5.1 若要使用 llama-server

`llama.cpp` 來源在 submodule `service/utils/llama.cpp`，需自行編譯。

#### Linux

```bash
cd /home/test/project/Trusta_AST_Backend/service/utils/llama.cpp
cmake -B build
cmake --build build -j
```

編譯輸出：

```
service/utils/llama.cpp/build/bin/llama-server
```

若有 CUDA GPU 可加上：

```bash
cmake -B build -DGGML_CUDA=ON
cmake --build build -j
```

#### Windows（PowerShell，需 Visual Studio Build Tools 2022）

```powershell
cd C:\Users\<user>\project\Trusta_AST_Backend\service\utils\llama.cpp
cmake -B build -G "Visual Studio 17 2022" -A x64
cmake --build build --config Release -j
```

編譯輸出：

```
service\utils\llama.cpp\build\bin\Release\llama-server.exe
```

若有 CUDA GPU：

```powershell
cmake -B build -G "Visual Studio 17 2022" -A x64 -DGGML_CUDA=ON
cmake --build build --config Release -j
```

編譯完成後，在 `.env` 設定 `LLAMA_SERVER_BINARY` 指向實際輸出路徑。

官方編譯說明：<https://github.com/ggml-org/llama.cpp#build>

---

### 5.2 若要使用 vLLM engine（僅 Linux + CUDA）

vLLM 環境獨立在 `service/inference/engines/vllm_server`。

`setup_env.sh` 在 CUDA 主機上會自動建立。若需手動建立：

```bash
cd /home/test/project/Trusta_AST_Backend/service/inference/engines/vllm_server
uv sync
```

---

## 6. 啟動服務

### Linux

```bash
cd /home/test/project/Trusta_AST_Backend
bash deploy/linux/run_service.sh
```

腳本會檢查 `service/.venv` 是否存在，並以 `python -m service.app` 啟動。

若需要讓 `/system/resources` API 透過 `dmidecode` 讀取完整 DRAM 資訊，可改用具備權限的方式啟動：

```bash
cd /home/test/project/Trusta_AST_Backend
sudo bash deploy/linux/run_service.sh
```

> 建議優先依照前文設定 `sudoers`，只授權特定 `dmidecode` 指令；除非必要，不建議長期以 root 執行整個服務。


### Windows（PowerShell）

Windows 沒有對應的啟動腳本，直接執行：

```powershell
cd C:\Users\<user>\project\Trusta_AST_Backend
service\.venv\Scripts\Activate.ps1
python -m service.app
```

### 預設服務位址

| 位址 | 說明 |
|------|------|
| `http://127.0.0.1:8000` | API Base URL |
| `http://127.0.0.1:8000/health` | 健康檢查 |
| `http://127.0.0.1:8000/docs` | Swagger UI |
| `http://127.0.0.1:8000/redoc` | ReDoc |

---

## 7. 啟動後如何驗證

### 7.1 健康檢查

#### Linux

```bash
curl http://127.0.0.1:8000/health
```

#### Windows（PowerShell）

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### 7.2 查看可用模型列表

#### Linux

```bash
curl http://127.0.0.1:8000/v1/models
```

#### Windows（PowerShell）

```powershell
Invoke-RestMethod http://127.0.0.1:8000/v1/models
```

### 7.3 OpenAI 相容聊天介面

#### Linux

```bash
curl http://127.0.0.1:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-model-name",
    "messages": [{"role": "user", "content": "你好，請簡單自我介紹"}],
    "stream": false
  }'
```

#### Windows（PowerShell）

```powershell
Invoke-RestMethod http://127.0.0.1:8000/v1/chat/completions `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"model":"your-model-name","messages":[{"role":"user","content":"你好"}],"stream":false}'
```

> 若尚未先載入模型，聊天請求可能會回傳模型未就緒。

---

## 8. 常用 API 路由

### 基本

- `GET /health`
- `GET /v1/models`
- `POST /v1/chat/completions`

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

### RAG

- `GET /rag/docs`
- `POST /rag/docs`
- `DELETE /rag/docs/{doc_id}`
- `GET /rag/search`

### 模型設定與下載

- `GET /config/models`
- `POST /config/models/download`
- `GET /config/models/download/{task_id}`
- `POST /config/models/convert`

### 系統資訊

- `GET /system/resources`

---

## 9. 前端整合

後端可掛載前端打包檔，提供兩種介面風格：

- `Trusta-AST-Frontend/dist`：Trusta 風格介面
- `Trusta-AST-Frontend/dist_client`：ADATA 風格介面

後端提供路由：

- `/frontend/`
- `/frontend/<任意子路徑>`
- `/`（若前端 build 存在，會轉址到 `/frontend/`）

### 前端建置方式

#### Linux

```bash
cd /home/test/project/Trusta-AST-Frontend
npm install
npm run build
```

#### Windows（PowerShell）

```powershell
cd C:\Users\<user>\project\Trusta-AST-Frontend
npm install
npm run build
```

### 前端設定檔

前端顯示的推論引擎可透過 `config.json` 調整：

- `Trusta-AST-Frontend/dist/config.json`
- `Trusta-AST-Frontend/dist_client/config.json`

```json
{
  "apiBaseUrl": "http://localhost:8000",
  "timeout": 10000,
  "enabledEngines": ["transformers", "llama_server", "vllm"]
}
```

若不使用 vLLM，將 `"vllm"` 從 `enabledEngines` 移除。Windows 平台建議只保留 `["transformers", "llama_server"]`。

---

## 10. 日誌設定

```dotenv
LOG_TO_FILE=true
LOG_DIR=<project>/logs
LOG_FILE_NAME=service.log
LOG_BACKUP_COUNT=14
```

啟用後會產生：

- `service.log`
- `service.log.YYYY-MM-DD`（日切輪替，Windows 預設停用以避免多進程衝突）

---

## 11. 測試

### Linux

```bash
source /home/test/project/Trusta_AST_Backend/service/.venv/bin/activate
cd /home/test/project/Trusta_AST_Backend
pytest
```

執行單一測試：

```bash
pytest tests/test_runtime_smoke.py
```

### Windows（PowerShell）

```powershell
service\.venv\Scripts\Activate.ps1
cd C:\Users\<user>\project\Trusta_AST_Backend
pytest
```

---

## 12. 常見問題

### Q1. 執行 `run_service.sh` 時出現找不到 `.venv`

尚未建立 Python 環境，請先執行 `setup_env.sh`（Linux）或 `uv sync`（Windows）。

### Q2. 新機器下載後，模型快取指到舊路徑

確認 `.env` 已設定：

```dotenv
HF_HOME=<你的快取路徑>
TIKTOKEN_RS_CACHE_DIR=<你的專案根目錄>
```

### Q3. API 起來了，但首頁沒有前端畫面

確認前端已 build，且 `dist/index.html` 存在。

### Q4. 只需要後端 API，不需要前端

直接使用 `/docs`、`/health`、`/v1/chat/completions` 即可。

### Q5. Windows 執行 `Activate.ps1` 出現執行原則錯誤

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q6. Windows 上 `uv sync --extra cuda` 失敗

確認已安裝 CUDA Toolkit 且驅動版本相容。若無 NVIDIA GPU，改用 `uv sync`（不加 `--extra cuda`）。

### Q7. 要用 Docker / Podman 部署嗎？

可參考 `deploy/docker/README-deploy.md`。

### Q8. 用 DeepSpeed 做 fine-tune 時出現 offload / buffer / swapper 類錯誤怎麼辦？

本專案內建的 DeepSpeed profile 放在：

- `service/configs/deepspeed/zero3_offload_cpu_cpu.json`
- `service/configs/deepspeed/zero3_offload_cpu_disk.json`
- `service/configs/deepspeed/zero3_offload_disk_cpu.json`
- `service/configs/deepspeed/zero3_offload_disk_disk.json`

如果 fine-tune 時錯誤訊息提到 `buffer 0`、`swapper 1`、NVMe offload、aio / offload queue 類問題，通常代表 **offload 緩衝數量不足、磁碟 I/O 跟不上，或目前配置不適合資料量**。最常見的第一步是：

1. 先找到你目前使用的 DeepSpeed profile。
2. 編輯對應的 `service/configs/deepspeed/*.json`。
3. 優先把 `zero_optimization.offload_param.buffer_count` 往上調整。

例如可從：

```json
"offload_param": {
  "device": "nvme",
  "buffer_count": 4
}
```

改成：

```json
"offload_param": {
  "device": "nvme",
  "buffer_count": 6
}
```

若還是出錯，再逐步調到 `8`，不要一次改太大。

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

---

## 13. 第一次初始化快速流程

### Linux（全新主機）

```bash
mkdir -p /home/test/project
cd /home/test/project
git clone --recursive <YOUR_GITLAB_REPOSITORY_URL> Trusta_AST_Backend
cd Trusta_AST_Backend

mkdir -p logs .cache/huggingface runtime_data/inference_offload runtime_data/finetune_output
cp .env.example .env
# 編輯 .env，設定 HF_HOME、LOG_DIR 等路徑

bash deploy/linux/setup_env.sh
source service/.venv/bin/activate
bash deploy/linux/run_service.sh
```

> CUDA 環境下 `setup_env.sh` 自動建立 vLLM 隔離環境；若要略過：
> `TRUSTA_SETUP_VLLM=0 bash deploy/linux/setup_env.sh`

---

### Windows（全新主機，PowerShell）

```powershell
# 1. 安裝前置工具（未安裝的話）
winget install Git.Git
winget install Python.Python.3.12
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Clone 專案
mkdir C:\Users\<user>\project
cd C:\Users\<user>\project
git clone --recursive <YOUR_GITLAB_REPOSITORY_URL> Trusta_AST_Backend
cd Trusta_AST_Backend

# 3. 建立必要資料夾
New-Item -ItemType Directory -Force logs, .cache\huggingface, runtime_data\inference_offload, runtime_data\finetune_output

# 4. 建立 .env 並編輯路徑
Copy-Item .env.example .env
notepad .env

# 5. 建立 Python 環境
cd service
uv sync --extra cuda   # 有 NVIDIA GPU；無 GPU 改用 uv sync
cd ..

# 6. 啟動服務
service\.venv\Scripts\Activate.ps1
python -m service.app
```

啟動成功後，用瀏覽器開啟：

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/health`

---

## 14. 補充說明

### Python 版本

`service/pyproject.toml` 要求 Python `>= 3.12`。

### 依賴管理

使用 `uv sync` 與 `service/pyproject.toml`。

### 啟動入口

```
python -m service.app
```

### 各引擎平台支援

| 引擎 | Linux | Windows |
|------|-------|---------|
| transformers | ✅ | ✅ |
| llama_server | ✅ | ✅（需自行編譯）|
| vllm | ✅（CUDA）| ❌ 不支援 |

---

## 15. 維護建議

每次從 GitLab 拉新版本後：

#### Linux

```bash
cd /home/test/project/Trusta_AST_Backend
source service/.venv/bin/activate
cd service
uv sync
```

vLLM 環境（選配）：

```bash
cd /home/test/project/Trusta_AST_Backend/service/inference/engines/vllm_server
uv sync
```

切換加速後端：

```bash
cd /home/test/project/Trusta_AST_Backend
TRUSTA_ACCEL=cuda bash deploy/linux/setup_env.sh
```

#### Windows（PowerShell）

```powershell
cd C:\Users\<user>\project\Trusta_AST_Backend
service\.venv\Scripts\Activate.ps1
cd service
uv sync
```

---

如需補充 Docker、Podman、前端整合或 API 範例文件，可再往下拆成獨立文件維護。
