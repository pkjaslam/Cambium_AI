# Course 01 · Intro to AI · Video narration script

One narration block per slide. Read it as written or riff on it; the same text is embedded in the deck as speaker notes, so you can record straight from PowerPoint's Presenter View.

Target length: 16 to 19 minutes. Pace: talk to one curious friend, not an auditorium. Pause one beat after each big number.

## Recording setup (10 minutes, one time)

1. Open the deck in PowerPoint: `slides/Cambium-Academy-Course01-Intro-to-AI.pptx`
2. Slide Show menu, then "Record Slide Show". PowerPoint captures your voice (and webcam if you want) over the slides.
3. Speak each slide's block below, click through, and stop. Re-record any single slide by opening Record on that slide.
4. File, Export, Create a Video, 1080p. That MP4 is your YouTube upload.
5. Prefer OBS or Clipchamp? Full-screen the PDF in `slides/` and record the screen the same way.

Microphone beats camera. Any quiet room and a phone headset already sounds fine.

---

## Narration

**Slide 1 · Title**
Welcome to Cambium Academy. This is Course 1, Intro to AI. In about an hour you will understand what AI actually is, how models like ChatGPT and Claude work under the hood, how they are trained, and which model to pick for any job. Everything is free, there is a quiz at the end, and you earn a certificate when you pass.

**Slide 2 · Built for beginners**
Quick promise before we start. You need no math, no programming, and no prior AI knowledge. A browser, about ninety minutes, and zero dollars. That is the whole entry fee.

**Slide 3 · Five outcomes**
Here is the deal we are making. By the end you can explain AI simply, picture what happens inside a model, describe how models get trained, name the major models of 2026, and choose the right one for any task you actually have.

**Slide 4 · Course map**
The route we will take. Six short modules, about an hour. Watching this lecture is step one of your path. After it, the flashcards and the hands-on AI Lab unlock the quiz. Pass at seventy percent and your certificate prints immediately. No account, no email, no payment.

**Slide 5 · Module 1 divider**
Module one. Let us pin down what artificial intelligence actually means, because the term gets thrown around loosely.

**Slide 6 · AI in one sentence**
Here is the whole idea in one sentence. AI is software that learns patterns from examples and uses them to make useful guesses about new things. Compare that with traditional software, where a person writes every rule by hand. With machine learning you show the computer a million examples and it works out the rules itself.

**Slide 7 · The family tree**
These four terms get mixed up constantly, so here is the family tree. AI is the broadest term. Machine learning is the approach that dominates today. Deep learning is machine learning built on many-layered neural networks. And generative AI, the newest child, is deep learning that creates things: text, images, audio, video. ChatGPT, Claude, and Gemini all live in that innermost circle.

**Slide 8 · Seventy-five years**
AI research started in the nineteen fifties, so the field is older than the internet. Deep Blue beat Kasparov in ninety-seven. Deep learning took off in twenty twelve. Then in twenty seventeen Google published the transformer architecture, and that single invention set up the ChatGPT moment of twenty twenty-two. Today AI assistants sit in about a billion pockets. The technology is old. The scale is new.

**Slide 9 · Already everywhere**
One more reframe before we go deeper. You already use AI every day. Spam filters, phone cameras, map routing, autocomplete, recommendations, voice assistants. All machine learning. Chatbots are just the newest and chattiest face of a technology you have trusted for years.

**Slide 10 · Module 2 divider**
Module two. Time to open the hood. No math, I promise. Just three ideas: prediction, tokens, and attention.

**Slide 11 · Predict the next word**
Everything a chatbot does comes from one trick: predict the next word. The capital of France is, blank. Paris, ninety-seven percent. Predict a word, append it, predict again, thousands of times. To get really good at this game on trillions of words, the model is forced to absorb grammar, facts, and reasoning patterns. Essays and code emerge from that single skill.

**Slide 12 · Tokens**
Models do not see words or letters. Text gets chopped into tokens, chunks of roughly three quarters of a word, and each token becomes a number. Two things follow. Models have a token budget called the context window. And tokens are the currency of AI: pricing and speed are measured in them.

**Slide 13 · Billions of dials**
Inside the model is a neural network. Picture columns of tiny dials, billions of them, each holding one number called a weight. Training works like this: the model guesses, the guess is scored, and every dial gets a microscopic nudge so the right answer comes out stronger next time. Repeat trillions of times and fluency emerges. Nobody hand-writes any rules.

**Slide 14 · The transformer**
In twenty seventeen Google researchers published a design called the transformer, built on a mechanism called attention. Every word learns which other words to pay attention to. The trophy did not fit in the suitcase because it was too big. Attention correctly links "it" to "trophy". And because transformers read everything in parallel, training on internet-scale data became practical. That is the T in GPT.

**Slide 15 · Context window**
A model's working memory is its context window, measured in tokens. Typical models hold a couple hundred thousand tokens, about a novel. Claude and Gemini offer million-token tiers. Meta advertises ten million on Llama 4 Scout, though independent testing finds about half of that reliably usable. Practical tip: when the window fills, the oldest content silently falls out. If a long chat gets forgetful, start fresh.

**Slide 16 · Module 3 divider**
Module three. Where does a model actually come from? The recipe has four steps, and you can summarize it as: read everything, learn the job, learn manners.

**Slide 17 · The recipe**
Four steps. Gather trillions of words. Pretrain by playing predict-the-next-token on all of it, which builds a brilliant autocomplete that knows language and facts but has no manners. Then fine-tune it on example conversations so it follows instructions. Finally, human feedback: real people rank candidate answers and the model learns what helpful, honest, and safe look like.

**Slide 18 · The price tag**
Pretraining is the expensive part. Months of continuous compute, tens of thousands of specialized chips, and estimated costs above a hundred million dollars for a single frontier run. That is why only a handful of labs play at this level. But the efficiency race is real: in twenty twenty-six, open models like DeepSeek V4 deliver near-frontier results at roughly a tenth of the serving cost.

**Slide 19 · Before and after**
Here is why the polishing steps matter. Ask a raw base model how to bake bread and it may reply, "asked Jim, who had baked for years." It is not being rude. It is autocompleting, because that is all it knows. After fine-tuning and human feedback, the same network answers the question, declines harmful requests, and admits uncertainty. That finishing school is why chatbots feel like assistants.

**Slide 20 · Hallucination**
Now the most important limitation. A language model always produces the most plausible next words. Plausible is not the same as true. When it hits a gap in its knowledge, it fills the gap smoothly, sometimes inventing names, dates, and citations. This is called hallucination. Search and reasoning features reduce it, but nothing eliminates it. So carry one rule out of this course: trust, but verify.

**Slide 21 · Module 4 divider**
Module four, the tour of who makes what in July twenty twenty-six. One warning: this is the fastest-moving slide in the deck. Names change monthly. The two philosophies do not.

**Slide 22 · Closed or open**
Every model you meet falls on one side of a line. Closed weights: you use it as a service and the recipe stays secret. GPT, Claude, Gemini. Open weights: you can download the actual model and run it on your own machine. Llama, DeepSeek, Qwen, Mistral. Closed usually buys polish and peak performance. Open buys freedom, privacy, and zero cost. Both philosophies are thriving in twenty twenty-six.

**Slide 23 · The frontier three**
The frontier three in the United States. OpenAI ships GPT 5.5, with 5.6 rolling out this month, the most used AI on the planet. Anthropic's Claude is prized for careful long-form work and coding, and its new Sonnet 5 just became the free default. Google's Gemini is woven through Search, Docs, and Gmail and gives away the broadest free tier. All three are excellent for everyday use.

**Slide 24 · More heavyweights**
Four more heavyweights. Meta surprised everyone by making its new flagship, Muse Spark, closed weight, while keeping the open Llama 4 line alive, free inside WhatsApp and Instagram. Grok from xAI taps live X data. DeepSeek proved open models can match the frontier at a tenth of the cost. And Mistral carries the flag for Europe with the largest fully open Western model.

**Slide 25 · The open-weights wave**
The open-weights wave is led from Asia right now. Alibaba's Qwen family comes in every size. Moonshot's Kimi is a trillion-parameter coding favorite. And GLM 5.2 is MIT licensed with a million-token window. One honest caveat: their hosted apps fall under Chinese data rules, so for sensitive work, download the weights and run them locally instead.

**Slide 26 · Four numbers**
Four numbers to feel the scale. The ChatGPT app passed a billion monthly users in June, the fastest app in history to get there. Gemini passed nine hundred million. One Google image tool generated five billion images in about two months. And Anthropic was valued at nearly a trillion dollars in May. This is why every industry is paying attention.

**Slide 27 · On your own computer**
Because open weights exist, you can run a real model on your own computer. Install a free app called Ollama, pick a small model like Qwen 3, and you have a private assistant that works offline and costs nothing. Honest trade-off: local models are clearly weaker than the frontier ones. Ideal for private material and learning, not for your hardest problems.

**Slide 28 · Module 5 divider**
Module five, the practical payoff. People ask which AI is best. Wrong question. The right question is: best for what? Here is the cheat sheet.

**Slide 29 · Cheat sheet, part 1**
Part one, the word-and-work jobs. Everyday writing: ChatGPT's free tier is excellent, and many prefer Claude's more natural writing voice. Coding: Claude leads, with DeepSeek and Kimi as strong free options. Research with sources: Perplexity cites as it answers, and Gemini's Deep Research writes full reports. Long documents: reach for the million-token models, Claude or Gemini.

**Slide 30 · Cheat sheet, part 2**
Part two, media and privacy. Images: Google's Nano Banana tool is free and shockingly good, with Midjourney the paid pick for art direction. Video: Veo 3.1 leads on quality, Kling on price. Voice: ElevenLabs. Privacy: run Qwen or Gemma locally through Ollama. And if you just want one free pick, Gemini's free tier is the broadest today, with ChatGPT right behind.

**Slide 31 · Four questions**
When in doubt, four questions beat any leaderboard. Is the data sensitive? Go local, or use a plan with training turned off. Need sources you can check? Use a citing research tool. Is the input huge? Big context model. Otherwise, honestly, any of the big three free tiers is excellent. And the best advice in this whole course: pick one model and learn it deeply. Skill compounds. Tool-hopping does not.

**Slide 32 · Module 6 divider**
Last module. You now know how these systems work. Let us close with how to use them well, because the difference between an AI power user and everyone else is habits, not access.

**Slide 33 · Five golden rules**
Five habits separate power users from everyone else. Verify before you rely. Guard private data. Keep the judgment yourself; AI accelerates, but you decide. Disclose AI help where it matters. And reassess monthly, because models leapfrog each other all the time. None of these require technical skill. All of them require discipline.

**Slide 34 · Four moves**
A parting gift and a teaser for next week. Most prompt advice fits in four moves. Give the AI a role. Give it context. State the task precisely. And say what format you want back. That one habit doubles the quality of answers from any model. Course 2, Prompting Essentials, goes deep on this next week.

**Slide 35 · Keep learning**
If this course lit a spark, here is where to go next, all free and all verified by hand this month. CGP Grey for a five-minute mental model. Karpathy's one-hour intro. 3Blue1Brown for gorgeous visuals. Elements of AI and AI for Everyone for structured courses. The links live on the course resources page.

**Slide 36 · Closing**
That is the lecture, step one of your path, done. Two short steps remain before the quiz unlocks: clear all twenty-four flashcards, and explore the three stations in the AI Lab. Then the quiz opens: twenty questions, fourteen to pass, and your certificate prints on the spot, ready for LinkedIn. Next week, Course 2, Prompting Essentials. I will see you there.

---

## YouTube upload block (copy-paste)

**Title:** Intro to AI: How AI Works, How It's Trained, and Which Model to Use (Free Course + Certificate)

**Description:**

Free beginner course from Cambium Academy. No math, no code, no signup. Learn what AI really is, how models like ChatGPT, Claude, and Gemini work, how they are trained, the July 2026 model landscape, and exactly which model to use for each job.

Finish the path (flashcards + hands-on AI Lab unlock the quiz) and print your free certificate: PASTE COURSE PAGE LINK HERE
Slides, resources, and all courses: PASTE ACADEMY LINK HERE

Chapters:
0:00 Welcome
1:29 Module 1 · What is AI?
3:39 Module 2 · How AI models work
6:27 Module 3 · How models are trained
8:52 Module 4 · The 2026 model landscape
12:19 Module 5 · Which model for which job
14:21 Module 6 · Using AI well
16:07 Quiz and certificate

New course every week. Cambium Academy is free forever.

(Adjust chapter times to your actual recording before publishing.)

**Tags:** intro to ai, ai course, free ai course, how ai works, chatgpt explained, llm explained, ai for beginners, claude ai, gemini, ai certificate

**Playlist:** Cambium Academy · Visibility: Public · License: Standard YouTube
