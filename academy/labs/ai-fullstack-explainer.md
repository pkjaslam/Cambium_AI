# What is AI full-stack development?

If you already build web apps, you are closer to AI engineering than you think. An AI app is a normal web app (frontend, backend, database) with three new layers added on top: a model layer, a retrieval layer, and an orchestration layer. Here is the key insight up front: a strong model still matters, but much of the competitive advantage sits in retrieval (what context you give the model) and orchestration (how you coordinate the work).

## The 7 layers

Think of the stack like a sandwich. You already know the bread; the new filling is in the middle.

1. **Frontend/UX.** React or Next.js, often using the Vercel AI SDK. The big new skill here is streaming: tokens arrive word by word, so your UI renders them as they come rather than waiting for a full response.

2. **Backend/API.** FastAPI (Python) or Node/Hono, deployed serverless. Looks like a normal REST backend. The difference is that instead of querying a database, your endpoint calls a model API.

3. **Model/Inference.** This is where the AI actually runs. You can use hosted APIs (OpenAI, Anthropic, Google) billed per token, or self-hosted open models via Ollama locally or vLLM in production. "Inference" just means running the model on your input to get output.

4. **Orchestration.** Libraries like LangGraph, LlamaIndex, or CrewAI. A core pattern is the ReAct loop: the model thinks, picks a tool to call, observes the result, and repeats until done. MCP (Model Context Protocol) is an emerging open standard for wiring tools to a model, though provider function-calling APIs are still the common mechanism today.

5. **Retrieval/RAG.** Retrieval-Augmented Generation solves the most common beginner frustration: "the model doesn't know my data." You convert your documents to embeddings (vectors that capture meaning), store them in a vector database like Pinecone, pgvector, or Chroma, then retrieve the most relevant chunks at query time and paste them into the prompt. The model now "knows" your data without retraining.

6. **Evaluation, observability, and guardrails.** Tools like LangSmith, Langfuse, or Phoenix trace every call, score output quality, and track cost and latency. Without this layer you are flying blind.

7. **Deployment/infra.** Docker, GPU-friendly serverless platforms like Modal or RunPod, and standard clouds. Same as any backend, with the added concern of GPU availability and model loading time.

## How a request actually flows

User types a message, the frontend streams it to your backend, the backend hands it to the orchestration layer, which assembles context (maybe running a RAG retrieval first), calls any tools, then sends everything to the model through a gateway. The model streams tokens back up the chain to the user's screen. Every step can emit traces. Your cost and latency come down to three things: how many tokens you use, which model tier you pick (cheap/fast vs. expensive/smart), and how many retries you need.

## What to learn first

Start with tokens and prompting (system prompt = role and rules, user prompt = the actual request). Then learn RAG, because it unlocks your own data. Then learn tool/function calling, because that is what makes an agent actually useful. Streaming comes naturally once you try the Vercel AI SDK.

## Go deeper

- https://roadmap.sh/ai-engineer (visual map of the whole field)
- https://ai-sdk.dev/docs/introduction (Vercel AI SDK, hands-on for web developers)
- https://www.freecodecamp.org/news/ai-engineering-roadmap/ (free plain-language overview)
