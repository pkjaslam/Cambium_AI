# Amelia live chat setup (MindRouter + Cloudflare Worker, ~15 minutes, $0)

Amelia's live chat lets learners talk to her directly on the course site, powered by the
University of Idaho MindRouter cluster. The architecture keeps your API key safe:

```
Learner's browser  ->  Cloudflare Worker (holds the key as a secret)  ->  MindRouter
```

The course site is public on GitHub Pages, so the key can NEVER appear in any file in this
repo. Anyone can read a public site's source. The worker is the locked box.

## Before you start: two responsibilities

1. **Rotate your key.** The key you shared in chat should be treated as exposed. In the
   MindRouter dashboard (mindrouter.uidaho.edu/dashboard), create a fresh API key for this
   purpose and deactivate the old one. Use the NEW key below, and never paste it anywhere
   except the Cloudflare secret field.
2. **Confirm acceptable use.** MindRouter is a shared research cluster (RCDS/IIDS, Luke
   Sheneman's group). A public course chatbot sends public traffic to it. Send Luke a
   two-line note describing the use and expected volume before going live. Your current
   quota ("other" group) is 100,000 tokens and 30 requests/minute; a typical Amelia answer
   costs ~120-180 tokens, so the budget covers roughly 600-800 answers before you need a
   quota increase (Dashboard, Request Quota).

## Deploy the worker (one time)

1. Create a free account at dash.cloudflare.com (no domain needed).
2. Workers & Pages, Create, Create Worker. Name it `amelia-chat`. Deploy the hello-world.
3. Click "Edit code", replace everything with the contents of `amelia-worker.js` (next to
   this file), then Deploy.
4. Worker Settings, Variables and Secrets, add:
   - `MR_API_KEY` (type: Secret) = your NEW MindRouter key
   - `MR_BASE_URL` (type: Text) = `https://mindrouter.uidaho.edu`
   - `MR_MODEL` (type: Text) = `default-llm-small`
   - `ALLOW_ORIGIN` (type: Text) = `https://pkjaslam.github.io`
5. Copy the worker URL, e.g. `https://amelia-chat.YOURNAME.workers.dev`.

## Point the site at it

1. Open `web/amelia-chat-config.js` and set:
   `endpoint: "https://amelia-chat.YOURNAME.workers.dev"`
2. Push and redeploy Pages. Done. Amelia's "Ask me anything" now answers in the widget
   on every page, in her own bubble, with her voice.

While the endpoint is empty, nothing is broken: Amelia falls back to the community page
flow (opening the question in a free chatbot).

## Built-in protections

The worker only accepts POSTs from your site's origin, clamps conversations to the last
6 short messages, caps answers at 1,500 tokens, enforces a best-effort 8 requests/minute
per visitor IP, keeps Amelia's system prompt server-side, and never exposes the key or
MindRouter's address to the browser. MindRouter's own 30 RPM limit on the key is the hard
backstop. If the daily budget runs out, learners see a polite "class is busy" note and the
community page still works.

## Local test (optional)

After deploying, test from any terminal:

```
curl -X POST https://amelia-chat.YOURNAME.workers.dev \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"What is a token?"}]}'
```

You should get `{"reply":"...","usage":{...}}` back in a few seconds.
