# Week 3 Progress Record

Project: Software Engineering QA Agent
Group: Group O
Week ending: 18 September 2026

## Status

Week 3 introduced retrieval-augmented generation so project questions can be answered from controlled project evidence rather than only from model memory. The project corpus is maintained in `knowledge/corpus`, and provenance is recorded in `knowledge/source_register.csv`.

The RAG implementation in `src/rag_service.py` loads the controlled Markdown records, splits them into 180-word chunks, builds a TF-IDF index with cosine-similarity ranking, retrieves the top matching chunks and adds source labels to model context. The Flask application exposes the grounded project-question workflow and displays source information with the answer.

## Week 3 deliverables completed

- Controlled corpus and source register.
- RAG architecture diagram at `docs/architecture/rag-architecture.png`.
- Working RAG pipeline with source grounding in `src/rag_service.py`.
- 15-case RAG evaluation evidence in `docs/evaluation` and `evidence/traces`.
- Week 3 progress report in `docs/weekly-reports`.

## Difference between Week 2 and Week 3

Week 2 established the baseline model-backed capability: local Qwen3 8B deployment, prompt specifications, prompt versioning and a 10-case prompt evaluation. Week 3 added the controlled corpus, provenance register, document chunking, TF-IDF retrieval, source-grounded answers and a 15-case RAG evaluation. In short, Week 2 tested the model's baseline QA reasoning, while Week 3 tested whether answers can be grounded in authorised project evidence.

## Known limitations

The controlled corpus contains only authorised project material. When relevant information is absent, the correct response is to state that the project documentation is insufficient rather than inventing an answer. Retrieval and grounding behaviour is measured in the RAG evaluation evidence.
