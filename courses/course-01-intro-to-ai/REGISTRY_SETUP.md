# Learner registry setup (Google Sheet, 10 minutes, free)

When enabled, every issued certificate quietly adds one row to a private Google Sheet you
own: name, designation/organization, email (if the learner gave one), certificate ID, date,
and score. That gives you a student count, a way to recover anyone's certificate, and a
contact list of consenting learners, with no signup wall and no third-party service.

## One-time setup

1. Create a Google Sheet named "Cambium Academy registry". Put headers in row 1:
   `time | course | name | org | email | certId | date | score`
2. Extensions, Apps Script. Replace the code with:

```js
function doPost(e) {
  var s = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  var d = JSON.parse(e.postData.contents);
  s.appendRow([new Date(), d.course || "", d.name || "", d.org || "", d.email || "",
               d.certId || "", d.date || "", d.score || ""]);
  return ContentService.createTextOutput("ok");
}
```

3. Deploy, New deployment, type "Web app". Execute as: Me. Who has access: Anyone.
   Authorize when asked (it only writes to this one sheet).
4. Copy the Web app URL (ends in `/exec`) and paste it into
   `web/registry-config.js` as the endpoint. Push, redeploy Pages.

## What learners see and consent to

The quiz's certificate form says plainly: email is optional, never appears on the
certificate, and is stored privately so their certificate can be recovered. No email, no
problem; the row simply has a blank email. The registry never blocks anyone: if the ping
fails or the endpoint is empty, the certificate still issues normally.

## Recovering a learner's certificate

Their row has name, org, date, and score. Rebuild their exact certificate link:

```
certificate.html?name=NAME&org=ORG&score=SCORE&date=YYYY-MM-DD
```

(URL-encode spaces as %20.) Send them that link; the page renders and prints their
certificate with the identical certificate ID, since IDs derive from name and date.

## Privacy duties (short version)

You are now holding learner emails: keep the sheet private, never sell or share the list,
and delete a learner's row if they ask. A one-line mention in a future site privacy note
("certificate details are stored by the Academy to enable recovery") keeps it honest.
