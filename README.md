# Shumaar: put it online

The site is a static page plus JSON data, with one small server function (`functions/api/`)
that lets Ask call Claude. Everything runs free on Cloudflare Pages, and Ask works without
Claude until you add an API key.

## 1. Put the files on GitHub (5 min)

1. Create a free account at github.com and click **New repository**. Name it `shumaar`; it can
   be private.
2. Click **uploading an existing file**.
3. Drag in **everything in this folder**, including the `functions` folder and `_headers`.
4. Click **Commit**.

## 2. Publish with Cloudflare Pages (5 min)

1. Create a free account at dash.cloudflare.com.
2. Go to **Workers & Pages → Create → Pages → Connect to Git** and choose the `shumaar` repo.
3. Set **Framework preset** to *None*, leave **Build command** empty, and set **Build output
   directory** to `/`.
4. Click **Save and Deploy**. The site goes live at `https://shumaar.pages.dev` (or a similar
   name).

From now on, every change you commit on GitHub redeploys the site automatically.

## 3. Turn on visitor analytics (1 min)

In the Pages project, go to **Metrics → Web Analytics → Enable**.

* **What you see:** visitors, page views, countries, where visitors came from, devices and load
  speed.
* **No cookie banner needed:** it doesn't use cookies and doesn't track people across sites.
* **One limit:** tabs inside the site (Economy, Districts, …) change only the `#` part of the
  address, so they count as one page. You get site visits, not per-tab views.

## 4. Turn on Munshi, the AI helper in Ask (10 min, optional)

Without this step, Ask uses quick keyword answers only, which are free and already handles most
questions.

1. **Get an API key:** at console.anthropic.com, add about $5 of credit, set a **monthly spend
   limit** (say $10), and create an API key.
2. **Create the answer store:** in Cloudflare, go to **Storage & databases → KV → Create**,
   name it `ASK_KV`.
3. **Connect the store:** in the Pages project, go to **Settings → Bindings → Add → KV
   namespace**. Variable name `ASK_KV`, namespace `ASK_KV`.
4. **Add the key:** go to **Settings → Variables and secrets → Add**. Type *Secret*, name
   `ANTHROPIC_API_KEY`, value: your key.
5. **Optional settings:** add these as variables if you want to change the defaults:

   | Variable | Default | What it does |
   |---|---|---|
   | `PER_IP_DAY` | 20 | Questions per visitor per day that reach Claude |
   | `DAILY_CAP` | 1000 | Questions per day in total that reach Claude |
   | `CACHE_TTL` | 0 | 0 keeps saved answers until the data is rebuilt; or seconds |
   | `PREWARM_TOKEN` | (secret) | Lets `prewarm.mjs` fill the cache; see the worker README |
   | `MODEL` | claude-haiku-5-5 | Which Claude model answers |

6. **Redeploy:** go to **Deployments → ⋯ → Retry deployment**.
7. **Check it:** `https://<your site>/api/health` should show `{"ok":true,...}`. Then ask the
   site "compare literacy in Lahore and Quetta".

### What Claude answers cost

* **What reaches Claude:** only questions that keyword matching is unsure about, and questions
  that need reasoning ("compare", "why", "which district is highest").
* **Model:** Claude Haiku 5.5, at about $0.001 per question.
* **Prompt caching:** the instructions and data catalog are cached, which cuts input cost about
  tenfold.
* **Saved answers:** each answer is kept until the data is rebuilt, and a reworded question with the
  same key words reuses it, so repeats are free.
* **Prewarm:** `node tools/prewarm.mjs https://<your site>` (with `PREWARM_TOKEN` set) asks about 50
  common "why" questions once and writes `faq.json`, so visitors never pay for them.
* **Limits:** each visitor and the whole site have daily limits, and your Anthropic spend limit
  is the hard ceiling.

## 5. Your own domain

**If you are buying one:** in Cloudflare, go to **Domain Registration → Register Domains**. It sells
at cost (about $10.46 a year for a `.com`), and the domain is ready to use straight away.

**If you already have one elsewhere** (e.g. GoDaddy, Namecheap, PKNIC for `.pk`):
1. In Cloudflare, click **Add a domain**, enter it, and pick the **Free** plan.
2. Cloudflare shows two nameservers. At your registrar, replace the domain's nameservers with those
   two. It usually takes under an hour, sometimes up to a day.
3. In the Pages project, go to **Custom domains → Set up a domain**, enter the domain (and
   `www.` too). HTTPS is automatic.

(If you'd rather keep DNS at your registrar, add a `CNAME` for `www` pointing to
`<project>.pages.dev` instead, and use `www.yourdomain` as the main address.)

## 6. The public data API

The same deployment serves a free, read-only data API at `/api/v1`, with no key and no AI cost:

| Request | What you get |
|---|---|
| `/api/v1` | List of endpoints |
| `/api/v1/indicators?theme=Economy` | Province and national indicators |
| `/api/v1/indicators/mo_m2` | One indicator with definition and source |
| `/api/v1/layers` | All district map layers |
| `/api/v1/layers/mc_read?province=sindh` | One layer for every district (`&format=csv` for a file) |
| `/api/v1/districts/rajanpur` | Every measure for one district |
| `/api/v1/tables/msGrow?format=csv` | The data behind a chart |
| `/api/v1/search?q=crop fires` | Find anything by words |

Responses are cached at Cloudflare's edge for an hour and allowed from any website (CORS). The Data
tab on the site documents it with live example links.

## Updating data

* **Charts:** each tab reads its own JSON file (`tracker.json` for This month, `debt.json` for
  Debt, …). Replace the file on GitHub and the site redeploys.
* **Claude's copy of the data:** Claude answers from `functions/_lib/askdata.json`. After big
  data changes, refresh it:
  1. Open the site and open the browser console.
  2. Run `copy(shumaarAskData())`.
  3. Paste the result over that file and commit.

## Testing locally

Run `python3 -m http.server` in this folder and open http://localhost:8000. Ask works with
keyword matching only, because the function needs Cloudflare. To test it too, run
`npx wrangler pages dev .`.
