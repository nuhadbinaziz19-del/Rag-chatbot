# Evaluation

1. Upload a real PDF through the API (or UI) and note its `document_id` and your `user_id`.
2. Write 15-30 questions in a JSON file shaped like `questions.json`, based on that document's actual content
   (mix Bangla and English; include a few genuinely hard/ambiguous ones).
3. Run:
   ```bash
   cd backend
   python eval/run_eval.py eval/questions.json --document-id 1 --user-id 1 --generate-answers
   ```
4. Report the printed **doc-hit** / **keyword coverage** numbers on your CV/README, e.g.
   "92% top-5 retrieval accuracy across 30 bilingual questions."
5. Re-run after any change to chunk size, embedding model, or `USE_RERANKER` to see the effect.

Retrieval metrics (doc/page hit, keyword coverage) are computed automatically. Free-text answer quality
still needs a human skim, since exact-match grading of natural-language answers is unreliable — that's why
`--generate-answers` just prints them rather than auto-scoring them.
