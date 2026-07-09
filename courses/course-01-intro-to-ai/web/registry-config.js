// Learner registry (optional). When endpoint is set, each issued certificate quietly
// registers {name, org, email, certId, date, score} to YOUR private Google Sheet so
// learners can recover certificates and you can see how many students you have.
// Setup: ../REGISTRY_SETUP.md (10 minutes, free). Leave empty to disable; nothing breaks.
// NEVER put API keys here. This file is public; the Apps Script URL is safe to expose.
window.CAMBIUM_REGISTRY = {
  endpoint: ""
};
