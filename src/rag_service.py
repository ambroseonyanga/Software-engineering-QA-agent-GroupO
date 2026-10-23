
try:
    from .console_logging import trace_operation, log_event, log_error
except ImportError:
    from console_logging import trace_operation, log_event, log_error

import configparser
import csv
import json
import urllib.error
import urllib.request
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = PROJECT_ROOT / "knowledge" / "corpus"
SOURCE_REGISTER = PROJECT_ROOT / "knowledge" / "source_register.csv"

try:
    from .model_service import MODEL, complete, load_prompt
except ImportError:
    from model_service import MODEL, complete, load_prompt

TOP_K = 3
MIN_SCORE = 0.08
CHUNK_SIZE = 180
MAX_RESPONSE_TOKENS = 400


def load_source_register():
    register = {}

    if not SOURCE_REGISTER.exists():
        return register

    with SOURCE_REGISTER.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            path = (row.get("file_path") or "").replace("\\", "/")
            register[path] = row

    return register


@trace_operation("RAG", "Load authorized corpus")
def load_documents():
    documents = []

    for row in load_source_register().values():
        if row.get("access_status") != "Authorized":
            continue
        file_path = (PROJECT_ROOT / row["file_path"].replace("\\", "/")).resolve()
        # Resolve before checking containment so symlinks cannot escape the corpus.
        if not file_path.is_relative_to(CORPUS_DIR.resolve()) or file_path.suffix != ".md":
            continue
        text = file_path.read_text(encoding="utf-8").strip()
        if not text:
            continue

        documents.append({
            "source": file_path.name,
            "path": str(file_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "text": text,
        })

    return documents


def chunk_text(text, chunk_size=CHUNK_SIZE):
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size]).strip()
        if chunk:
            chunks.append(chunk)

    return chunks


@trace_operation("RAG", "Chunk documents")
def build_chunks(documents):
    chunks = []

    for document in documents:
        for index, chunk in enumerate(chunk_text(document["text"])):
            chunks.append({
                "source": document["source"],
                "path": document["path"],
                "chunk_id": index,
                "text": chunk,
            })

    return chunks


@trace_operation("RAG", "Build retrieval index")
def build_index(chunks):
    texts = [chunk["text"] for chunk in chunks]
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
    )
    matrix = vectorizer.fit_transform(texts)
    return vectorizer, matrix


@trace_operation("RAG", "Rank evidence passages")
def retrieve(query, chunks, vectorizer, matrix, top_k=TOP_K):
    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, matrix)[0]
    ranked_indices = scores.argsort()[::-1][:top_k]

    results = []
    for index in ranked_indices:
        results.append({
            "source": chunks[index]["source"],
            "path": chunks[index]["path"],
            "chunk_id": chunks[index]["chunk_id"],
            "score": float(scores[index]),
            "text": chunks[index]["text"],
        })

    return results


def build_context(results):
    context_parts = []

    for result in results:
        context_parts.append(
            f"[Source: {result['source']} | Chunk: {result['chunk_id']}]\n"
            f"{result['text']}"
        )

    return "\n\n".join(context_parts)


def build_prompt(question, context):
    return json.dumps({"question": question, "project_excerpts": context}, ensure_ascii=False)


def ask_model(prompt):
    return complete(load_prompt("rag-answer-v1.0.txt"), prompt, max_tokens=1200)["text"]


class RagPipeline:
    def __init__(self, documents=None, register=None):
        self.register = load_source_register() if register is None else register
        self.documents = load_documents() if documents is None else documents
        self.chunks = build_chunks(self.documents)
        if not self.chunks:
            raise RuntimeError("No authorised project documents are available. Check the source register.")
        self.vectorizer, self.matrix = build_index(self.chunks)

    @trace_operation("RAG", "Ground answer")
    def answer(self, question, generate=True, top_k=TOP_K):
        results = retrieve(
            question,
            self.chunks,
            self.vectorizer,
            self.matrix,
            top_k=top_k,
        )

        grounded_results = [
            result for result in results if result["score"] >= MIN_SCORE
        ]

        for result in grounded_results:
            meta = self.register.get(result["path"], {})
            result["source_id"] = meta.get("source_id", "")
            result["authority"] = meta.get("authority", "")

        if not grounded_results:
            return {
                "question": question,
                "answer": "I could not find sufficient information in the project documentation.",
                "sources": [],
                "retrieved": results,
                "grounded": False,
            }

        context = build_context(grounded_results)
        prompt = build_prompt(question, context)

        if not generate:
            return {
                "question": question,
                "answer": "",
                "sources": grounded_results,
                "retrieved": results,
                "grounded": True,
                "prompt": prompt,
                "context": context,
            }

        answer = ask_model(prompt)
        source_lines = []
        seen = set()

        for result in grounded_results:
            key = (result["source"], result["chunk_id"])
            if key in seen:
                continue
            seen.add(key)
            source_id = result.get("source_id") or "unregistered"
            source_lines.append(
                f"- {source_id}: {result['source']} (chunk {result['chunk_id']}, score {result['score']:.3f})"
            )

        sourced_answer = answer.strip()
        if "Source:" not in sourced_answer and "source" not in sourced_answer.lower():
            sourced_answer = sourced_answer + "\n\nRetrieved context (not proof that every excerpt supports the answer):\n" + "\n".join(source_lines)

        return {
            "question": question,
            "answer": sourced_answer,
            "sources": grounded_results,
            "retrieved": results,
            "grounded": True,
            "prompt": prompt,
            "context": context,
        }


_pipeline = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = RagPipeline()
    return _pipeline


@trace_operation("RAG", "Answer knowledge question")
def answer_question(question, generate=True, top_k=TOP_K):
    return get_pipeline().answer(question, generate=generate, top_k=top_k)



def repository_binding(source_path):
    """Bind only a local Git origin represented in the authorised source register."""
    if not source_path:
        return ''
    config = configparser.ConfigParser(interpolation=None)
    try:
        config.read(Path(source_path) / '.git' / 'config', encoding='utf-8')
        origin = config.get('remote "origin"', 'url').strip().rstrip('/')
    except (OSError, configparser.Error):
        return ''
    def canonical(url):
        return url.rstrip('/').removesuffix('.git')
    for row in load_source_register().values():
        repository = row.get('origin', '').split(';', 1)[0].strip().rstrip('/')
        if row.get('access_status') == 'Authorized' and canonical(repository) == canonical(origin):
            return repository
    return ''


@trace_operation("RAG", "Build project evidence pipeline")
def project_pipeline(state):
    """Keep target-system evidence separate from the QA Agent's own requirements."""
    repository = (state.get("knowledge_repository") or repository_binding(state.get("source_path"))).rstrip("/")
    register = load_source_register()
    documents = []
    if repository:
        documents = [doc for doc in load_documents()
                     if register[doc["path"]].get("origin", "").split(";", 1)[0].rstrip("/") == repository]
    # Supplied requirements belong only to this session, and retain their provenance.
    for requirement in state.get("requirements", []):
        identifier = str(requirement.get("id", "unknown"))
        path = "session/requirements/" + identifier
        text = json.dumps(requirement, ensure_ascii=False)
        documents.append({"source": identifier, "path": path,
                          "text": "User-supplied target requirement; not independent runtime evidence. " + text})
        register[path] = {"source_id": identifier, "authority": "User-supplied target requirement"}
    if not documents:
        return None
    return RagPipeline(documents=documents, register=register)


@trace_operation("RAG", "Retrieve project corpus")
def project_corpus_context(state, question):
    """Retrieve evidence bound to this repository/session only."""
    pipeline = project_pipeline(dict(state, requirements=[]))
    if pipeline is None:
        return []
    results = retrieve(state["name"] + " " + question, pipeline.chunks, pipeline.vectorizer, pipeline.matrix)
    return [dict(item, source_id=pipeline.register[item["path"]]["source_id"])
            for item in results if item["score"] > 0]


@trace_operation("RAG", "Retrieve project evidence")
def project_retrieve(state, query, top_k=3):
    pipeline = project_pipeline(state)
    if pipeline is None:
        return {"grounded": False, "answer": "No target project evidence is available.", "sources": []}
    return pipeline.answer(query, generate=False, top_k=top_k)
