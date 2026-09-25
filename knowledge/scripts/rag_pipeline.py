import sys
from pathlib import Path

src_dir = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(src_dir))

from rag_service import RagPipeline


def main():
    pipeline = RagPipeline()

    print("Loading corpus...")
    print(f"Documents loaded: {len(pipeline.documents)}")
    print(f"Chunks created: {len(pipeline.chunks)}")
    print("Index created successfully.")

    query = input("\nEnter your question: ")
    result = pipeline.answer(query)

    print("\nRetrieved sources:")

    for item in result["retrieved"]:
        print(
            f"\nSource: {item['source']}"
            f"\nChunk: {item['chunk_id']}"
            f"\nScore: {item['score']:.4f}"
            f"\n{item['text'][:1000]}"
        )

    print("\n" + "=" * 60)
    print("GROUNDED ANSWER")
    print("=" * 60)
    print(result["answer"])


if __name__ == "__main__":
    main()
