from pathlib import Path
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


CORPUS_DIR = Path("knowledge/corpus")


def load_documents():
    documents = []

    for file_path in CORPUS_DIR.glob("*.md"):
        text = file_path.read_text(encoding="utf-8")

        documents.append({
            "source": file_path.name,
            "text": text
        })

    return documents


def chunk_text(text, chunk_size=500):
    words = text.split()

    chunks = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)

    return chunks


def build_chunks(documents):
    chunks = []

    for document in documents:
        document_chunks = chunk_text(document["text"])

        for index, chunk in enumerate(document_chunks):
            chunks.append({
                "source": document["source"],
                "chunk_id": index,
                "text": chunk
            })

    return chunks


def build_index(chunks):
    texts = [chunk["text"] for chunk in chunks]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english"
    )

    matrix = vectorizer.fit_transform(texts)

    return vectorizer, matrix


def retrieve(query, chunks, vectorizer, matrix, top_k=3):
    query_vector = vectorizer.transform([query])

    scores = cosine_similarity(
        query_vector,
        matrix
    )[0]

    ranked_indices = scores.argsort()[::-1][:top_k]

    results = []

    for index in ranked_indices:
        results.append({
            "source": chunks[index]["source"],
            "chunk_id": chunks[index]["chunk_id"],
            "score": float(scores[index]),
            "text": chunks[index]["text"]
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
    prompt = f"""
You are a Software Engineering QA Assistant.

Answer the user's question using only the project documentation
provided in the context below.

If the answer cannot be found in the provided context, say:
"I could not find sufficient information in the project documentation."

Do not invent information.

PROJECT CONTEXT:
----------------
{context}

USER QUESTION:
--------------
{question}

ANSWER:
"""
    return prompt

def ask_ollama(prompt, model="qwen3:8b"):
    import requests

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "num_predict": 400,
                "num_ctx": 2048,
            },
        },
        timeout=180
    )

    response.raise_for_status()

    data = response.json()

    return data["response"]
def main():
    print("Loading corpus...")

    documents = load_documents()

    print(f"Documents loaded: {len(documents)}")

    chunks = build_chunks(documents)

    print(f"Chunks created: {len(chunks)}")

    vectorizer, matrix = build_index(chunks)

    print("Index created successfully.")

    query = input("\nEnter your question: ")

    results = retrieve(
        query,
        chunks,
        vectorizer,
        matrix
    )

    print("\nRetrieved sources:")

    for result in results:
        print(
            f"\nSource: {result['source']}"
            f"\nChunk: {result['chunk_id']}"
            f"\nScore: {result['score']:.4f}"
            f"\n{result['text'][:1000]}"
        )
    context = build_context(results)

    print("\n" + "=" * 60)
    print("CONSTRUCTED RAG CONTEXT")
    print("=" * 60)
    print(context)

    prompt = build_prompt(query, context)

    print("\n" + "=" * 60)
    print("RAG PROMPT FOR QWEN3")
    print("=" * 60)
    print(prompt)

    print("\n" + "=" * 60)
    print("QWEN3 ANSWER")
    print("=" * 60)

    answer = ask_ollama(prompt)

    print(answer)
if __name__ == "__main__":
    main()