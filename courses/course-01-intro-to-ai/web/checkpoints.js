// Module checkpoints + course progress writer for slides.html.
// Loads after the main slides script and wraps the global go().
(function(){
  var CP = {
    8:  { m: "Module 1 checkpoint", qs: [
      ["Which is the newest, innermost member of the AI family tree?", ["Machine learning","Generative AI","Deep learning"], 1],
      ["Before chatbots, had you already been using AI daily?", ["Yes, spam filters, cameras, maps and more","No, chatbots were the first real AI"], 0] ] },
    14: { m: "Module 2 checkpoint", qs: [
      ["At its core, a language model...", ["searches a database of answers","follows grammar rules written by linguists","predicts the next token, again and again"], 2],
      ["When a chat outgrows the context window...", ["the earliest content silently falls out","the model crashes","it starts charging money"], 0] ] },
    19: { m: "Module 3 checkpoint", qs: [
      ["Which steps turn a raw autocomplete into a polite assistant?", ["More pretraining data","Fine-tuning plus human feedback","A bigger context window"], 1],
      ["AI hallucinates because...", ["it gets tired","plausible is not the same as true","its internet connection drops"], 1] ] },
    26: { m: "Module 4 checkpoint", qs: [
      ["Open weights means...", ["the model is free on the maker's website","you can download and run the model yourself","the training data is public"], 1],
      ["Which trio is closed-weights?", ["GPT, Claude, Gemini","Llama, DeepSeek, Qwen","Mistral, Gemma, Phi"], 0] ] },
    30: { m: "Module 5 checkpoint", qs: [
      ["Sensitive data. Best habit?", ["Paste it into any free chatbot","Run an open model locally, or use a plan with training off","Email it to yourself first"], 1],
      ["The right question is not which model is best, but...", ["which is newest","which is best for this job","which has the most users"], 1] ] },
    34: { m: "Module 6 checkpoint", qs: [
      ["The four prompt moves are role, context, task, and...", ["format","length","politeness"], 0],
      ["The one rule to carry out the door:", ["The newest model is always best","Never use AI for real work","Trust, but verify"], 2] ] }
  };
  var SEENKEY = "cambium-c01-checkpoints", PROGKEY = "cambium-c01-slides";
  var seen = {};
  try { seen = JSON.parse(localStorage.getItem(SEENKEY) || "{}"); } catch(e){}
  function saveProgress(){
    var prev = {};
    try { prev = JSON.parse(localStorage.getItem(PROGKEY) || "{}"); } catch(e){}
    var reached = Math.max(prev.seen || 0, (typeof i === "number" ? i : 0) + 1);
    localStorage.setItem(PROGKEY, JSON.stringify({ seen: reached, total: 36, done: reached >= 36 }));
  }
  var overlay = document.createElement("div");
  overlay.style.cssText = "display:none;position:fixed;inset:0;background:rgba(31,61,36,.72);z-index:50;align-items:center;justify-content:center;padding:16px";
  overlay.innerHTML = '<div style="background:#fff;border-radius:16px;max-width:560px;width:100%;max-height:88vh;overflow:auto;padding:24px" id="cpCard"></div>';
  document.body.appendChild(overlay);
  var open = false, pending = null;

  function show(idx){
    open = true; pending = idx;
    var cp = CP[idx];
    var h = '<div style="font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#6E9648">' + cp.m + '</div>' +
      '<div style="font-family:Cambria,Georgia,serif;font-size:22px;font-weight:700;margin:6px 0 14px;color:#1F2A20">Quick check before you move on</div>';
    cp.qs.forEach(function(q, qi){
      h += '<div style="margin-bottom:14px" id="cpq' + qi + '"><div style="font-weight:600;font-size:14.5px;margin-bottom:8px;color:#1F2A20">' + (qi+1) + '. ' + q[0] + '</div>';
      q[1].forEach(function(o, oi){
        h += '<label style="display:block;padding:8px 11px;border:1px solid #DFE9D8;border-radius:8px;margin:5px 0;font-size:13.5px;cursor:pointer;color:#1F2A20"><input type="radio" name="cpq' + qi + '" value="' + oi + '" style="margin-right:8px;accent-color:#2C5F2D">' + o + '</label>';
      });
      h += '<div id="cpfb' + qi + '" style="display:none;font-size:13px;margin-top:6px"></div></div>';
    });
    h += '<div style="display:flex;gap:10px;align-items:center;margin-top:16px">' +
      '<button id="cpCheck" style="background:#2C5F2D;color:#fff;border:0;border-radius:8px;padding:11px 20px;font-size:14px;font-weight:700;cursor:pointer">Check answers</button>' +
      '<button id="cpGo" style="display:none;background:#97BC62;color:#1F3D24;border:0;border-radius:8px;padding:11px 20px;font-size:14px;font-weight:700;cursor:pointer">Continue</button>' +
      '<a href="#" id="cpSkip" style="margin-left:auto;font-size:12.5px;color:#5C6B5A">skip</a></div>';
    document.getElementById("cpCard").innerHTML = h;
    overlay.style.display = "flex";
    document.getElementById("cpCheck").onclick = function(){
      var allAnswered = true;
      cp.qs.forEach(function(q, qi){ if (!document.querySelector('input[name="cpq' + qi + '"]:checked')) allAnswered = false; });
      if (!allAnswered) { alert("Answer both questions, or press skip."); return; }
      cp.qs.forEach(function(q, qi){
        var pick = +document.querySelector('input[name="cpq' + qi + '"]:checked').value;
        var fb = document.getElementById("cpfb" + qi);
        fb.style.display = "block";
        if (pick === q[2]) { fb.textContent = "Correct."; fb.style.color = "#2C5F2D"; }
        else { fb.textContent = "Not quite. Answer: " + q[1][q[2]]; fb.style.color = "#B3372E"; }
      });
      document.getElementById("cpGo").style.display = "inline-block";
      this.style.display = "none";
    };
    document.getElementById("cpGo").onclick = closeAndAdvance;
    document.getElementById("cpSkip").onclick = function(e){ e.preventDefault(); closeAndAdvance(); };
  }
  function closeAndAdvance(){
    overlay.style.display = "none"; open = false;
    seen[pending] = 1; localStorage.setItem(SEENKEY, JSON.stringify(seen));
    pending = null;
    _cpGo(1);
  }
  var _cpGo = go;
  go = function(d){
    if (open) return;
    if (d > 0 && CP[i] && !seen[i]) { show(i); return; }
    _cpGo(d);
    saveProgress();
  };
  saveProgress();
})();
