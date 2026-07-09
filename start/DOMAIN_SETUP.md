# Free branded domain: cambiumai.is-a.dev (checked available July 9, 2026)

is-a.dev gives free-for-life subdomains for developer and open-source projects, run on
Cloudflare DNS, claimed through a small pull request. `cambiumai`, `cambium`, and
`cambium-ai` were all unclaimed at time of writing. No renewals, no fees, ever.

## Step A · Claim the name (5 minutes, do this from YOUR GitHub account)

1. Open https://github.com/is-a-dev/register and click Fork.
2. In your fork: Add file, Create new file. Name it exactly:
   `domains/cambiumai.json`
3. Paste this (also saved next to this guide as `is-a-dev-cambiumai.json`):

```json
{
    "owner": {
        "username": "pkjaslam",
        "email": "pkjaslamagrico@gmail.com"
    },
    "records": {
        "CNAME": "pkjaslam.github.io"
    }
}
```

4. Commit, then open the pull request. In the PR description write one short personal
   line, for example: "Registering cambiumai for Cambium Academy, my free open AI-literacy
   course project, live at https://pkjaslam.github.io/Cambium_AI/start/". Keep it human:
   their maintainers reject PRs that look AI-generated or spammy, and the live site is
   what convinces them.
5. Watch the PR for reviewer comments. Merges usually land within hours to a couple of days.

Privacy note: that email becomes public in their repo. If you prefer, replace the email
line with your Discord handle ("discord": "yourhandle"), one of the two is required.

## Step B · Connect it to the site (2 minutes, after the PR merges)

1. github.com/pkjaslam/Cambium_AI, Settings, Pages.
2. Custom domain: `cambiumai.is-a.dev`, Save.
3. Wait for the DNS check to turn green, then tick "Enforce HTTPS".

From that moment the whole site lives at the new address, and every old
pkjaslam.github.io/Cambium_AI link redirects there automatically, so nothing breaks,
including certificates already on LinkedIn.

New key URLs:
- Landing page: https://cambiumai.is-a.dev/start/
- Course: https://cambiumai.is-a.dev/courses/course-01-intro-to-ai/web/

## Step C · Tell Claude "domain is live"

One pass then updates every reference: the og:url tags, the share buttons and share-image
footer, PUBLISHING.md, the YouTube description links, and, important, the Amelia chat
worker's ALLOW_ORIGIN variable in Cloudflare must change to `https://cambiumai.is-a.dev`
or her live chat will be blocked by CORS on the new domain.

## Free extras is-a.dev supports (optional, later)

- More record types: A, AAAA, TXT, MX, URL redirects, and Cloudflare proxying.
- Free branded email such as hello@cambiumai.is-a.dev: add MX + TXT records in a second
  PR pointing at a free forwarder like ImprovMX, which relays to your Gmail.
- Nested names (e.g. labs.cambiumai.is-a.dev) are separate one-file claims.

## Honest caveats

It is a community-run service (Cloudflare-sponsored, years of track record, thousands of
domains, but not a contract). The name lives under their terms of service. That is why our
certificates keep pointing at the permanent github.io address, and if the Academy outgrows
this, a paid cambium-ai.com can replace it later with the same one-setting switch.
