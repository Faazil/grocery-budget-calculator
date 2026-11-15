#!/usr/bin/env python3
"""Static site generator for the grocery budget calculator site.

Usage: python3 src/build.py  -> writes ./public
Config via env: SITE_URL, CONTACT_EMAIL
"""
import html
import json
import os
import shutil
from datetime import date

import data as D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "public")
SITE_URL = os.environ.get("SITE_URL", "https://grocery-budget-calculator.vercel.app").rstrip("/")
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "digitalforge.infotech@gmail.com")
SITE_NAME = "Grocery Budget Calculator"
TODAY = date.today().isoformat()
NL = chr(10)
M = D.REPORT_MONTH
YEAR = M.split()[-1]


def money(n):
    return "${:,.0f}".format(n)


def esc(s):
    return html.escape(s, quote=True)


NAV = [
    ("/", "Calculator"),
    ("/grocery-budget-for-family-of-4", "Family of 4"),
    ("/how-much-should-i-spend-on-groceries", "How much to spend"),
    ("/usda-food-plans-explained", "USDA plans"),
]


def page(path, title, desc, body, faq=None, extra_ld=None, crumbs=None):
    url = SITE_URL + (path if path != "/" else "/")
    ld = []
    if crumbs:
        items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL + "/"}]
        items.append({"@type": "ListItem", "position": 2, "name": crumbs, "item": url})
        ld.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items})
    if faq:
        ld.append({
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": q,
                            "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq],
        })
    if extra_ld:
        ld.append(extra_ld)
    ld_html = "".join('<script type="application/ld+json">%s</script>' % json.dumps(x) for x in ld)
    faq_html = ""
    if faq:
        faq_html = "<h2>Frequently asked questions</h2>" + "".join(
            "<details><summary>%s</summary><p>%s</p></details>" % (esc(q), a) for q, a in faq)
    nav = "".join('<a href="%s">%s</a>' % (h, t) for h, t in NAV)
    return f"""<!doctype html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="google-site-verification" content="poDGbQt-x1nsXU1AHATatCfVG17MQ-CB_ZgX1bugrhQ">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/style.css">
{ld_html}
</head>
<body>
<header class="site"><div class="wrap"><a class="logo" href="/">🛒 Grocery<span>Budget</span>Calc</a><nav>{nav}</nav></div></header>
<main><div class="wrap">
{body}
{faq_html}
</div></main>
<footer class="site"><div class="wrap">
<p><a href="/about">About</a><a href="/contact">Contact</a><a href="/privacy-policy">Privacy Policy</a><a href="/usda-food-plans-explained">Data &amp; method</a></p>
<p>Estimates use the USDA Food Plans, Cost of Food at Home ({M}). They're for planning only and aren't financial advice. © {YEAR} {SITE_NAME}.</p>
</div></footer>
</body>
</html>"""


def plan_table(people, highlight="moderate", note=True):
    rows = ""
    for p in D.PLANS:
        t = D.household(people, p)
        cls = ' class="hl"' if p == highlight else ""
        rows += f"<tr{cls}><td>{D.PLAN_NAMES[p]}</td><td>{money(t['weekly'])}</td><td>{money(t['monthly'])}</td><td>{money(t['yearly'])}</td></tr>"
    return f"""<div class="tablewrap"><table><thead><tr><th>USDA plan</th><th>Weekly</th><th>Monthly</th><th>Yearly</th></tr></thead><tbody>{rows}</tbody></table></div>"""


def hq(people):
    return ".".join(f"{s}{a}" for a, s in people)


CALC_HTML = """
<section id="calc" class="card" data-default="{default}" aria-label="Grocery budget calculator">
  <h2 style="margin-top:0">Who's in your household?</h2>
  <div class="people"></div>
  <div class="row"><button type="button" id="addAdult">+ Add adult</button><button type="button" id="addChild">+ Add child</button></div>

  <div class="field"><label>Budget level</label>
    <div class="plans" role="radiogroup">
      <label><input type="radio" name="plan" value="thrifty"><span>Thrifty</span></label>
      <label><input type="radio" name="plan" value="low"><span>Low-Cost</span></label>
      <label><input type="radio" name="plan" value="moderate"><span>Moderate</span></label>
      <label><input type="radio" name="plan" value="liberal"><span>Liberal</span></label>
    </div>
    <div class="note">Thrifty is the tightest healthy budget, and USDA uses it to set SNAP benefits. Liberal allows more premium foods. Most families land around Low-Cost or Moderate.</div>
  </div>

  <div class="field"><label for="home">Share of meals eaten at home: <output id="homeOut">100%</output></label>
    <input id="home" type="range" min="10" max="100" step="5" value="100">
    <div class="note">USDA figures assume every meal is made at home. If you often eat out or get school or work meals, lower this.</div>
  </div>

  <div class="result" aria-live="polite">
    <div class="sub">Recommended grocery budget · <span id="resPlan">Moderate-Cost</span> plan · <span id="resSize"></span></div>
    <div class="big"><span id="resMonthly">{monthly}</span><span class="sub"> / month</span></div>
    <div class="grid3">
      <div><span class="sub">Per week</span><b id="resWeekly">{weekly}</b></div>
      <div><span class="sub">Per year</span><b id="resYearly">{yearly}</b></div>
      <div><span class="sub">Per person / mo</span><b id="resPer">{per}</b></div>
    </div>
    <div class="tablewrap"><table id="allPlans"><thead><tr><th>All four plans</th><th>Weekly</th><th>Monthly</th><th>Yearly</th></tr></thead><tbody>{rows}</tbody></table></div>
    <div class="field"><label for="spend">Compare with what you spend now ($/month, optional)</label>
      <input id="spend" type="number" min="0" step="10" inputmode="decimal" placeholder="e.g. 900">
      <div id="compare" class="compare"></div>
    </div>
    <p><button type="button" id="share" class="primary">Copy link to this budget</button></p>
  </div>
</section>
<script>window.GB_DATA={data};</script>
<script src="/calc.js" defer></script>
"""


def calc_block(people, plan="moderate"):
    t = D.household(people, plan)
    rows = ""
    for p in D.PLANS:
        x = D.household(people, p)
        cls = ' class="hl"' if p == plan else ""
        rows += f"<tr{cls}><td>{D.PLAN_NAMES[p]}</td><td>{money(x['weekly'])}</td><td>{money(x['monthly'])}</td><td>{money(x['yearly'])}</td></tr>"
    return CALC_HTML.format(
        default=hq(people), monthly=money(t["monthly"]), weekly=money(t["weekly"]),
        yearly=money(t["yearly"]), per=money(t["monthly"] / len(people)), rows=rows,
        data=json.dumps(D.js_data(), separators=(",", ":")))


# ---------------------------------------------------------------- pages

FAM4 = [(35, "m"), (35, "f"), (7, "f"), (10, "m")]
COUPLE = [(35, "m"), (35, "f")]


def home():
    f4 = D.household(FAM4, "moderate")
    single_f = D.household([(35, "f")], "moderate")
    single_m = D.household([(35, "m")], "moderate")
    thr4 = D.household(FAM4, "thrifty")
    body = f"""
<h1>Grocery Budget Calculator</h1>
<p class="lede">Find out how much your household should spend on groceries each week, month and year. Add each person's age, pick a budget level, and get a number based on the USDA's official food-cost data.</p>
<p class="updated">Updated with the USDA Cost of Food report for {M}.</p>
{calc_block(COUPLE)}

<h2>How this grocery budget calculator works</h2>
<p>Every month the U.S. Department of Agriculture prices a healthy, home-cooked diet for people of different ages and sexes. It publishes four <a href="/usda-food-plans-explained">food plans</a>: Thrifty, Low-Cost, Moderate-Cost and Liberal. This calculator follows the USDA's own method:</p>
<ol>
<li><strong>Look up each person.</strong> Each household member gets the USDA cost for their age and sex. A teenage boy costs far more to feed than a toddler.</li>
<li><strong>Add the costs together.</strong> The individual costs are summed into a household total.</li>
<li><strong>Adjust for household size.</strong> USDA's per-person figures assume a family of four. Smaller households pay more per person because they buy smaller packages and waste more, so the total goes up 20% for one person, 10% for two and 5% for three. It goes down 5% for five or six people and 10% for seven or more.</li>
<li><strong>Adjust for eating out (optional).</strong> If some meals come from restaurants, school or work, lower the "meals at home" slider so you don't budget twice for the same food.</li>
</ol>

<h2>Average grocery budgets at a glance ({M})</h2>
<div class="tablewrap"><table><thead><tr><th>Household (Moderate-Cost plan)</th><th>Weekly</th><th>Monthly</th></tr></thead><tbody>
<tr><td><a href="/grocery-budget-for-one-person">Single woman, 19–50</a></td><td>{money(single_f['weekly'])}</td><td>{money(single_f['monthly'])}</td></tr>
<tr><td><a href="/grocery-budget-for-one-person">Single man, 19–50</a></td><td>{money(single_m['weekly'])}</td><td>{money(single_m['monthly'])}</td></tr>
<tr><td><a href="/grocery-budget-for-two">Couple, 19–50</a></td><td>{money(D.household(COUPLE,'moderate')['weekly'])}</td><td>{money(D.household(COUPLE,'moderate')['monthly'])}</td></tr>
<tr><td><a href="/grocery-budget-for-family-of-3">Family of 3 (one child, 6–8)</a></td><td>{money(D.household(FAM3,'moderate')['weekly'])}</td><td>{money(D.household(FAM3,'moderate')['monthly'])}</td></tr>
<tr><td><a href="/grocery-budget-for-family-of-4">Family of 4 (children 6–8 and 9–11)</a></td><td>{money(f4['weekly'])}</td><td>{money(f4['monthly'])}</td></tr>
<tr><td><a href="/grocery-budget-for-family-of-5">Family of 5 (three children)</a></td><td>{money(D.household(FAM5,'moderate')['weekly'])}</td><td>{money(D.household(FAM5,'moderate')['monthly'])}</td></tr>
</tbody></table></div>
<p>A family of four on the tightest healthy budget (Thrifty) needs about <strong>{money(thr4['monthly'])} a month</strong>. That matches USDA's reference family figure.</p>

<h2>Which budget level should you choose?</h2>
<ul>
<li><strong>Thrifty:</strong> mostly cooking from scratch, store brands, beans, rice, frozen vegetables, and very little food waste. It's realistic, but it takes planning.</li>
<li><strong>Low-Cost:</strong> careful shopping with a few conveniences and branded items.</li>
<li><strong>Moderate-Cost:</strong> a comfortable everyday budget with more fresh produce, meat and some prepared foods.</li>
<li><strong>Liberal:</strong> premium cuts, organic choices, specialty items and more convenience food.</li>
</ul>
<p>Not sure? Enter what you spend now in the comparison box above to see which plan you already match, then aim one level lower if you want to save.</p>

<h2>Tips to bring your grocery bill down</h2>
<ul>
<li>Plan meals for the week before you shop, and build them around what's on sale.</li>
<li>Shop with a list and a firm weekly limit, which is your weekly figure above.</li>
<li>Buy store brands for staples like flour, oats, canned tomatoes, milk and frozen vegetables.</li>
<li>Cook once, eat twice: plan leftovers on purpose to cut waste.</li>
<li>Track every receipt for a month. Most people underestimate their grocery spending by a lot.</li>
</ul>
<p>More ideas: <a href="/how-much-should-i-spend-on-groceries">How much should I spend on groceries?</a></p>
"""
    faq = [
        ("How much should I budget for groceries per month?",
         f"Based on the USDA Moderate-Cost plan for {M}, a single adult (19–50) needs about {money(single_f['monthly'])}–{money(single_m['monthly'])} a month, a couple about {money(D.household(COUPLE,'moderate')['monthly'])}, and a family of four about {money(f4['monthly'])}. Use the calculator above for your household's exact ages."),
        ("Where do these numbers come from?",
         f"From the USDA Food Plans: Cost of Food at Home reports, which the USDA updates every month for food-price inflation. This page uses the {M} report."),
        ("Does the budget include eating out?",
         "No. USDA figures cover food and drinks prepared at home only. Restaurant meals, takeout and alcohol are separate. Use the meals-at-home slider if you eat some meals outside the home."),
        ("Do prices differ by state?",
         "Yes. The USDA figures are U.S. averages. High-cost areas such as Alaska, Hawaii, California and big cities usually cost more, and lower-cost regions often cost less. Treat the result as a starting point and adjust it after tracking a month of receipts."),
        ("Does it include household items like paper towels?",
         "No. The USDA food plans cover food only. Budget separately for cleaning supplies, toiletries, paper goods and pet food, even if you buy them at the grocery store."),
    ]
    app_ld = {"@context": "https://schema.org", "@type": "WebApplication", "name": SITE_NAME,
              "url": SITE_URL + "/", "applicationCategory": "FinanceApplication", "operatingSystem": "Any",
              "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
              "description": "Free grocery budget calculator based on USDA food plan costs."}
    return page("/", f"Grocery Budget Calculator ({YEAR}) – Weekly & Monthly, USDA-Based",
                f"Free grocery budget calculator using official USDA {M} food costs. Enter your household's ages to get a weekly, monthly and yearly grocery budget.",
                body, faq, app_ld)


FAM3 = [(35, "m"), (35, "f"), (7, "f")]
FAM5 = [(38, "m"), (36, "f"), (12, "m"), (9, "f"), (5, "m")]

HOUSEHOLDS = {
    "grocery-budget-for-one-person": {
        "h1": "Grocery Budget for One Person",
        "title": f"Grocery Budget for One Person ({YEAR}): Weekly & Monthly",
        "crumb": "One person",
        "people": [(35, "f")],
        "alt": [("Single woman 19–50", [(35, "f")]), ("Single man 19–50", [(35, "m")]),
                ("Single woman 51–70", [(60, "f")]), ("Single man 51–70", [(60, "m")]),
                ("Single adult 71+ (woman)", [(75, "f")]), ("Single adult 71+ (man)", [(75, "m")])],
        "intro": "Cooking for one costs more per person than cooking for a family. Packages are sized for households, and it's harder to use everything before it spoils. That's why the USDA adds 20% to a single person's food cost. Here's what one adult should budget at each level.",
        "tips": [
            "Freeze half of every loaf of bread and pack of meat as soon as you get home.",
            "Pick recipes that share ingredients across the week, e.g. one bag of spinach for omelets, pasta and a salad.",
            "Buy loose produce by the piece instead of pre-bagged.",
            "Cook a big batch on the weekend and freeze single portions instead of buying ready meals.",
        ],
    },
    "grocery-budget-for-two": {
        "h1": "Grocery Budget for Two People",
        "title": f"Grocery Budget for 2 People ({YEAR}): Couple's Weekly & Monthly",
        "crumb": "Two people",
        "people": COUPLE,
        "alt": [("Couple 19–50", COUPLE), ("Couple 51–70", [(60, "m"), (60, "f")]),
                ("Couple 71+", [(75, "m"), (73, "f")]), ("Two women 19–50", [(30, "f"), (30, "f")]),
                ("Two men 19–50", [(30, "m"), (30, "m")]), ("Single parent + child 6–8", [(35, "f"), (7, "m")])],
        "intro": "A two-person household gets a 10% size adjustment in the USDA method. You buy in slightly better quantities than a single person, but still pay more per head than a family of four. Here's what a couple should budget.",
        "tips": [
            "Split bulk packs (meat, cheese, bread) and freeze half right away.",
            "Agree on one weekly budget number and one shared list, because two people shopping separately overspend.",
            "Plan two or three “cook once, eat twice” dinners a week for lunches.",
            "Warehouse clubs only pay off if you'll finish the big packs. Compare unit prices first.",
        ],
    },
    "grocery-budget-for-family-of-3": {
        "h1": "Grocery Budget for a Family of 3",
        "title": f"Grocery Budget for a Family of 3 ({YEAR}): Weekly & Monthly",
        "crumb": "Family of 3",
        "people": FAM3,
        "alt": [("Two adults + child 1 year", [(32, "m"), (30, "f"), (1, "f")]),
                ("Two adults + child 4–5", [(35, "m"), (35, "f"), (4, "m")]),
                ("Two adults + child 6–8", FAM3),
                ("Two adults + teen boy 14–18", [(45, "m"), (43, "f"), (16, "m")]),
                ("Single parent + two children (6–8, 9–11)", [(38, "f"), (7, "m"), (10, "f")])],
        "intro": "For a family of three, the child's age changes the budget the most. A toddler eats a fraction of what a teenager does. USDA adds a 5% size adjustment for three-person households. Here are typical budgets for common family-of-3 setups.",
        "tips": [
            "Make one family meal instead of separate kids' food, and adjust spice at the table.",
            "Buy snacks in large tubs and portion them yourself instead of buying single-serve packs.",
            "Check whether your child's school offers free or reduced-price meals, then lower the meals-at-home slider.",
            "Keep a “use it up” shelf in the fridge for leftovers and food close to expiring.",
        ],
    },
    "grocery-budget-for-family-of-4": {
        "h1": "Grocery Budget for a Family of 4",
        "title": f"Grocery Budget for a Family of 4 ({YEAR}): USDA Weekly & Monthly",
        "crumb": "Family of 4",
        "people": FAM4,
        "alt": [("2 adults + children 6–8 & 9–11 (USDA reference)", FAM4),
                ("2 adults + children 2–3 & 4–5", [(33, "m"), (32, "f"), (2, "f"), (5, "m")]),
                ("2 adults + teens 14–18 (boy & girl)", [(46, "m"), (44, "f"), (15, "m"), (17, "f")]),
                ("2 adults + two teen boys", [(46, "m"), (44, "f"), (15, "m"), (17, "m")]),
                ("Single parent + three children", [(40, "f"), (6, "m"), (9, "f"), (13, "m")])],
        "intro": "The family of four is the USDA's reference household: a man and woman aged 19–50 with two children aged 6–8 and 9–11. No size adjustment applies. Here is what that family, and other common family-of-four setups, should spend on groceries.",
        "tips": [
            "Plan a weekly rotation (taco night, pasta night, soup night) so shopping is repeatable and predictable.",
            "Buy proteins in family packs on sale and portion and freeze them.",
            "Pack school lunches from dinner leftovers to avoid buying pricey lunch kits.",
            "Expect the budget to jump when kids hit their teens. A teen boy costs more to feed than an adult on most plans.",
        ],
    },
    "grocery-budget-for-family-of-5": {
        "h1": "Grocery Budget for a Family of 5",
        "title": f"Grocery Budget for a Family of 5 ({YEAR}): Weekly & Monthly",
        "crumb": "Family of 5",
        "people": FAM5,
        "alt": [("2 adults + children 5, 9, 12", FAM5),
                ("2 adults + three young children (1–5)", [(34, "m"), (33, "f"), (1, "m"), (3, "f"), (5, "m")]),
                ("2 adults + three teens", [(47, "m"), (45, "f"), (14, "m"), (16, "f"), (18, "m")]),
                ("Single parent + four children", [(40, "f"), (4, "m"), (7, "f"), (10, "m"), (13, "f")])],
        "intro": "Larger families get a small break: USDA reduces the total by 5% for households of five or six because buying in bulk and cooking in volume is more efficient. Here's what a family of five should budget.",
        "tips": [
            "A warehouse club membership usually pays off at this size for staples, eggs, milk and frozen produce.",
            "Cook double batches of chili, soups and casseroles and freeze the second one.",
            "Make breakfast cheap and filling: oats, eggs, pancakes from scratch.",
            "Give older kids a role in meal planning. It cuts waste and “there's nothing to eat” trips.",
        ],
    },
}


def household_page(slug, h):
    people = h["people"]
    mod = D.household(people, "moderate")
    thr = D.household(people, "thrifty")
    lib = D.household(people, "liberal")
    alt_rows = ""
    for label, ppl in h["alt"]:
        t = D.household(ppl, "thrifty")["monthly"], D.household(ppl, "low")["monthly"], D.household(ppl, "moderate")["monthly"], D.household(ppl, "liberal")["monthly"]
        alt_rows += f"<tr><td><a href='/?h={hq(ppl)}&amp;p=moderate'>{label}</a></td>" + "".join(f"<td>{money(x)}</td>" for x in t) + "</tr>"
    def who(a, s):
        if a >= 19:
            return "man" if s == "m" else "woman"
        return "boy" if s == "m" else "girl"
    people_desc = ", ".join(f"{who(a, s)} age {a}" for a, s in people)
    tips = "".join(f"<li>{t}</li>" for t in h["tips"])
    others = "".join(f'<li><a href="/{s}">{v["h1"]}</a></li>' for s, v in HOUSEHOLDS.items() if s != slug)
    body = f"""
<h1>{h['h1']}</h1>
<p class="lede">{h['intro']}</p>
<p class="updated">Based on USDA Cost of Food at Home, {M}.</p>
<div class="card">
<p style="margin-top:0"><strong>Quick answer:</strong> on the USDA Moderate-Cost plan, budget about <strong>{money(mod['monthly'])} a month</strong> ({money(mod['weekly'])} a week). The range runs from {money(thr['monthly'])} on the Thrifty plan to {money(lib['monthly'])} on the Liberal plan.</p>
{plan_table(people)}
<p class="note">Example household: {people_desc}. All meals prepared at home, U.S. average prices.</p>
<a class="cta" href="/?h={hq(people)}&amp;p=moderate">Adjust ages in the calculator →</a>
</div>

<h2>Monthly budget for other household setups</h2>
<div class="tablewrap"><table><thead><tr><th>Household</th><th>Thrifty</th><th>Low-Cost</th><th>Moderate</th><th>Liberal</th></tr></thead><tbody>{alt_rows}</tbody></table></div>
<p class="note">Click any row to open it in the calculator and change the ages.</p>

<h2>How to make this budget work</h2>
<ul>{tips}</ul>

<h2>What the budget covers and what it doesn't</h2>
<p>USDA food plans cover food and non-alcoholic drinks bought at a store and prepared at home. They don't include restaurant meals, takeout, alcohol, pet food, or non-food items like paper towels and cleaning supplies. If your family eats out regularly, lower the meals-at-home slider in the <a href="/">calculator</a> so you don't double-count.</p>
<h3>More household sizes</h3>
<ul class="links">{others}<li><a href="/how-much-should-i-spend-on-groceries">How much should I spend on groceries?</a></li></ul>
"""
    faq = [
        (f"Is {money(mod['monthly'])} a month a lot for this household?",
         f"It's the USDA Moderate-Cost level, a middle-of-the-road budget. Households that cook from scratch and shop sales can get close to the Thrifty level of {money(thr['monthly'])}."),
        ("Why is the per-person cost different from the USDA table?",
         "USDA per-person costs assume a four-person household. The calculator applies USDA's official size adjustment: +20% for 1 person, +10% for 2, +5% for 3, −5% for 5–6 and −10% for 7 or more."),
        ("How often are these numbers updated?",
         f"USDA publishes new costs every month. This page currently uses the {M} report."),
    ]
    return page("/" + slug, h["title"],
                f"How much should {h['h1'].replace('Grocery Budget for ','').lower()} spend on groceries? USDA {M} figures: about {money(mod['monthly'])}/month on the Moderate plan, from {money(thr['monthly'])} (Thrifty) to {money(lib['monthly'])} (Liberal).",
                body, faq, crumbs=h["crumb"])


def spend_page():
    f4 = D.household(FAM4, "moderate")
    body = f"""
<h1>How Much Should I Spend on Groceries?</h1>
<p class="lede">There's no single right number, but there are three good ways to find yours. The most reliable is the USDA's food plan for your household's ages, which the <a href="/">grocery budget calculator</a> works out for you.</p>
<p class="updated">Figures from USDA Cost of Food at Home, {M}.</p>

<h2>Method 1: the USDA food plans (most accurate)</h2>
<p>The USDA prices a healthy diet every month for each age and sex at four budget levels. Add up your household and apply the size adjustment. For example, a family of four with two school-age children needs about <strong>{money(D.household(FAM4,'thrifty')['monthly'])}</strong> a month on the Thrifty plan and <strong>{money(f4['monthly'])}</strong> on the Moderate-Cost plan.</p>
<a class="cta" href="/">Calculate your household's USDA budget →</a>

<h2>Method 2: start from your income</h2>
<p>Many budgeting frameworks, such as 50/30/20, put groceries in the “needs” half of your take-home pay alongside housing, utilities and transportation. Groceries have no fixed percentage, but if they take a large share of your take-home pay, use the Thrifty or Low-Cost plan as your target until other costs come down.</p>

<h2>Method 3: track, then trim</h2>
<ol>
<li>Save every grocery receipt for four weeks, including quick trips for milk.</li>
<li>Add them up to get your real monthly number. Most people are surprised.</li>
<li>Compare it with the USDA levels in the calculator's comparison box.</li>
<li>Set next month's budget one level lower, or cut 10%, and split it into weekly amounts.</li>
</ol>

<h2>Budget by household size ({M}, Moderate-Cost)</h2>
<div class="tablewrap"><table><thead><tr><th>Household</th><th>Weekly</th><th>Monthly</th></tr></thead><tbody>
""" + "".join(
        f"<tr><td><a href='/{s}'>{v['h1'].replace('Grocery Budget for ', '').capitalize()}</a></td><td>{money(D.household(v['people'],'moderate')['weekly'])}</td><td>{money(D.household(v['people'],'moderate')['monthly'])}</td></tr>"
        for s, v in HOUSEHOLDS.items()) + f"""
</tbody></table></div>

<h2>Signs your grocery budget is too high</h2>
<ul>
<li>You regularly throw away produce, leftovers or dairy.</li>
<li>You shop more than twice a week without a list.</li>
<li>Pre-cut, pre-marinated and single-serve items fill most of your cart.</li>
<li>Your total is above the USDA Liberal plan for your household.</li>
</ul>
<h2>Signs it may be too low</h2>
<ul>
<li>You're well below the Thrifty plan and skipping fruit, vegetables or protein.</li>
<li>Kids are often hungry between meals.</li>
<li>You put everything on a credit card and run out before payday.</li>
</ul>
<p>If money for food is tight, the USDA's SNAP program and local food banks can help. Your state's SNAP office can tell you whether you qualify.</p>
"""
    faq = [
        ("What is a reasonable grocery budget for one person?",
         f"About {money(D.household([(35,'f')],'thrifty')['monthly'])}–{money(D.household([(35,'m')],'moderate')['monthly'])} a month for an adult aged 19–50, depending on sex and on whether you follow the USDA Thrifty or Moderate-Cost plan. See <a href='/grocery-budget-for-one-person'>grocery budget for one person</a>."),
        ("Is $200 a week enough for a family of four?",
         f"It's below the USDA Thrifty plan for the reference family of four ({money(D.household(FAM4,'thrifty')['weekly'])} a week in {M}). It's doable with young children and strict scratch cooking, but tight with older kids."),
        ("Should groceries include toiletries and cleaning supplies?",
         "For budgeting it's clearer to keep them separate. USDA food plans cover food only, so a separate household-supplies line makes the comparison fair."),
    ]
    return page("/how-much-should-i-spend-on-groceries", f"How Much Should I Spend on Groceries? ({YEAR} Guide)",
                f"Three ways to set a grocery budget: USDA food plans, income-based budgeting, and tracking. Includes {M} weekly and monthly figures by household size.",
                body, faq, crumbs="How much to spend")


def plans_page():
    def full_table():
        head = "<tr><th>Age / sex group</th>" + "".join(f"<th>{D.PLAN_NAMES[p]}</th>" for p in D.PLANS) + "</tr>"
        rows = ""
        thr = D.rows_for("thrifty")
        for i, r in enumerate(D.LML):
            label = r[0]
            t = thr[i]
            tl = "" if t[0] == label else f" <span class='note'>(Thrifty: {t[0].split(' ',1)[1]})</span>"
            rows += f"<tr><td>{label}{tl}</td><td>{money(t[5])}</td><td>{money(r[4][1])}</td><td>{money(r[5][1])}</td><td>{money(r[6][1])}</td></tr>"
        return f"<div class='tablewrap'><table><thead>{head}</thead><tbody>{rows}</tbody></table></div>"

    body = f"""
<h1>USDA Food Plans Explained ({M})</h1>
<p class="lede">The USDA Food Plans are the official estimates of what a nutritious, home-cooked diet costs in the U.S. They power this site's <a href="/">grocery budget calculator</a>. Here's what they are, how they're built, and the full {M} cost table.</p>

<h2>The four plans</h2>
<ul>
<li><strong>Thrifty Food Plan:</strong> the lowest-cost healthy diet. It's the basis for maximum SNAP (food stamp) benefits, and USDA last reevaluated it in 2021.</li>
<li><strong>Low-Cost plan:</strong> a step up, with more variety and convenience.</li>
<li><strong>Moderate-Cost plan:</strong> a middle-income everyday budget.</li>
<li><strong>Liberal plan:</strong> the highest-cost plan, with premium and convenience foods.</li>
</ul>
<p>All four describe a diet that meets dietary guidelines with every meal and snack prepared at home. USDA updates the costs every month for inflation using the Consumer Price Index.</p>

<h2>Monthly cost per person, {M}</h2>
{full_table()}
<p class="note">Monthly costs per person, U.S. average, rounded to the nearest dollar. The Thrifty plan uses slightly different teen/adult age brackets (14–19 and 20–50) than the other three plans (14–18 and 19–50). Figures assume a four-person household. Apply the size adjustment below for other household sizes.</p>

<h2>Household size adjustment</h2>
<div class="tablewrap"><table><thead><tr><th>Household size</th><th>Adjustment to total</th></tr></thead><tbody>
<tr><td>1 person</td><td>+20%</td></tr><tr><td>2 people</td><td>+10%</td></tr><tr><td>3 people</td><td>+5%</td></tr>
<tr><td>4 people</td><td>none</td></tr><tr><td>5–6 people</td><td>−5%</td></tr><tr><td>7 or more</td><td>−10%</td></tr></tbody></table></div>
<p>To estimate a household budget, add each member's individual cost first, then apply the adjustment. The calculator does this automatically.</p>

<h2>Limitations to keep in mind</h2>
<ul>
<li>Costs are national averages, so local prices can be noticeably higher or lower.</li>
<li>Weekly figures × 4.333 = monthly figures (USDA's convention).</li>
<li>The plans assume everything is cooked at home with no restaurant or takeout food.</li>
<li>Special diets (gluten-free, allergies, medical diets) can cost more than any plan shows.</li>
</ul>
<p>Source: <a href="{D.REPORT_URL}" rel="nofollow">USDA FNS, Official USDA Food Plans: Cost of Food Monthly Reports</a>.</p>
"""
    faq = [
        ("What is the USDA Thrifty Food Plan?",
         "It is the USDA's estimate of the cost of a healthy, low-cost diet prepared at home. It is used to set maximum SNAP benefit amounts."),
        ("How often does USDA update the food plan costs?",
         "Every month, using Consumer Price Index data for specific food items."),
    ]
    return page("/usda-food-plans-explained", f"USDA Food Plans Explained: Cost of Food Table ({M})",
                f"What the USDA Thrifty, Low-Cost, Moderate-Cost and Liberal food plans are, with the full {M} monthly cost table by age and sex and the household size adjustments.",
                body, faq, crumbs="USDA food plans")


def simple(path, title, h1, content, desc):
    return page(path, title, desc, f"<h1>{h1}</h1>{content}", crumbs=h1)


def about():
    return simple("/about", f"About – {SITE_NAME}", "About this site", f"""
<p>{SITE_NAME} is a free tool that helps U.S. households set a realistic grocery budget. Instead of guessing or copying someone else's number, you get an estimate built from the USDA's official monthly food-cost data, adjusted for your household's ages and size.</p>
<h2>Why we built it</h2>
<p>Most grocery budget advice gives one flat number for everyone. A toddler and a teenager cost very different amounts to feed, and a person living alone pays more per meal than a family of four. The USDA already publishes the data to account for this. We made it quick to use.</p>
<h2>How we keep it accurate</h2>
<p>We update the figures when USDA releases each monthly Cost of Food report and show the report month on every page. Our method is explained on the <a href="/usda-food-plans-explained">USDA food plans</a> page.</p>
<p>The calculator gives planning estimates, not financial advice. Prices in your area and your family's needs may differ.</p>
""", f"About {SITE_NAME}: a free USDA-based tool for planning household grocery budgets.")


def contact():
    email = (f'<p>Email: <a href="mailto:{CONTACT_EMAIL}">{CONTACT_EMAIL}</a></p>' if CONTACT_EMAIL
             else "<p>Email: (address coming soon)</p>")
    return simple("/contact", f"Contact – {SITE_NAME}", "Contact us", f"""
<p>Found a mistake, have a suggestion, or want a calculator for a specific situation? We'd like to hear from you.</p>
{email}
<p>We usually reply within a few business days. We can't give personal financial advice.</p>
""", f"Contact {SITE_NAME}.")


def privacy():
    return simple("/privacy-policy", f"Privacy Policy – {SITE_NAME}", "Privacy Policy", f"""
<p class="updated">Last updated: {TODAY}</p>
<p>This policy explains what information {SITE_NAME} ("we") collects when you use {SITE_URL} and how it's used.</p>
<h2>Calculator inputs</h2>
<p>The calculator runs entirely in your browser. The ages, budget level and spending amounts you enter are not sent to or stored on our servers. They appear only in your page's web address so you can share or bookmark a result.</p>
<h2>Analytics and logs</h2>
<p>Our hosting provider may keep standard server logs (such as IP address, browser type and pages visited) for security and performance. We may use privacy-friendly analytics to count visits. This data is aggregated and not used to identify you.</p>
<h2>Advertising and cookies</h2>
<p>We may show ads from third-party vendors, including Google. Third-party vendors, including Google, use cookies to serve ads based on a user's prior visits to this website or other websites. Google's use of advertising cookies enables it and its partners to serve ads to users based on their visit to this site and/or other sites on the Internet.</p>
<p>You may opt out of personalized advertising by visiting <a href="https://www.google.com/settings/ads" rel="nofollow">Google Ads Settings</a>, or opt out of some third-party vendors' use of cookies for personalized advertising at <a href="https://www.aboutads.info/choices/" rel="nofollow">www.aboutads.info</a>. Where required by law (for example in the EEA, UK and some U.S. states), we'll ask for your consent before using cookies for advertising.</p>
<h2>Children</h2>
<p>This site is intended for adults managing a household budget and isn't directed to children under 13.</p>
<h2>Changes and contact</h2>
<p>We may update this policy from time to time. The date above shows the latest version. Questions? See our <a href="/contact">contact page</a>.</p>
""", f"Privacy policy for {SITE_NAME}.")


def build():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    pages = {"/": home(), "/how-much-should-i-spend-on-groceries": spend_page(),
             "/usda-food-plans-explained": plans_page(), "/about": about(),
             "/contact": contact(), "/privacy-policy": privacy()}
    for slug, h in HOUSEHOLDS.items():
        pages["/" + slug] = household_page(slug, h)
    for path, content in pages.items():
        fn = os.path.join(OUT, "index.html" if path == "/" else path.strip("/") + ".html")
        with open(fn, "w") as f:
            f.write(content)
    for name in ("style.css", "calc.js"):
        shutil.copy(os.path.join(SRC, name), OUT)
    with open(os.path.join(OUT, "favicon.svg"), "w") as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">🛒</text></svg>')
    with open(os.path.join(OUT, "robots.txt"), "w") as f:
        f.write("User-agent: *" + NL + "Allow: /" + NL + NL + "Sitemap: " + SITE_URL + "/sitemap.xml" + NL)
    urls = "".join(f"<url><loc>{SITE_URL}{p if p != '/' else '/'}</loc><lastmod>{TODAY}</lastmod></url>" for p in pages)
    with open(os.path.join(OUT, "sitemap.xml"), "w") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    with open(os.path.join(OUT, "404.html"), "w") as f:
        f.write(page("/404", "Page not found", "Page not found", '<h1>Page not found</h1><p><a href="/">Go to the grocery budget calculator →</a></p>'))
    print(f"Built {len(pages)} pages -> {OUT}")


if __name__ == "__main__":
    build()
