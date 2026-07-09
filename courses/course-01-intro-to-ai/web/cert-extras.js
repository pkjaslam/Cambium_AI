// Certificate extras: LinkedIn add-to-profile, share image, graduate wall, progress write.
(function(){
  var COURSE = "Intro to AI (Cambium Academy Course 01)";
  var ORG = "Cambium AI Research Institution";
  var CERTURL = "https://pkjaslam.github.io/Cambium_AI/courses/course-01-intro-to-ai/web/certificate.html";
  var LI_COMPANY = "https://www.linkedin.com/company/cambium-ai-institute/";

  function q(k){ return new URLSearchParams(location.search).get(k); }
  var name = q("name");
  if (!name) return;

  try { localStorage.setItem("cambium-c01-cert", JSON.stringify({ issued: true, date: q("date") || "", score: q("score") || "" })); } catch(e){}

  var certId = document.getElementById("certId") ? document.getElementById("certId").textContent : "";
  var d = q("date") ? new Date(q("date") + "T12:00:00") : new Date();

  var bar = document.createElement("div");
  bar.id = "extrasbar";
  bar.style.cssText = "width:min(900px,96%);max-width:900px;margin:18px auto 0;background:#fff;border:1px solid #DFE9D8;border-radius:12px;padding:16px 18px";
  bar.innerHTML = '<div style="font-weight:700;margin-bottom:10px;color:#1F2A20">Make it count</div>' +
    '<div style="display:flex;gap:10px;flex-wrap:wrap">' +
    '<a id="liAdd" style="background:#0A66C2;color:#fff;border-radius:8px;padding:11px 18px;font-size:14px;font-weight:700;text-decoration:none" target="_blank" rel="noopener">Add to LinkedIn profile</a>' +
    '<button id="shareImg" style="background:#2C5F2D;color:#fff;border:0;border-radius:8px;padding:11px 18px;font-size:14px;font-weight:700;cursor:pointer">Download share image</button>' +
    '<a href="https://github.com/pkjaslam/Cambium_AI/discussions" target="_blank" rel="noopener" style="background:#fff;color:#2C5F2D;border:1.5px solid #97BC62;border-radius:8px;padding:11px 18px;font-size:14px;font-weight:700;text-decoration:none">Post it on the graduate wall</a>' +
    '<a href="' + LI_COMPANY + '" target="_blank" rel="noopener" style="background:#fff;color:#2C5F2D;border:1.5px solid #97BC62;border-radius:8px;padding:11px 18px;font-size:14px;font-weight:700;text-decoration:none">Follow the institute</a>' +
    '<a href="career.html" style="background:#fff;color:#2C5F2D;border:1.5px solid #97BC62;border-radius:8px;padding:11px 18px;font-size:14px;font-weight:700;text-decoration:none">Career guide</a>' +
    '</div><div style="font-size:12px;color:#5C6B5A;margin-top:10px">LinkedIn opens prefilled: certification name, issuer, date, and your certificate ID. Anyone can check your ID on the <a href="verify.html" style="color:#2C5F2D">verification page</a>.</div>';
  var anchor = document.querySelector(".scalebox") || document.querySelector(".cert");
  anchor.parentNode.insertBefore(bar, anchor.nextSibling);

  var li = "https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME" +
    "&name=" + encodeURIComponent(COURSE) +
    "&organizationName=" + encodeURIComponent(ORG) +
    "&issueYear=" + d.getFullYear() + "&issueMonth=" + (d.getMonth() + 1) +
    "&certUrl=" + encodeURIComponent(CERTURL) +
    "&certId=" + encodeURIComponent(certId);
  document.getElementById("liAdd").href = li;

  document.getElementById("shareImg").onclick = function(){
    var cv = document.createElement("canvas"); cv.width = 1200; cv.height = 630;
    var c = cv.getContext("2d");
    c.fillStyle = "#1F3D24"; c.fillRect(0, 0, 1200, 630);
    c.strokeStyle = "#97BC62"; c.lineWidth = 3; c.strokeRect(26, 26, 1148, 578);
    c.fillStyle = "#97BC62"; c.font = "700 26px Arial"; c.textAlign = "center";
    c.fillText("C A M B I U M   A C A D E M Y", 600, 110);
    c.fillStyle = "#CFE3BF"; c.font = "italic 24px Georgia";
    c.fillText("certificate of completion", 600, 158);
    c.fillStyle = "#FFFFFF"; c.font = "italic 700 64px Georgia";
    c.fillText(name, 600, 268);
    c.strokeStyle = "#97BC62"; c.lineWidth = 2;
    c.beginPath(); c.moveTo(320, 296); c.lineTo(880, 296); c.stroke();
    c.fillStyle = "#E8F2DE"; c.font = "700 40px Georgia";
    c.fillText("Intro to AI", 600, 372);
    c.fillStyle = "#CFE3BF"; c.font = "22px Arial";
    c.fillText("How AI works, how models are trained, which model to use", 600, 414);
    c.fillStyle = "#97BC62"; c.font = "700 22px Arial";
    c.fillText(d.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }) + "   ·   " + certId, 600, 480);
    c.fillStyle = "#7FA06F"; c.font = "20px Arial";
    c.fillText("Cambium AI Research Institution  ·  free courses in AI  ·  linkedin.com/company/cambium-ai-institute", 600, 560);
    var img = new Image();
    img.onload = function(){
      c.save(); c.beginPath(); c.arc(600, 100, 0, 0, 7); c.restore();
      try { c.drawImage(img, 84, 60, 96, 96); } catch(e){}
      finish();
    };
    img.onerror = finish;
    img.src = "../../../assets/logo-mark@2x.png";
    function finish(){
      try {
        var a = document.createElement("a");
        a.download = "cambium-academy-course01-certificate.png";
        a.href = cv.toDataURL("image/png");
        a.click();
      } catch(e) {
        alert("Your browser blocked the image download (this can happen when opening the file directly from disk). It will work on the published course site.");
      }
    }
  };
})();
