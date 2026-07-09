// Certificate extras v2: LinkedIn add-to-profile, social share row, share image,
// learner registry ping, career guide. Waits for the certificate to render, then
// reads the real certificate ID from the page.
(function(){
  var COURSE = "Intro to AI (Cambium Academy Course 01)";
  var ORG = "Cambium AI Research Institution";
  var LANDER = "https://pkjaslam.github.io/Cambium_AI/start/";
  var CERTURL = "https://pkjaslam.github.io/Cambium_AI/courses/course-01-intro-to-ai/web/certificate.html";
  var LI_COMPANY = "https://www.linkedin.com/company/cambium-ai-institute/";

  var cfgTag = document.createElement("script");
  cfgTag.src = "registry-config.js";
  document.head.appendChild(cfgTag);

  function rd(k){ try { return JSON.parse(localStorage.getItem(k) || "null"); } catch(e){ return null; } }

  var tries = 0;
  var timer = setInterval(function(){
    tries++;
    var cert = window.__CERT;
    if (!cert || !cert.name) { if (tries > 20) clearInterval(timer); return; }
    var m = (document.body.innerText || "").match(/CAMB-C01-[A-Z0-9]{6}/);
    if (!m && tries < 14) return;
    clearInterval(timer);
    init(cert, m ? m[0] : "");
  }, 320);

  function init(cert, certId){
    var d = cert.date ? new Date(cert.date + "T12:00:00") : new Date();
    var dateTxt = d.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });

    var li = "https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME" +
      "&name=" + encodeURIComponent(COURSE) +
      "&organizationName=" + encodeURIComponent(ORG) +
      "&issueYear=" + d.getFullYear() + "&issueMonth=" + (d.getMonth() + 1) +
      "&certUrl=" + encodeURIComponent(CERTURL) +
      "&certId=" + encodeURIComponent(certId);

    var shareText = "I just earned the Intro to AI certificate from Cambium AI Research Institution. Free, hands-on, and the quiz is locked until you actually study. Join the founding cohort:";
    var enc = encodeURIComponent;
    var shares = [
      ["LinkedIn", "https://www.linkedin.com/sharing/share-offsite/?url=" + enc(LANDER)],
      ["Facebook", "https://www.facebook.com/sharer/sharer.php?u=" + enc(LANDER) + "&quote=" + enc(shareText)],
      ["X", "https://twitter.com/intent/tweet?text=" + enc(shareText) + "&url=" + enc(LANDER)],
      ["WhatsApp", "https://wa.me/?text=" + enc(shareText + " " + LANDER)]
    ];

    var bar = document.createElement("div");
    bar.id = "extrasbar";
    bar.style.cssText = "width:min(920px,96%);margin:18px auto 0;background:#fff;border:1px solid #DFE9D8;border-radius:14px;padding:16px 18px";
    var btnCss = "border-radius:8px;padding:11px 16px;font-size:13.5px;font-weight:700;text-decoration:none;display:inline-block;cursor:pointer";
    bar.innerHTML =
      '<div style="font-weight:700;margin-bottom:10px;color:#1F2A20">Make it count</div>' +
      '<div style="display:flex;gap:9px;flex-wrap:wrap">' +
        '<a href="' + li + '" target="_blank" rel="noopener" style="background:#0A66C2;color:#fff;' + btnCss + '">Add to LinkedIn profile</a>' +
        '<button id="shareImg" style="background:#2C5F2D;color:#fff;border:0;' + btnCss + '">Download share image</button>' +
        '<a href="career.html" style="background:#fff;color:#2C5F2D;border:1.5px solid #97BC62;' + btnCss + '">Career guide</a>' +
        '<a href="https://github.com/pkjaslam/Cambium_AI/discussions" target="_blank" rel="noopener" style="background:#fff;color:#2C5F2D;border:1.5px solid #97BC62;' + btnCss + '">Graduate wall</a>' +
      '</div>' +
      '<div style="display:flex;gap:9px;flex-wrap:wrap;align-items:center;margin-top:11px">' +
        '<span style="font-size:13px;font-weight:700;color:#5C6B5A">Share the news:</span>' +
        shares.map(function(s){ return '<a href="' + s[1] + '" target="_blank" rel="noopener" style="background:#F0F5EC;color:#2C5F2D;border:1px solid #DFE9D8;border-radius:16px;padding:7px 14px;font-size:12.5px;font-weight:700;text-decoration:none">' + s[0] + '</a>'; }).join("") +
      '</div>' +
      '<div style="font-size:12px;color:#5C6B5A;margin-top:10px">Closed this page by mistake? Just come back: your certificate reprints from this browser anytime. Anyone can check your ID on the <a href="verify.html" style="color:#2C5F2D">verification page</a>. Sharing links point to the Academy so friends can join free.</div>';
    var anchor = document.querySelector(".scalebox") || document.querySelector("x-dc") || document.body.lastElementChild;
    anchor.parentNode.insertBefore(bar, anchor.nextSibling);

    document.getElementById("shareImg").onclick = function(){
      var cv = document.createElement("canvas"); cv.width = 1200; cv.height = 630;
      var c = cv.getContext("2d");
      c.fillStyle = "#1F3D24"; c.fillRect(0, 0, 1200, 630);
      c.strokeStyle = "#97BC62"; c.lineWidth = 3; c.strokeRect(26, 26, 1148, 578);
      c.fillStyle = "#97BC62"; c.font = "700 26px Arial"; c.textAlign = "center";
      c.fillText("C A M B I U M   A C A D E M Y", 600, 104);
      c.fillStyle = "#CFE3BF"; c.font = "italic 24px Georgia";
      c.fillText("certificate of completion", 600, 150);
      c.fillStyle = "#FFFFFF"; c.font = "italic 700 60px Georgia";
      c.fillText(cert.name, 600, 254);
      if (cert.org) { c.fillStyle = "#CFE3BF"; c.font = "22px Arial"; c.fillText(cert.org, 600, 296); }
      c.strokeStyle = "#97BC62"; c.lineWidth = 2;
      c.beginPath(); c.moveTo(320, 316); c.lineTo(880, 316); c.stroke();
      c.fillStyle = "#E8F2DE"; c.font = "700 38px Georgia";
      c.fillText("Intro to AI", 600, 382);
      c.fillStyle = "#CFE3BF"; c.font = "21px Arial";
      c.fillText("How AI works, how models are trained, which model to use", 600, 422);
      c.fillStyle = "#97BC62"; c.font = "700 22px Arial";
      c.fillText(dateTxt + "   ·   " + certId, 600, 486);
      c.fillStyle = "#7FA06F"; c.font = "20px Arial";
      c.fillText("Cambium AI Research Institution  ·  free AI courses  ·  " + LANDER.replace("https://",""), 600, 560);
      var img = new Image();
      img.onload = function(){ try { c.drawImage(img, 84, 58, 96, 96); } catch(e){} finish(); };
      img.onerror = finish;
      img.src = "../../../assets/logo-mark@2x.png";
      function finish(){
        try {
          var a = document.createElement("a");
          a.download = "cambium-academy-course01-certificate.png";
          a.href = cv.toDataURL("image/png");
          a.click();
        } catch(e) {
          alert("Your browser blocked the image download (this can happen when opening the file directly from disk). It works on the published course site.");
        }
      }
    };

    // Learner registry: one quiet, one-time ping to YOUR sheet, only if enabled.
    setTimeout(function(){
      try {
        var reg = window.CAMBIUM_REGISTRY;
        if (!reg || !reg.endpoint || reg.endpoint.length < 9) return;
        if (localStorage.getItem("cambium-c01-registered") === certId) return;
        var learner = rd("cambium-c01-learner") || {};
        fetch(reg.endpoint, {
          method: "POST",
          mode: "no-cors",
          headers: { "Content-Type": "text/plain" },
          body: JSON.stringify({ course: "C01", name: cert.name, org: cert.org || "", email: learner.email || "", certId: certId, date: cert.date || "", score: cert.score || "" })
        }).then(function(){ localStorage.setItem("cambium-c01-registered", certId); }).catch(function(){});
      } catch(e) {}
    }, 800);
  }
})();
