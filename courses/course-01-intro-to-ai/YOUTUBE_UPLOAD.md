# Course 01 · YouTube upload pack (ready to paste)

The finished lecture video is at `D:\IFC_SSD2\idaho_sae\Cambium\academy_media\Cambium-Academy-Course01-Intro-to-AI-lecture.mp4`
(16:31, 1080p, AI-narrated by an Indian English neural voice, 31 MB). It sits outside the repo on purpose: YouTube hosts the video, git should not.

## Upload steps (10 minutes)

1. youtube.com, Create, Upload videos, pick the MP4 above.
2. Paste the title, description, and tags below. Chapters are already exact for this render.
3. Visibility Public. Add to a playlist named "Cambium Academy".
4. Under "Altered content", answer Yes: the narration is AI-generated. YouTube asks this at upload; the description already discloses it too.
5. Subtitles: in the upload flow (or Studio, Subtitles), add the English caption file `Cambium-Academy-Course01-Intro-to-AI-lecture.srt` from the same academy_media folder. It is timed exactly to this render (242 cues). YouTube can then auto-translate captions into dozens of languages.
6. After publishing, copy the video ID (the part after `watch?v=`) and replace `REPLACE_WITH_VIDEO_ID` in `web/index.html`. Push and redeploy Pages.

## Title

Intro to AI: How AI Works, How It's Trained, and Which Model to Use (Free Course + Certificate)

## Description

Free beginner course from Cambium Academy. No math, no code, no signup. Learn what AI really is, how models like ChatGPT, Claude, and Gemini work, how they are trained, the July 2026 model landscape, and exactly which model to use for each job.

Take the quiz and print your free certificate: PASTE COURSE PAGE LINK HERE
Slides, resources, and all courses: PASTE ACADEMY LINK HERE

Chapters:
0:00 Welcome
1:23 Module 1 · What is AI?
3:34 Module 2 · How AI models work
6:21 Module 3 · How models are trained
8:46 Module 4 · The 2026 model landscape
12:13 Module 5 · Which model for which job
14:16 Module 6 · Using AI well
16:01 Quiz and certificate

New course every week. Cambium Academy is free forever.
Follow Cambium AI Research Institution: https://www.linkedin.com/company/cambium-ai-institute/

Note: this lecture is narrated by Amelia, Cambium Academy's AI teacher (an AI-generated voice and persona). Facts are a July 2026 snapshot; sources are listed on the course resources page.

## Tags

intro to ai, ai course, free ai course, how ai works, chatgpt explained, llm explained, ai for beginners, claude ai, gemini, ai certificate

## Re-rendering the video (any future edit)

The whole pipeline is saved in `script/render/` (narration.py, tts.py, seg.sh). Change the narration or voice there, re-run TTS and seg.sh, concat, done. Rendering is free (edge-tts neural voices + ffmpeg). To re-render with a different voice, edit the VOICE line in tts.py; samples of four candidate voices live in `script/voice-samples/`.
