// Certificate extras v3: LinkedIn add-to-profile linked to the institute's company page,
// a proper achievement badge (Credly-style medallion), share row with working text,
// learner registry ping, career guide. Waits for the certificate to render.
(function(){
  var COURSE = "Intro to AI (Cambium Academy Course 01)";
  var ORG_ID = "133384582"; // linkedin.com/company/cambium-ai-institute
  var LANDER = "https://pkjaslam.github.io/Cambium_AI/start/";
  var CERTURL = "https://pkjaslam.github.io/Cambium_AI/courses/course-01-intro-to-ai/web/certificate.html";

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
      "&organizationId=" + ORG_ID +
      "&issueYear=" + d.getFullYear() + "&issueMonth=" + (d.getMonth() + 1) +
      "&certUrl=" + encodeURIComponent(CERTURL) +
      "&certId=" + encodeURIComponent(certId);

    var shareText = "I just earned the Intro to AI certificate from Cambium AI Institute. Free, hands-on, and the quiz stays locked until you actually study. Join the founding cohort: " + LANDER;
    var enc = encodeURIComponent;
    var shares = [
      ["LinkedIn", "https://www.linkedin.com/feed/?shareActive=true&text=" + enc(shareText)],
      ["Facebook", "https://www.facebook.com/sharer/sharer.php?u=" + enc(LANDER) + "&quote=" + enc(shareText)],
      ["X", "https://twitter.com/intent/tweet?text=" + enc(shareText)],
      ["WhatsApp", "https://wa.me/?text=" + enc(shareText)]
    ];

    var bar = document.createElement("div");
    bar.id = "extrasbar";
    bar.style.cssText = "width:min(920px,96%);margin:18px auto 0;background:#fff;border:1px solid #DFE9D8;border-radius:14px;padding:16px 18px";
    var btnCss = "border-radius:8px;padding:11px 16px;font-size:13.5px;font-weight:700;text-decoration:none;display:inline-block;cursor:pointer";
    bar.innerHTML =
      '<div style="font-weight:700;margin-bottom:10px;color:#1F2A20">Make it count</div>' +
      '<div style="display:flex;gap:9px;flex-wrap:wrap">' +
        '<a href="' + li + '" target="_blank" rel="noopener" style="background:#0A66C2;color:#fff;' + btnCss + '">Add to LinkedIn profile</a>' +
        '<button id="badgeBtn" style="background:#2C5F2D;color:#fff;border:0;' + btnCss + '">Download my badge</button>' +
        '<a href="career.html" style="background:#fff;color:#2C5F2D;border:1.5px solid #97BC62;' + btnCss + '">Career guide</a>' +
        '<a href="https://github.com/pkjaslam/Cambium_AI/discussions" target="_blank" rel="noopener" style="background:#fff;color:#2C5F2D;border:1.5px solid #97BC62;' + btnCss + '">Graduate wall</a>' +
      '</div>' +
      '<div style="display:flex;gap:9px;flex-wrap:wrap;align-items:center;margin-top:11px">' +
        '<span style="font-size:13px;font-weight:700;color:#5C6B5A">Share the news:</span>' +
        shares.map(function(s){ return '<a href="' + s[1] + '" target="_blank" rel="noopener" style="background:#F0F5EC;color:#2C5F2D;border:1px solid #DFE9D8;border-radius:16px;padding:7px 14px;font-size:12.5px;font-weight:700;text-decoration:none">' + s[0] + '</a>'; }).join("") +
      '</div>' +
      '<div style="font-size:12px;color:#5C6B5A;margin-top:10px">Lost this page? Reopen it in this browser and your certificate reappears automatically; the Reprint note confirms it. Employers can scan the QR on the certificate to verify it instantly. Share links point to the Academy so friends can join free.</div>';
    var anchor = document.querySelector(".scalebox") || document.querySelector("x-dc") || document.body.lastElementChild;
    anchor.parentNode.insertBefore(bar, anchor.nextSibling);

    // Achievement badge: gold-ringed medallion on forest, logo crest, ribbon with the name.
    document.getElementById("badgeBtn").onclick = function(){
      var cv = document.createElement("canvas"); cv.width = 640; cv.height = 800;
      var c = cv.getContext("2d");
      var cx = 320, cy = 330, R = 240;

      function arcText(text, radius, startDeg, endDeg, size, color, weight){
        var a0 = startDeg * Math.PI / 180, a1 = endDeg * Math.PI / 180;
        var per = (a1 - a0) / Math.max(1, text.length - 1);
        c.save();
        c.fillStyle = color;
        c.font = (weight || "700") + " " + size + "px Georgia";
        c.textAlign = "center"; c.textBaseline = "middle";
        for (var i = 0; i < text.length; i++){
          var a = a0 + per * i;
          c.save();
          c.translate(cx + radius * Math.cos(a), cy + radius * Math.sin(a));
          c.rotate(a + Math.PI / 2);
          c.fillText(text[i], 0, 0);
          c.restore();
        }
        c.restore();
      }

      // medallion
      var ring = c.createLinearGradient(cx - R, cy - R, cx + R, cy + R);
      ring.addColorStop(0, "#D9B25C"); ring.addColorStop(.5, "#8C6320"); ring.addColorStop(1, "#D9B25C");
      c.beginPath(); c.arc(cx, cy, R, 0, 7); c.fillStyle = ring; c.fill();
      c.beginPath(); c.arc(cx, cy, R - 14, 0, 7); c.fillStyle = "#1F3D24"; c.fill();
      var disc = c.createRadialGradient(cx, cy - 60, 40, cx, cy, R);
      disc.addColorStop(0, "#2C4A28"); disc.addColorStop(1, "#16240F");
      c.beginPath(); c.arc(cx, cy, R - 20, 0, 7); c.fillStyle = disc; c.fill();
      c.beginPath(); c.arc(cx, cy, R - 30, 0, 7); c.strokeStyle = "rgba(217,178,92,.65)"; c.lineWidth = 1.5; c.stroke();

      arcText("C A M B I U M   A I   I N S T I T U T E", R - 52, -164, -16, 19, "#D9B25C");
      arcText("F O U N D I N G   C O H O R T   2 0 2 6", R - 52, 168, 12, 15, "#97BC62");

      // laurel dashes
      c.strokeStyle = "#97BC62"; c.lineWidth = 3; c.lineCap = "round";
      [-1, 1].forEach(function(s){
        for (var k = 0; k < 7; k++){
          var a = Math.PI / 2 + s * (0.55 + k * 0.13);
          var r1 = R - 66, r2 = R - 44;
          c.beginPath();
          c.moveTo(cx + r1 * Math.cos(a), cy + r1 * Math.sin(a));
          c.lineTo(cx + r2 * Math.cos(a - s * 0.06), cy + r2 * Math.sin(a - s * 0.06));
          c.stroke();
        }
      });

      function finish(){
        c.textAlign = "center";
        c.fillStyle = "#FFFDF6"; c.font = "700 52px Georgia";
        c.fillText("INTRO TO AI", cx, cy + 44);
        c.strokeStyle = "#D9B25C"; c.lineWidth = 1.5;
        c.beginPath(); c.moveTo(cx - 110, cy + 70); c.lineTo(cx + 110, cy + 70); c.stroke();
        c.fillStyle = "#D9B25C"; c.font = "700 22px Georgia";
        c.fillText("C E R T I F I E D", cx, cy + 102);

        // ribbon
        var rw = 520, rh = 86, ry = 610;
        c.fillStyle = "#2C5F2D";
        c.beginPath();
        c.moveTo(cx - rw/2, ry); c.lineTo(cx + rw/2, ry); c.lineTo(cx + rw/2 + 26, ry + rh/2);
        c.lineTo(cx + rw/2, ry + rh); c.lineTo(cx - rw/2, ry + rh); c.lineTo(cx - rw/2 - 26, ry + rh/2);
        c.closePath(); c.fill();
        c.strokeStyle = "#D9B25C"; c.lineWidth = 2;
        c.strokeRect(cx - rw/2 + 8, ry + 8, rw - 16, rh - 16);
        var nm = cert.name;
        c.fillStyle = "#FFFDF6";
        c.font = "italic 700 " + (nm.length > 22 ? Math.max(22, Math.round(34 * 22 / nm.length)) : 34) + "px Georgia";
        c.fillText(nm, cx, ry + rh/2 + 2);

        c.fillStyle = "#5C6B5A"; c.font = "600 15px Georgia";
        c.fillText(dateTxt + "   ·   " + certId, cx, ry + rh + 34);
        c.fillStyle = "#8A9784"; c.font = "13px Georgia";
        c.fillText("verify: pkjaslam.github.io/Cambium_AI · scan the certificate QR", cx, ry + rh + 58);

        try {
          var a = document.createElement("a");
          a.download = "cambium-academy-intro-to-ai-badge.png";
          a.href = cv.toDataURL("image/png");
          a.click();
        } catch(e) {
          alert("Your browser blocked the download (this can happen when opening the file from disk). It works on the published course site.");
        }
      }

      var img = new Image();
      img.onload = function(){
        var lw = 108;
        c.save();
        c.beginPath(); c.arc(cx, cy - 92, 62, 0, 7); c.fillStyle = "#FFFDF6"; c.fill();
        c.beginPath(); c.arc(cx, cy - 92, 62, 0, 7); c.strokeStyle = "#D9B25C"; c.lineWidth = 3; c.stroke();
        c.clip ? null : null;
        try { c.drawImage(img, cx - lw/2, cy - 92 - lw/2, lw, lw); } catch(e){}
        c.restore();
        finish();
      };
      img.onerror = finish;
      img.src = "../../../assets/logo-mark@2x.png";
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
