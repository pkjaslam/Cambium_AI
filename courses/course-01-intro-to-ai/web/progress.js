// Course progress tracker for the home page, ordered by the required learning path:
// lecture -> flashcards -> playground -> quiz (locked until the three are done) -> certificate.
(function(){
  function read(k){ try { return JSON.parse(localStorage.getItem(k) || "null"); } catch(e){ return null; } }
  function render(){
    var slides = read("cambium-c01-slides") || {};
    var seen = slides.seen || 0;
    var watched = !!(read("cambium-c01-lecture") || {}).watched;
    var lectureDone = watched || seen >= 36;
    var cards = Object.keys(read("cambium-c01-cards") || {}).length;
    var pg = read("cambium-c01-playground") || {};
    var pgN = (pg.tok?1:0) + (pg.lm?1:0) + (pg.net?1:0);
    var quiz = read("cambium-c01-quiz") || {};
    var cert = read("cambium-c01-cert") || {};
    var unlocked = lectureDone && cards >= 24 && pgN >= 3;

    var steps = [
      { label: "1 · Lecture", detail: lectureDone ? (watched && seen < 36 ? "watched the video" : "done") : (seen > 0 ? seen + " of 36 slides" : "slides or video"), pct: lectureDone ? 100 : Math.min(99, Math.round(100 * seen / 36)), href: "slides.html" },
      { label: "2 · Flashcards", detail: cards + " of 24 known", pct: Math.min(100, Math.round(100 * cards / 24)), href: "flashcards.html" },
      { label: "3 · Playground", detail: pgN + " of 3 labs explored", pct: Math.round(100 * pgN / 3), href: "playground.html" },
      { label: "4 · Quiz", detail: quiz.passed ? "passed, " + quiz.best + "/20" : (unlocked ? (quiz.best ? "best " + quiz.best + "/20, pass is 14" : "unlocked, go for it") : "locked until steps 1 to 3 are done"), pct: quiz.passed ? 100 : (unlocked ? Math.min(99, Math.round(100 * (quiz.best || 0) / 14)) : 0), href: "quiz.html" },
      { label: "5 · Certificate", detail: cert.issued ? "issued" : "after the quiz", pct: cert.issued ? 100 : 0, href: "certificate.html" }
    ];
    var total = Math.round(steps.reduce(function(s, x){ return s + x.pct; }, 0) / steps.length);
    var host = document.getElementById("progress-host");
    if (!host) return;
    var h = '<div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px"><h2 style="font-family:Cambria,Georgia,serif;font-size:30px;margin-bottom:6px">Your path</h2><div style="font-size:14px;color:#5C6B5A">saved in this browser only</div></div>';
    h += '<div style="background:#D3DECC;border-radius:8px;height:12px;margin:10px 0 16px"><div style="background:#2C5F2D;height:12px;border-radius:8px;width:' + total + '%"></div></div>';
    h += '<div class="grid">';
    steps.forEach(function(s){
      h += '<a href="' + s.href + '" style="text-decoration:none"><div class="card"><h3 style="display:flex;justify-content:space-between"><span>' + s.label + '</span><span style="color:' + (s.pct >= 100 ? "#2C5F2D" : "#B98A2D") + '">' + s.pct + "%" + '</span></h3><p>' + s.detail + '</p></div></a>';
    });
    h += '</div>';
    if (total >= 100) h += '<p style="margin-top:12px;font-size:14.5px;color:#2C5F2D;font-weight:600">Course complete. Post your certificate on the graduate wall and see you next week for Course 02.</p>';
    host.innerHTML = h;
  }
  render();

  var btn = document.getElementById("lectureBtn");
  if (btn) {
    var w = !!(read("cambium-c01-lecture") || {}).watched;
    if (w) { btn.textContent = "Lecture marked as watched"; btn.style.background = "#97BC62"; btn.style.color = "#1F3D24"; }
    btn.addEventListener("click", function(){
      localStorage.setItem("cambium-c01-lecture", JSON.stringify({ watched: true, date: new Date().toISOString().slice(0,10) }));
      btn.textContent = "Lecture marked as watched";
      btn.style.background = "#97BC62"; btn.style.color = "#1F3D24";
      render();
    });
  }
})();
