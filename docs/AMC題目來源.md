# AMC 10 題目來源調查

調查日期：2026-11-21。本文只記錄來源與授權狀態，不含任何題目原文。

> **重要提醒**：AMC 題目與答案由 MAA（美國數學協會）擁有著作權。以下各來源的「授權」欄多數是**第三方轉述或未驗證**的說明，不是 MAA 的正式書面授權。在與孫老師討論並確定前，本站不應發布題目原文，網站也不應被搜尋引擎收錄。

## 一、來源清單

| # | 來源 | 網址 | 涵蓋年份／份別 | 格式 | 含解答？ | 授權／使用條款（已知內容） |
|---|---|---|---|---|---|---|
| 1 | AoPS Wiki（Art of Problem Solving） | https://artofproblemsolving.com/wiki/index.php/AMC_10_Problems_and_Solutions | AMC 10A/B，約 2000 年起（頁面有 2026、2027 條目，後者不尋常，需留意） | HTML（wiki 頁面）、LaTeX 原始碼 | 有（使用者撰寫的解法） | 題目頁面標示 MAA 版權；wiki 文字的授權未在本次查證中確認（通常標示為 CC BY-SA，需到頁面底部自行核對）。 |
| 2 | MAA 官網 AMC 頁面 | https://maa.org/math-competitions/amc-policies （政策頁）；AMC 辦公室可購買歷屆試卷與解答 | 歷屆 AMC 10 | PDF／紙本／光碟 | 通常含解答卷 | 本次調查時，MAA 政策頁回傳 **HTTP 403**，無法讀取其使用條款。MAA 的 FAQ 指出可直接向 AMC 辦公室購買試卷與解答。**這是最權威的來源，但條款內容未驗證。** |
| 3 | LIVE by Po-Shen Loh（過去試題頁） | https://live.poshenloh.com/past-contests | AMC 8／10（含 AMC 10A/B 歷屆） | 可列印 PDF、網頁 | 有答案卷 | 網站自述：AMC 題目「經 MAA 官方許可」使用。**這是第三方的聲明，未見到 MAA 的書面許可原文。** |
| 4 | Hugging Face：`kaggle-aimo/amc_filtered` | https://huggingface.co/datasets/kaggle-aimo/amc_filtered | 2002–2023 AMC 10A/B（本次取得 640 題，分布不完整，每卷約 6–19 題，非完整卷） | Parquet（已用 datasets-server API 轉成 JSON） | **否**：只有題幹與數值答案，無選項、無解答 | 資料集卡片與 metadata **未列出授權**（無 license 欄位）。題目 id 指向 AoPS wiki。**授權不明，不可視為可再發布。** |
| 5 | Hugging Face：`nanoverl/amc` | https://huggingface.co/datasets/nanoverl/amc | 2022–2023 **AMC 12** 題目（83 題） | JSON | 否 | 無授權欄位。**不含 AMC 10，已棄用。** |
| 6 | Hugging Face：`camel-ai/amc_aime_self_improving` | https://huggingface.co/datasets/camel-ai/amc_aime_self_improving | 含 AMC／AIME 題目 | JSON（records.json） | 有模型生成的解題軌跡 | 授權標示 MIT（資料集卡片）。但解題軌跡為模型生成，題目來源仍是 AMC，**MIT 不代表 AMC 題目可以再發布**。未深入查核，未使用。 |
| 7 | Toomates.net（AoPS 頁面提及的合集 PDF） | 見 AoPS AMC 10 頁面連結 | 多項競賽合併 PDF | PDF | 視版本 | 未查證，未使用。 |
| 8 | 大學網站的 AMC 8 冊子（如 usm.edu、mathwo.github.io） | 例：https://mathwo.github.io/assets/files/AMC-8-Problems-2014-2019.pdf | AMC 8（非 AMC 10） | PDF | 有 | 其中一本 2014 年的冊子寫道：為非營利教育用途，可以在網頁上張貼單題影本，但需附版權聲明。**這是舊版、第三方轉述，無法確認是否適用於現行 AMC 10。** 另一所大學頁面則以「合理使用」主張，同樣只是機構自己的立場。 |

### 中文來源
本次只做了英文搜尋，**未系統性查找中文來源**（例如台灣或大陸的競賽書籍、補習班講義）。這些來源大多同樣含有 MAA 題目，授權問題相同，需另行評估。

## 二、已取得的本機資料

- 位置：`data/amc10_local/contests/`（已被 `.gitignore` 的 `data/*/` 規則忽略，**不可 `git add`**）。
- 檔案：`{年}_AMC10{A|B}.json`，共 44 份卷，**640 題**，涵蓋 2002–2023 年 A/B 卷。
- 每題欄位：`id`、`year`、`AB`、`number`、`statement`（題幹，目前為原始文字，尚未轉為 LaTeX 格式化）、`choices`（**此來源沒有，全部為 null**）、`answer`（**數值，不是選項字母**）、`answer_note`、`source_url`（AoPS 題目頁）、`dataset_url`。
- 缺口：每卷只有部分題目（完整 AMC 10 每卷 25 題）；2024、2025、2026 年沒有資料；選項與答案字母缺失。
- 原始暫存檔 `data/amc10_local/raw/kaggle_amc10_rows.json` 同樣只留在本機。

## 三、建議

1. **首選：向 MAA／AMC 辦公室確認書面授權。** 這是唯一能確定可否發布的途徑。在拿到答覆前，不發布題目原文。
2. **可作為參考的官方管道：** LIVE（Po-Shen Loh）的 PDF 聲稱有 MAA 許可，可以先在本機閱讀、比對，但仍需確認其授權範圍是否允許再發布。
3. **不建議作為正式資料來源：** `kaggle-aimo/amc_filtered`（授權不明、無選項、答案非字母、資料不完整）。目前只用於本機內部比對。
4. **若要做網站：** 在授權確定前，只能放「題目出處」與「自己改寫的解法」，而且不應附原題文字；網站設定 `noindex`（目前 repo 已有此設定，需保持）。

## 四、版權立場（未確定的部分）

- **已知：** AMC 題目的著作權屬於 MAA。
- **未知，需與 MAA 確認：** (a) 網站上發布題目原文是否允許；(b) 是否允許改寫後發布（改寫的解法是否屬於衍生著作）；(c) 「合理使用」主張在美國法下是否適用於這種教育網站，且只能由法律專業判斷；(d) LIVE 所稱的「MAA 官方許可」範圍為何。
- 本文不是法律意見。以上未知事項應與孫老師一併討論。

## 五、查證限制

- MAA 政策頁在本次調查時回傳 HTTP 403，無法讀取，條款內容**未驗證**。
- 大部分授權說明來自第三方網站或搜尋摘要，未逐一核對原始條款。
- Hugging Face 資料集的授權欄位為空白或未列出，已如實標示為「不明」。
