"""USDA Food Plans: Cost of Food at Home, U.S. Average.

Source: USDA FNS monthly Cost of Food reports, October 2026
  Thrifty:  https://fns-prod.azureedge.us/sites/default/files/resource-files/CostofFoodOct2026Thrifty.pdf
  Low/Mod/Liberal: https://fns-prod.azureedge.us/sites/default/files/resource-files/CostofFoodOct2026LowModLib.pdf

To update each month: replace the numbers below with the new report, change
REPORT_MONTH, and run `python3 src/build.py`.
"""

REPORT_MONTH = "October 2026"
REPORT_URL = "https://www.fns.usda.gov/cnpp/usda-food-plans-cost-food-monthly-reports"

PLANS = ["thrifty", "low", "moderate", "liberal"]
PLAN_NAMES = {
    "thrifty": "Thrifty",
    "low": "Low-Cost",
    "moderate": "Moderate-Cost",
    "liberal": "Liberal",
}

# Each row: (group label, sex 'any'|'f'|'m', min_age, max_age, {plan: (weekly, monthly)})
# Thrifty uses 14-19 / 20-50 brackets; the other three use 14-18 / 19-50,
# so teen/adult rows are stored per plan family.
THRIFTY = [
    ("Child 1 year", "any", 0, 1, (26.40, 114.20)),
    ("Child 2-3 years", "any", 2, 3, (39.80, 172.60)),
    ("Child 4-5 years", "any", 4, 5, (43.50, 188.50)),
    ("Child 6-8 years", "any", 6, 8, (48.30, 209.30)),
    ("Child 9-11 years", "any", 9, 11, (55.80, 242.00)),
    ("Female 12-13", "f", 12, 13, (51.70, 223.90)),
    ("Female 14-19", "f", 14, 19, (60.10, 260.50)),
    ("Female 20-50", "f", 20, 50, (58.70, 254.20)),
    ("Female 51-70", "f", 51, 70, (54.60, 236.60)),
    ("Female 71+", "f", 71, 200, (60.30, 261.40)),
    ("Male 12-13", "m", 12, 13, (59.70, 258.60)),
    ("Male 14-19", "m", 14, 19, (75.30, 326.50)),
    ("Male 20-50", "m", 20, 50, (73.70, 319.10)),
    ("Male 51-70", "m", 51, 70, (65.00, 281.70)),
    ("Male 71+", "m", 71, 200, (62.00, 268.70)),
]

# (label, sex, min, max, low(w,m), moderate(w,m), liberal(w,m))
LML = [
    ("Child 1 year", "any", 0, 1, (38.30, 165.80), (43.10, 186.90), (52.40, 227.10)),
    ("Child 2-3 years", "any", 2, 3, (40.10, 173.80), (47.90, 207.70), (58.30, 252.80)),
    ("Child 4-5 years", "any", 4, 5, (41.40, 179.50), (51.30, 222.40), (62.00, 268.80)),
    ("Child 6-8 years", "any", 6, 8, (60.50, 262.10), (70.50, 305.60), (82.60, 357.80)),
    ("Child 9-11 years", "any", 9, 11, (62.60, 271.40), (81.00, 351.20), (94.60, 409.80)),
    ("Female 12-13", "f", 12, 13, (62.30, 269.90), (74.50, 322.90), (92.70, 401.70)),
    ("Female 14-18", "f", 14, 18, (62.60, 271.40), (74.50, 322.70), (92.30, 399.80)),
    ("Female 19-50", "f", 19, 50, (63.90, 277.00), (77.80, 337.00), (99.30, 430.20)),
    ("Female 51-70", "f", 51, 70, (62.20, 269.40), (76.60, 331.90), (92.40, 400.40)),
    ("Female 71+", "f", 71, 200, (62.10, 269.00), (76.40, 331.20), (91.40, 395.90)),
    ("Male 12-13", "m", 12, 13, (73.20, 317.20), (90.80, 393.50), (106.60, 462.00)),
    ("Male 14-18", "m", 14, 18, (74.50, 323.00), (93.20, 403.70), (109.60, 475.00)),
    ("Male 19-50", "m", 19, 50, (73.50, 318.50), (92.10, 398.90), (112.30, 486.80)),
    ("Male 51-70", "m", 51, 70, (69.20, 299.90), (86.80, 376.00), (103.90, 450.40)),
    ("Male 71+", "m", 71, 200, (68.40, 296.40), (84.30, 365.30), (103.60, 448.70)),
]

# Household-size adjustment (USDA: table costs assume a 4-person household).
SIZE_ADJ = {1: 1.20, 2: 1.10, 3: 1.05, 4: 1.00, 5: 0.95, 6: 0.95}  # 7+ -> 0.90


def size_factor(n):
    if n <= 0:
        return 1.0
    return SIZE_ADJ.get(n, 0.90)


def rows_for(plan):
    """Return list of (label, sex, min, max, weekly, monthly) for a plan."""
    if plan == "thrifty":
        return [(l, s, a, b, w, m) for (l, s, a, b, (w, m)) in THRIFTY]
    idx = {"low": 4, "moderate": 5, "liberal": 6}[plan]
    return [(r[0], r[1], r[2], r[3], r[idx][0], r[idx][1]) for r in LML]


def person_cost(plan, age, sex):
    for (label, s, a, b, w, m) in rows_for(plan):
        if a <= age <= b and (s == "any" or s == sex):
            return label, w, m
    raise ValueError(f"no row for {plan} {age} {sex}")


def household(people, plan, home_share=1.0):
    """people: list of (age, sex). Returns dict with weekly, monthly, yearly."""
    f = size_factor(len(people))
    w = sum(person_cost(plan, a, s)[1] for a, s in people) * f * home_share
    m = sum(person_cost(plan, a, s)[2] for a, s in people) * f * home_share
    return {"weekly": w, "monthly": m, "yearly": m * 12}


def js_data():
    """Compact data object for the browser calculator."""
    out = {}
    for p in PLANS:
        out[p] = [[l, s, a, b, w, m] for (l, s, a, b, w, m) in rows_for(p)]
    return out
