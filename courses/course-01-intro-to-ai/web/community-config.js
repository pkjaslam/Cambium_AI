// One-time community setup (see PUBLISHING.md, Part C).
// 1. Enable Discussions on the GitHub repo (Settings, Features, Discussions).
// 2. Create two discussion categories: "Academy Q&A" (Q&A format) and "Academy discussion" (open-ended).
// 3. Install the giscus app on the repo, then open https://giscus.app, pick the repo and each
//    category, and copy the repoId and categoryId values it shows into the fields below.
//    The graduate wall reuses the "Academy discussion" category, so it needs no extra ID.
// 4. Push. The panels light up on the next Pages deploy. Until then the pages show a
//    friendly pending card and a direct link to the GitHub forum.
window.CAMBIUM_COMMUNITY = {
  repo: "pkjaslam/Cambium_AI",
  repoId: "",
  qa: { category: "Academy Q&A", categoryId: "", term: "course-01-qa" },
  discussion: { category: "Academy discussion", categoryId: "", term: "course-01-discussion" },
  graduates: { category: "Academy discussion", categoryId: "", term: "course-01-graduate-wall" }
};
// The graduate wall uses the same categoryId as discussion; the setup script below copies it.
if (!window.CAMBIUM_COMMUNITY.graduates.categoryId) {
  window.CAMBIUM_COMMUNITY.graduates.categoryId = window.CAMBIUM_COMMUNITY.discussion.categoryId;
}
