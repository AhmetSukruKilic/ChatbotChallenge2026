"""Our chatbot: single-shot RAG over one index of page text and image
descriptions.

Per question: embed once, take the nearest chunks overall plus the
nearest image descriptions (so a question whose answer lives in an image
still sees one), one chat call, then clean the reply into a short
answer. Every gateway call runs against a per-question deadline, and no
failure escapes: a question that cannot be answered returns "" instead
of blanking the whole batch in main.py.
"""
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from bot.llm import CHAT_DEPLOYMENT, CHAT_URL, EMBED_DEPLOYMENT, EMBED_URL, _client
from bot.store import get_store, query

ROOT = Path(__file__).resolve().parents[1]
STORE_PATH = str(ROOT / "data" / "chroma")

CONFIG = {
    "k": 8,            # nearest chunks of any kind
    "k_image": 3,      # nearest image descriptions, added on top
    "budget_s": 25.0,  # per question, under main.py's 30s TIME_LIMIT
    "workers": 4,      # concurrent questions in rag_answer_batch
    "max_tokens": 200,
}

SYSTEM_PROMPT = """You answer quiz questions about the Tam Wing Fan Innovation Wing and the
Innovation Academy, Faculty of Engineering, The University of Hong Kong (HKU).

Use the numbered context below. Context entries marked IMAGE are descriptions of
photos and posters, including any text written in them; treat them as facts.
Where the context disagrees with what you think you know, the context is correct.
If the context does not contain the answer, answer from general knowledge.
Always give your best answer. Never say you do not know, never ask for more
information.

Reply with the shortest complete answer only: a name, number, date or short
phrase. No explanation, no preamble, no full sentence. If the question asks for
several items, list all of them. If the question asks how many, reply with a
number in digits."""

# Invented examples, not from dev_set.json: they set the format only.
FEW_SHOT = [
    ("What does CNC stand for?", "Computer numerical control"),
    ("How many seats does the Seminar Room hold?", "36"),
    ("Which two companies sponsored the 2024 Robotics Cup?", "Arcwell and Northline"),
]

NUMBER_WORDS = {w: str(i) for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}

_store = None


def _log(msg: str) -> None:
    print(f"[answer] {msg}", file=sys.stderr)


def _store_once():
    global _store
    if _store is None:
        _store = get_store(path=STORE_PATH)
    return _store


def _left(deadline: float) -> float:
    return deadline - time.time()


def _embed(texts: list[str], deadline: float) -> list[list[float]]:
    client = _client(EMBED_URL).with_options(timeout=max(1.0, min(8.0, _left(deadline))), max_retries=1)
    r = client.embeddings.create(model=EMBED_DEPLOYMENT, input=[t.replace("\n", " ") for t in texts])
    return [d.embedding for d in r.data]


def _chat(messages: list[dict], deadline: float) -> str:
    """Chat with a timeout bounded by the deadline; one retry if time allows."""
    last = None
    for _ in range(2):
        left = _left(deadline)
        if left < 2:
            break
        try:
            client = _client(CHAT_URL).with_options(timeout=min(15.0, left), max_retries=0)
            r = client.chat.completions.create(
                model=CHAT_DEPLOYMENT, messages=messages,
                temperature=0.0, max_tokens=CONFIG["max_tokens"],
            )
            return r.choices[0].message.content or ""
        except Exception as exc:                  # noqa: BLE001
            last = exc
            _log(f"chat failed: {type(exc).__name__}: {str(exc)[:120]}")
    if last:
        raise last
    raise TimeoutError("no time left for chat")


def _search(vec: list[float], k: int, where: dict = None) -> list[dict]:
    r = _store_once().query(query_embeddings=[vec], n_results=k, where=where or None)
    return [
        {"text": d, "metadata": m, "distance": dist}
        for d, m, dist in zip(r["documents"][0], r["metadatas"][0], r["distances"][0])
    ]


def retrieve(question: str, k: int = None, where: dict = None) -> list[dict]:
    """Return the k chunks most relevant to the question.

    Kept separate from rag_answer on purpose: it lets you check whether
    an answer was ever fetched at all, which is the only way to tell a
    retrieval failure from a prompt failure.
    """
    return query(_store_once(), question, k=k or CONFIG["k"], where=where)


def retrieve_vec(vec: list[float]) -> list[dict]:
    """Nearest chunks overall plus nearest image descriptions, closest first."""
    chunks = _search(vec, CONFIG["k"])
    try:
        chunks += _search(vec, CONFIG["k_image"], where={"kind": "image"})
    except Exception as exc:                      # noqa: BLE001  (no image chunks yet)
        _log(f"image search skipped: {exc}")
    seen, out = set(), []
    for c in sorted(chunks, key=lambda c: c["distance"]):
        if c["text"] not in seen:
            seen.add(c["text"])
            out.append(c)
    return out


def build_messages(question: str, chunks: list[dict]) -> list[dict]:
    blocks = []
    for i, c in enumerate(chunks, 1):
        m = c["metadata"]
        tag = "IMAGE" if m.get("kind") == "image" else "PAGE"
        blocks.append(f"[{i}] {tag} {m.get('title', '')} — {m.get('url', '')}\n{c['text']}")
    context = "\n\n".join(blocks) if blocks else "(no context retrieved)"

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for q, a in FEW_SHOT:
        messages += [{"role": "user", "content": f"Question: {q}"},
                     {"role": "assistant", "content": a}]
    messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"})
    return messages


def clean_answer(question: str, reply: str) -> str:
    raw = (reply or "").strip()
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    ans = lines[0] if lines else ""
    ans = re.sub(r"^(final answer|answer)\s*[:\-]\s*", "", ans, flags=re.I).strip()
    ans = ans.strip("*_` ").rstrip(".").strip()
    if re.match(r"\s*how many\b", question, re.I):
        m = re.search(r"\d[\d,]*(\.\d+)?", ans)
        if m:
            ans = m.group(0).replace(",", "")
        else:
            words = re.findall(r"[a-z]+", ans.lower())
            num = next((NUMBER_WORDS[w] for w in words if w in NUMBER_WORDS), None)
            ans = num or ans
    return ans or raw


def fallback_answer(question: str, chunks: list[dict]) -> str:
    """No chat (quota, outage): a crude extractive guess beats an empty
    line, which always scores 0. Counts get the first number in the top
    chunks; anything else gets the first sentence of the top chunk."""
    bodies = [c["text"].split("\n", 1)[-1] for c in chunks[:3]]
    if re.match(r"\s*how many\b", question, re.I):
        for body in bodies:
            m = re.search(r"\b\d+\b", body)
            if m:
                return m.group(0)
        return ""
    for body in bodies:
        for sentence in re.split(r"(?<=[.!?])\s+|\n", body):
            sentence = sentence.strip()
            if len(sentence) >= 3:
                return sentence[:150]
    return ""


def _answer(question: str, vec: list[float] = None, started: float = None) -> str:
    deadline = (started or time.time()) + CONFIG["budget_s"]
    chunks = []
    try:
        if vec is None:
            vec = _embed([question], deadline)[0]
        chunks = retrieve_vec(vec)
    except Exception as exc:                      # noqa: BLE001  closed book beats nothing
        _log(f"retrieval failed, answering closed book: {type(exc).__name__}: {str(exc)[:120]}")
    try:
        reply = _chat(build_messages(question, chunks), deadline)
    except Exception as exc:                      # noqa: BLE001
        _log(f"chat failed for {question!r}: {type(exc).__name__}; extractive fallback")
        return fallback_answer(question, chunks)
    return clean_answer(question, reply)


def rag_answer(question: str) -> str:
    """One question in, one answer out. Never raises."""
    return _answer(question)


def rag_answer_batch(questions: list[str]) -> list[str]:
    """Many questions in, the same number of answers out, in order.

    One embedding call for all questions, then the chat calls run
    concurrently. Each question keeps its own budget and failure.
    """
    started = time.time()
    try:
        _store_once()                             # open once, before the threads race for it
    except Exception as exc:                      # noqa: BLE001
        _log(f"store failed to open: {type(exc).__name__}: {str(exc)[:120]}")
    try:
        vecs = _embed(questions, started + CONFIG["budget_s"])
    except Exception as exc:                      # noqa: BLE001
        _log(f"batch embed failed, embedding per question: {type(exc).__name__}")
        vecs = [None] * len(questions)

    def one(i: int) -> str:
        # A question waiting in the pool starts its clock when it starts.
        return _answer(questions[i], vecs[i], time.time())

    with ThreadPoolExecutor(CONFIG["workers"]) as pool:
        return list(pool.map(one, range(len(questions))))
