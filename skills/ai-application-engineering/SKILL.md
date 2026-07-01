---
name: ai-application-engineering
description: Design and build LLM and AI features correctly: RAG pipelines, agent loops, tool use, evals, prompt-injection defense, and cost and latency budgets. Use when the user wants to add AI to an application, build a chatbot or assistant, set up retrieval-augmented generation, implement an agent with tool calls, write offline evals, or add guardrails to an LLM feature. Trigger on "RAG", "embeddings", "vector search", "LangChain", "LlamaIndex", "LangGraph", "agent", "tool use", "function calling", "prompt injection", "guardrails", "evals", "LLM pipeline", "AI feature", "chatbot", "retrieval", "reranking", "pgvector", "Chroma", "Milvus". Pairs with backend-api-design (for the API layer) and databases-and-data-modeling (for the vector store and persistence layer). Honest: this encodes engineering patterns, not model behavior guarantees; evals and a human reviewer are always required; this is not a safety certification.
---

# AI application engineering: ship AI features that actually work

The job is not to call the LLM. The job is to build a system where the LLM produces reliable, verifiable
output, within a cost and latency budget, and that degrades gracefully when it is wrong. Start from the
simplest pipeline that satisfies the eval, not the most impressive framework.

Encode the patterns below, not the library calls. LangChain (~140k GitHub stars at time of writing),
LlamaIndex (~49k at time of writing), and LangGraph all move fast and break APIs between minor versions.
Version-pin everything, write against the pattern rather than the convenience wrapper, and expect to
update import paths on upgrades.

## RAG pipeline anatomy

A retrieval-augmented generation pipeline has five stages; get all five right or the whole thing regresses.

| Stage | What to do | Common failure |
|---|---|---|
| Chunking | Split at semantic boundaries (paragraph, section) not character count; keep metadata (source, page, date) on every chunk. | Chunks that cut mid-sentence destroy retrieval recall. |
| Embedding | Use a consistent model throughout (same model for indexing and query); sentence-transformers/all-MiniLM-L6-v2 is a widely adopted open-source model with good general-purpose performance; OpenAI text-embedding-3-small is the cheapest hosted option. | Mixing models breaks cosine similarity silently. |
| Retrieval | Top-k cosine similarity is a floor; add a keyword (BM25) pass and merge results (hybrid search). | Pure dense retrieval misses exact-match terms like IDs, acronyms, and proper nouns. |
| Reranking | Run a cross-encoder (Cohere Rerank, BGE-reranker, or Flashrank for local) on the top 20 to 50 candidates; return the top 5 to 10 to the prompt. | Sending 50 chunks into context buries the good answer and inflates cost. |
| Generation | Cite the retrieved chunks in the prompt; instruct the model to say "I don't know" if the context is insufficient. | Grounding skipped, so the model confabulates. |

```python
# Minimal hybrid retrieval pattern (pseudo-code, not a library call)
dense_hits  = vector_store.search(query_embedding, top_k=50)
sparse_hits = bm25_index.search(query_text, top_k=50)
candidates  = reciprocal_rank_fusion(dense_hits, sparse_hits)
reranked    = cross_encoder.rerank(query_text, candidates, top_n=8)
context     = format_chunks(reranked)
answer      = llm.complete(system_prompt, context, user_query)
```

## Vector stores: choose by deployment constraint

| Store | Best fit |
|---|---|
| pgvector (PostgreSQL extension) | Already using Postgres; simple ops; HNSW index covers most scales. |
| Chroma | Local dev and prototyping; no infrastructure; in-memory or file-backed. |
| Milvus (~42k stars at time of writing) | High-scale production; billions of vectors; separate infrastructure justified. |

## Agents and tool use

An agent is a loop: plan, call a tool, observe the result, repeat. Keep loops short, bounded, and logged.

- Define tools as typed schemas (OpenAI function-calling format or Anthropic tool use); validate inputs before execution.
- Set a maximum turn limit and a timeout; an unbounded loop is a cost and reliability hazard.
- Log every tool call and result; observability is mandatory when debugging a multi-step run.
- Prefer deterministic tools (search, code execution, database reads) over letting the model invent actions.
- LangGraph is the clearest way to express a stateful multi-step graph with retries and branching without hiding control flow.

## Evals: offline test sets are not optional

You cannot ship an LLM feature without measuring it. An "it looked good in the demo" story is not enough.

- Build a golden dataset: 50 to 200 question-answer pairs with known correct answers, sourced from real use cases.
- Score automatically where possible: exact match, ROUGE, BERTScore, or an LLM-as-judge call on a separate model.
- Track metrics per release; regression on the eval set is a blocking signal.
- Use RAGAS (ragas.io) for RAG-specific metrics: faithfulness, answer relevancy, context precision.

## Prompt-injection defense and guardrails

- Never concatenate raw user input directly into a system prompt; keep system instructions and user content in separate roles.
- Validate and strip known injection patterns (e.g., "Ignore previous instructions") with a classification pass or a regex blocklist before the main call.
- Use Guardrails AI (guardrailsai.com) or NeMo Guardrails (github.com/NVIDIA/NeMo-Guardrails) for structured output validation and off-topic blocking.
- Apply output validation: if the response must be JSON, parse and reject malformed output rather than passing it downstream.

## Cost and latency budgets

- Pick the smallest model that passes the eval; GPT-4o is not always the answer.
- Cache embedding lookups and frequent retrievals; semantic caching (GPTCache, Redis) can meaningfully reduce costs on repetitive queries.
- Stream responses to users; a 2 s first-token is tolerable, a 20 s full response is not.
- Log token counts per call; set a hard ceiling and return a graceful error if exceeded.

## Human-in-the-loop

For any action with real-world consequences (sending an email, writing a file, calling an external API),
pause and show the proposed action to the user before executing. Cambium never deploys to production, moves
money, or holds secrets on the user's behalf. The human reviews and runs.

## Honest guardrails

- Evals and a human reviewer are required before shipping; this skill cannot certify correctness or safety.
- Framework APIs move fast: pin LangChain, LlamaIndex, and LangGraph to a minor version and read the changelog before upgrading.
- LLM behavior is non-deterministic; set temperature to 0 and seed where the API supports it for more stable evals, but expect variation.
- Do not store user secrets (API keys, credentials) in prompt history or logs; scrub before writing.

## Attribution and sources

Patterns drawn from public documentation and research: LangChain (python.langchain.com), LlamaIndex (docs.llamaindex.ai),
LangGraph (langchain-ai.github.io/langgraph), pgvector (github.com/pgvector/pgvector), Chroma (docs.trychroma.com),
Milvus (milvus.io/docs), RAGAS (ragas.io), Guardrails AI (guardrailsai.com), NeMo Guardrails
(github.com/NVIDIA/NeMo-Guardrails), sentence-transformers (sbert.net), Flashrank (github.com/PrithivirajDamodaran/FlashRank),
GPTCache (github.com/zilliztech/GPTCache), OpenAI function calling (platform.openai.com/docs/guides/function-calling),
Anthropic tool use (docs.anthropic.com/en/docs/tool-use). Reciprocal rank fusion: Cormack et al., 2009.
