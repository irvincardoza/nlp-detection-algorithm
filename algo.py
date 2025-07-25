

from sentence_transformers import SentenceTransformer, util
from transformers import pipeline
from difflib import get_close_matches
import re
import torch
# ---------- Setup ----------

# SBERT for semantic matching
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')

# Zero-shot classifier (slow but powerful)
zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

modules=[add your own]


names = [m["name"] for m in modules]
desc_texts = [f"{m['name']}: {m['description']}" for m in modules]
corpus_embeddings = sbert_model.encode(desc_texts, convert_to_tensor=True)

# ---------- Related Module Rules (Optional) ----------
related_modules = {
    "IP Vulnerabilities": ["Active Scanning", "ASM", "Exposed Services"],
    "Phishing": ["Email Intel", "Public Group Monitoring"],
    "Cred Leaks": ["Email Intel", "Darknet", "Stealer Logs"],
}

# ---------- Main Detection Function ----------

def detect_modules(query: str, debug=False):
    import re
    from difflib import get_close_matches
    from sentence_transformers import util
    import torch

    # Lowercase query for matching
    query_l = query.lower()
    hard_matches = set()

    # --- Step 1: Hard string + fuzzy match (exact only) ---
    # Exact name or compact name match
    for i, name in enumerate(names):
        nc = name.lower().replace(" ", "")
        if name.lower() in query_l or nc in query_l:
            hard_matches.add(i)

    # Fuzzy match acronyms/variants, but ignore tiny words (<4 chars)
    shorts = [n.replace(" ", "").lower() for n in names]
    for word in re.findall(r"\w+", query_l):
        if len(word) < 4:
            continue
        match = get_close_matches(word, shorts, cutoff=0.85)
        if match:
            hard_matches.add(shorts.index(match[0]))

    # If any hard matches, return only those
    if hard_matches:
        if debug:
            print(f"🔍 Hard Match for: '{query}'")
        final = hard_matches
    else:
        # --- Step 2: SBERT top‑k fallback ---
        query_vec = sbert_model.encode(query, convert_to_tensor=True)
        cos_scores = util.pytorch_cos_sim(query_vec, corpus_embeddings)[0]

        # If the best SBERT score is too low, treat as irrelevant
        top_score = float(cos_scores.max())
        if top_score < 0.45:
            if debug:
                print("❌ Top SBERT score below threshold; no match.")
            return []

        # Otherwise pick top‑2 SBERT matches above threshold
        top_k = 2
        top_scores = torch.topk(cos_scores, k=top_k)
        sbert_matches = {
            int(idx)
            for idx, score in zip(top_scores[1], top_scores[0])
            if float(score) >= 0.45
        }

        if sbert_matches:
            if debug:
                print(f"🧠 SBERT Match for: '{query}'")
            final = sbert_matches
        else:
            # --- Step 3: Zero‑shot fallback ---
            zshot = zero_shot_classifier(query, names, multi_label=True)
            zshot_matches = {
                names.index(label)
                for label, score in zip(zshot["labels"], zshot["scores"])
                if score >= 0.5
            }
            if not zshot_matches:
                if debug:
                    print("❌ No relevant modules detected via zero‑shot.")
                return []
            if debug:
                print(f"🤖 Zero‑Shot Match for: '{query}'")
            final = zshot_matches

    # Assemble results
    results = [
        {"name": names[i], "doc_type": modules[i]["doc_type"], "score": 1.0}
        for i in sorted(final)
    ]

    return results


# ---------- Terminal Loop ----------
if __name__ == "__main__":
    print("🔍 Module Detector Terminal (type 'exit' to quit)")
    while True:
        user_input = input("\nEnter your query: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        results = detect_modules(user_input)
        if not results:
            print("⚠️  No modules detected.")
        else:
            print("\n✅ Matched Modules:")
            for r in results:
                print(f"- {r['name']} ({r['doc_type']})")

