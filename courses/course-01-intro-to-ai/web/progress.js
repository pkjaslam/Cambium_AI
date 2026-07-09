// Course progress tracker for the home page. Reads what each page saved locally.
(function(){
  function read(k){ try { return JSON.parse(localStorage.getItem(k) || "null"); } catch(e){ return null; } }
  var slides = read("cambium-c01-slides") || {};
  var cards = read("cambium-c01-cards") || {};
  var quiz = read("cambium-c01-quiz") || {};
  var cert = read("cambium-c01-cert") || {};
  var cardKnown = Object.keys(cards).length;
  var steps = [
    { label: "Slides", detail: (slides.seen || 0) + " of 36 viewed", pct: Math.min(100, Math.round(100 * (slides.seen || 0) / 36)), href: "slides.html" },
    { label: "Flashcards", detail: cardKnown + " of 24 known", pct: Math.round(100 * cardKnown / 24), href: "flashcards.html" },
    { label: "Quiz", detail: quiz.passed ? "passed, " + quiz.best + "/20" : (quiz.best ? "best " + quiz.best + "/20, pass is 14" : "not taken yet"), pct: quiz.passed ? 100 : Math.min(99, Math.round(100 * (quiz.best || 0) / 14)), href: "quiz.html" },
    { label: "Certificate", detail: cert.issued ? "issued" : "waiting for you", pct: cert.issued ? 100 : 0, href: "certificate.html" }
  ];
  var total = Math.round(steps.reduce(function(s, x){ return s + x.pct; }, 0) / 4);
  var host = document.getElementById("progress-host");
  if (!host) return;
  var h = '<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px"><h2 style="font-family:Cambria,Georgia,serif;font-size:30px;margin-bottom:6px">Your progress</h2><div style="font-size:14px;color:#5C6B5A">saved in this browser only</div></div>';
  h += '<div style="background:#D3DECC;border-radius:8px;height:12px;margin:10px 0 16px"><div style="background:#2C5F2D;height:12px;border-radius:8px;width:' + total + '%"></div></div>';
  h += '<div class="grid">';
  steps.forEach(function(s){
    h += '<a href="' + s.href + '" style="text-decoration:none"><div class="card"><h3 style="display:flex;justify-content:space-between"><span>' + s.label + '</span><span style="color:' + (s.pct >= 100 ? "#2C5F2D" : "#B98A2D") + '">' + s.pct + "%" + '</span></h3><p>' + s.detail + '</p></div></a>';
  });
  h += '</div>';
  if (total >= 100) h += '<p style="margin-top:12px;font-size:14.5px;color:#2C5F2D;font-weight:600">Course complete. Post your certificate on the graduate wall and see you next week for Course 02.</p>';
  host.innerHTML = h;
})();
