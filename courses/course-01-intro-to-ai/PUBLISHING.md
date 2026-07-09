# Publishing Course 01 (YouTube + GitHub Pages, both free)

Two channels, one afternoon. Do Part A once for the whole Academy; Part B repeats for every course.

## Part A · Put the course site live on GitHub Pages (one-time)

The repo's existing Pages workflow (`.github/workflows/pages.yml`) already publishes the entire repository, so the course pages ride along automatically.

1. Commit and push the `courses/` folder (use `push_cambium.bat` as usual).
2. Confirm the repo setting once: Settings, then Pages, then Source = "GitHub Actions". (Already set if the landing page is live.)
3. Trigger a deploy: either publish a Release, or open Actions, pick "Deploy to GitHub Pages", and press "Run workflow".
4. Wait for the green check, then open:
   `https://pkjaslam.github.io/Cambium_AI/courses/course-01-intro-to-ai/web/`
5. Click through: slides, quiz (try passing and failing), certificate print preview. Everything runs in the browser; there is no backend to configure.

## Part B · Publish the lecture on YouTube

**Shortcut: the video is already rendered.** An AI-narrated 16:31 lecture (Neerja Expressive voice) is ready at `D:\IFC_SSD2\idaho_sae\Cambium\academy_media\`, with exact chapters and a paste-ready description in [YOUTUBE_UPLOAD.md](YOUTUBE_UPLOAD.md). Upload it, mark it as AI-altered content when YouTube asks, paste the video ID into `web/index.html`, and skip the recording steps below.

Prefer your own voice instead? Record it yourself:

1. Open `slides/Cambium-Academy-Course01-Intro-to-AI.pptx` in PowerPoint.
2. Slide Show, then "Record Slide Show". Narrate each slide from `script/VIDEO_SCRIPT.md` (the same text is in the speaker notes). Expect 16 to 19 minutes; re-record any slide you stumble on.
3. File, Export, "Create a Video", 1080p. PowerPoint renders an MP4.
4. Upload to YouTube (a channel is free): paste the ready-made title, description, chapters, and tags from the "YouTube upload block" at the bottom of VIDEO_SCRIPT.md. Fix the chapter timestamps to match your actual recording.
5. In the description, replace the two PASTE links with the course page URL from Part A.
6. Copy the YouTube video ID (the part after `watch?v=`) and paste it into `web/index.html`, replacing `REPLACE_WITH_VIDEO_ID`. Commit, push, redeploy Pages (step A3).
7. Add the video to a public "Cambium Academy" playlist so weekly courses stack up in order.

## Part C · Turn on the community boards (one-time, 10 minutes)

The community page (`web/community.html`) ships with an AI teaching assistant that works immediately, plus a Q&A board and a discussion space powered by GitHub Discussions through giscus (free, no server, no ads; learners sign in with a free GitHub account, readers need nothing).

1. On github.com/pkjaslam/Cambium_AI: Settings, General, Features, tick "Discussions".
2. In the new Discussions tab, create two categories: "Academy Q&A" (format: Q&A) and "Academy discussion" (format: open-ended).
3. Install the giscus app on the repo: github.com/apps/giscus.
4. Open giscus.app, select the repo and the "Academy Q&A" category, and copy the `data-repo-id` and `data-category-id` values it shows. Repeat with "Academy discussion" for its category id.
5. Paste the three values into `web/community-config.js`, push, redeploy Pages.

Until this is done, the community page shows a friendly note and links learners straight to the repo's Discussions tab, so nothing looks broken.

## Part D · Amelia's live chat (optional, 15 minutes)

Amelia can answer learners directly on the site through the university's MindRouter cluster, via a free Cloudflare Worker that keeps the API key server-side. Full steps, security rules, and quota math: [proxy/AMELIA_CHAT_SETUP.md](proxy/AMELIA_CHAT_SETUP.md). Until it is configured, her "Ask me anything" falls back to the community flow and nothing looks broken.

## The engagement loop (already built, know it exists)

Learners see a progress bar on the course home, hit a two-question checkpoint after every module in the web slides, drill flashcards, play with the hands-on AI playground, and finish with the quiz. Passing unlocks the certificate page with an "Add to LinkedIn profile" button (prefilled with Cambium AI Research Institution as issuer) and a downloadable share image, then invites them to post on the graduate wall. Every certificate on LinkedIn is free marketing; every wall post is social proof. A monthly async AMA keeps the human heartbeat with zero live pressure: on the first Monday of each month, pin a new thread titled "AMA · Month Year" in the Academy Q&A category and answer posts during the week. Five thoughtful answers a month is plenty.

Two more weekly rituals, five minutes each: every Monday pin a "Cohort · week of Month Day" thread in the discussion category (learners introduce themselves and aim to finish by Sunday), and once a month feature the best capstone write-up from the project gallery in the AMA thread. The capstone brief, rubric, and gallery link live at `web/capstone.html`; the career guide at `web/career.html` teaches graduates to put the certificate on their resume and LinkedIn, which is where new learners come from.

## Spreading it (all free)

Share the course page link and the YouTube link on LinkedIn, X, Facebook groups, and relevant subreddits (r/learnmachinelearning and r/artificial allow free course posts; read each community's rules first). Pin a "new course every week" comment under the video. The certificate is a genuine share hook: invite learners to post it and tag the Academy.

## Weekly rhythm (every new course)

Build from `courses/_templates/COURSE_TEMPLATE.md`, then repeat Part B, add a card to the catalog table in `courses/README.md`, and redeploy. Part A never needs doing again.

## Zero-cost checklist

GitHub Pages hosting: $0. YouTube hosting: $0. Quiz and certificate: static browser pages, $0, no accounts, no data collected. The only investment is your recording voice and one push.
