# 🛡️ NPL Detection Algorithm

![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg) ![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

A **fancy**, lightning‑fast CLI tool that routes free‑form user queries to one or more security modules.  
Built with:
-  **Hard Match**  
-  **SBERT Semantic**  
-  **Zero‑Shot NLI**  

---

## 🚀 Features

- **Instant explicit matches** for named modules  
- **Semantic understanding** of fuzzy or implied requests  
- **Deep fallback** using zero‑shot classification  
- **Threshold controls** to avoid false positives  
- **Modular design** for easy extension  

---

## 🔍 Layers Explained

### Layer 1: Hard Match 
- **What it does**: Scans the query for exact module names or compact variants (e.g. “PublicGroupMonitoring”)  
- **Fuzzy acronyms**: Uses `get_close_matches` on words ≥ 4 chars to catch acronyms like “phishing” → `Phishing`  
- **Why it matters**: Guarantees 100% precision when users explicitly mention modules  
- **Output**: If any hard match is found, **only** those modules are returned — no further processing.

---

### Layer 2: SBERT Semantic 
- **When it runs**: Only if Layer 1 finds *no* hard match  
- **How it works**:  
  1. Encodes your query and all module descriptions with **Sentence‑BERT**  
  2. Computes cosine similarities  
  3. Picks the **top‑k** modules (default k=2) with similarity ≥ 0.45  
- **Strength**: Captures implied requests like “domain exposure” → `ASM`  
- **Guardrail**: If the **highest** similarity < 0.45, it aborts and declares “no match.”

---

### Layer 3: Zero‑Shot NLI 
- **When it runs**: Only if Layer 2 finds *no* SBERT matches  
- **Mechanism**: Uses `facebook/bart-large-mnli` zero‑shot classifier  
- **Process**:  
  1. Treats each module name as a label  
  2. Runs multi‑label entailment  
  3. Picks labels with probability ≥ 0.5  
- **Use case**: Handles very vague or multi‑intent queries, e.g. “scan for anything data leak”  
- **Abort**: If *no* labels pass 0.5, it returns **no modules**.

---

## 🏗️ Architecture Diagram

```mermaid
flowchart TD
    Q[User Query] --> L1{Hard Match?}
    L1 -->|Yes| R[Return Hard Matches]
    L1 -->|No| L2[SBERT Layer]
    L2 -->|Top‑k ≥ 0.45| R
    L2 -->|No| L3[Zero‑Shot Layer]
    L3 -->|Score ≥ 0.5| R
    L3 -->|No| X[No Modules Detected]
