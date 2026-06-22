# Wiki Log

> 知識庫操作的 chronological 記錄。追加模式。
> 格式：`## [YYYY-MM-DD] action | subject`
> 動作：ingest, update, query, lint, create, archive, delete

## [2026-05-28] create | LLM Wiki 知識庫初始化
- 建立基礎目錄結構
- 創建 SCHEMA.md - 定義知識庫規範
- 創建 index.md - 頁面目錄
- 創建 log.md - 操作日誌

## [2026-05-28] ingest | LLM Wiki 格式轉換機制研究
- 來源：GitHub 查詢
- 網址：https://github.com/atomicstrata/llm-wiki-compiler
- 內容：查詢 LLM Wiki 如何將不同格式（HTML、PDF、圖片等）轉換為 Markdown
- 建立檔案：
  - raw/articles/llm-wiki-format-conversion-2026-05-28.md
  - concepts/llm-wiki-pattern.md
  - concepts/file-format-conversion.md
  - SCHEMA.md
  - index.md
  - log.md

## [2026-05-28] ingest | Research Evidence Documentation
- 建立檔案：research-evidence.md
- 記錄所有查詢佐證和來源
- 提供完整的可追溯性

## [2026-05-28] update | Knowledge Base Structure Complete
- 總頁面數：5
- 原始文章：1
- 概念頁面：2
- 研究佐證：1
- SCHEMA: 1
- 知識庫結構完成，可開始後續查詢和補充

---

**備註**：
- 日誌超過 500 條時需旋轉（rename 為 log-YYYY.md）
- 每次 ingest、update、query 後都應更新此日誌
- 所有動作必須可追溯
