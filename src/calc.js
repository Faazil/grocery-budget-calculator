(function () {
  var D = window.GB_DATA, PLANS = ["thrifty", "low", "moderate", "liberal"];
  var NAMES = { thrifty: "Thrifty", low: "Low-Cost", moderate: "Moderate-Cost", liberal: "Liberal" };
  var root = document.getElementById("calc");
  if (!root || !D) return;

  var peopleEl = root.querySelector(".people");
  var homeEl = root.querySelector("#home");
  var homeOut = root.querySelector("#homeOut");
  var spendEl = root.querySelector("#spend");
  var state = { people: [], plan: "moderate" };

  function money(n) {
    return "$" + Math.round(n).toLocaleString("en-US");
  }
  function sizeFactor(n) {
    return n <= 1 ? 1.2 : n === 2 ? 1.1 : n === 3 ? 1.05 : n === 4 ? 1 : n <= 6 ? 0.95 : 0.9;
  }
  function row(plan, age, sex) {
    var rows = D[plan];
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      if (age >= r[2] && age <= r[3] && (r[1] === "any" || r[1] === sex)) return r;
    }
    return rows[rows.length - 1];
  }
  function totals(plan) {
    var f = sizeFactor(state.people.length), h = Number(homeEl.value) / 100, w = 0, m = 0;
    state.people.forEach(function (p) {
      var r = row(plan, p.age, p.sex);
      w += r[4];
      m += r[5];
    });
    return { weekly: w * f * h, monthly: m * f * h, yearly: m * f * h * 12 };
  }

  function personRow(p, i) {
    var d = document.createElement("div");
    d.className = "person";
    d.innerHTML =
      '<div class="who"><label>Person ' + (i + 1) + '</label><strong>' + (p.age < 12 ? "Child" : p.age < 19 ? "Teen" : "Adult") + "</strong></div>" +
      '<div><label for="age' + i + '">Age</label><input id="age' + i + '" type="number" min="1" max="110" inputmode="numeric" value="' + p.age + '"></div>' +
      '<div><label for="sex' + i + '">Sex</label><select id="sex' + i + '"><option value="f">Female</option><option value="m">Male</option></select></div>' +
      '<div><label>&nbsp;</label><button type="button" class="rm" aria-label="Remove person ' + (i + 1) + '">✕</button></div>';
    d.querySelector("select").value = p.sex;
    d.querySelector("input").addEventListener("input", function (e) {
      var v = parseInt(e.target.value, 10);
      if (!isNaN(v)) { state.people[i].age = Math.max(1, Math.min(110, v)); update(false); }
    });
    d.querySelector("select").addEventListener("change", function (e) { state.people[i].sex = e.target.value; update(false); });
    d.querySelector(".rm").addEventListener("click", function () {
      if (state.people.length > 1) { state.people.splice(i, 1); update(true); }
    });
    return d;
  }

  function render() {
    peopleEl.innerHTML = "";
    state.people.forEach(function (p, i) { peopleEl.appendChild(personRow(p, i)); });
  }

  function update(rerender) {
    if (rerender) render();
    homeOut.textContent = homeEl.value + "%";
    var t = totals(state.plan), n = state.people.length;
    root.querySelector("#resMonthly").textContent = money(t.monthly);
    root.querySelector("#resWeekly").textContent = money(t.weekly);
    root.querySelector("#resYearly").textContent = money(t.yearly);
    root.querySelector("#resPer").textContent = money(t.monthly / n);
    root.querySelector("#resPlan").textContent = NAMES[state.plan];
    root.querySelector("#resSize").textContent = n + (n === 1 ? " person" : " people");

    var tb = root.querySelector("#allPlans tbody"), html = "", all = {};
    PLANS.forEach(function (p) {
      var x = totals(p);
      all[p] = x;
      html += '<tr' + (p === state.plan ? ' class="hl"' : "") + "><td>" + NAMES[p] + "</td><td>" + money(x.weekly) + "</td><td>" + money(x.monthly) + "</td><td>" + money(x.yearly) + "</td></tr>";
    });
    tb.innerHTML = html;

    var cmp = root.querySelector("#compare"), s = parseFloat(spendEl.value);
    if (!isNaN(s) && s > 0) {
      var msg;
      if (s < all.thrifty.monthly) msg = "You spend " + money(all.thrifty.monthly - s) + " less than the USDA Thrifty plan. That's very lean, so check that everyone is getting enough.";
      else if (s <= all.low.monthly) msg = "Your spending sits between the Thrifty and Low-Cost plans. That's a tight but realistic budget.";
      else if (s <= all.moderate.monthly) msg = "Your spending sits between the Low-Cost and Moderate-Cost plans, which is typical for many U.S. households.";
      else if (s <= all.liberal.monthly) msg = "Your spending sits between the Moderate-Cost and Liberal plans. Moving to Moderate would save about " + money(s - all.moderate.monthly) + " a month.";
      else msg = "You spend " + money(s - all.liberal.monthly) + " a month more than the USDA Liberal plan. Matching Moderate-Cost would save about " + money((s - all.moderate.monthly) * 12) + " a year.";
      cmp.textContent = msg;
    } else cmp.textContent = "";

    var q = state.people.map(function (p) { return p.sex + p.age; }).join(".");
    var url = location.pathname + "?h=" + q + "&p=" + state.plan + (homeEl.value !== "100" ? "&home=" + homeEl.value : "");
    try { history.replaceState(null, "", url); } catch (e) {}
  }

  function load() {
    var sp = new URLSearchParams(location.search), h = sp.get("h") || root.getAttribute("data-default");
    state.people = h.split(".").map(function (t) {
      var sex = t.charAt(0) === "m" ? "m" : "f", age = parseInt(t.slice(1), 10);
      return { sex: sex, age: isNaN(age) ? 35 : Math.max(1, Math.min(110, age)) };
    }).slice(0, 15);
    var p = sp.get("p");
    if (PLANS.indexOf(p) >= 0) state.plan = p;
    var home = parseInt(sp.get("home"), 10);
    if (!isNaN(home)) homeEl.value = Math.max(10, Math.min(100, home));
    root.querySelector('input[name=plan][value="' + state.plan + '"]').checked = true;
  }

  root.querySelector("#addAdult").addEventListener("click", function () {
    state.people.push({ age: 35, sex: state.people.length % 2 ? "f" : "m" }); update(true);
  });
  root.querySelector("#addChild").addEventListener("click", function () {
    state.people.push({ age: 8, sex: "f" }); update(true);
  });
  root.querySelectorAll("input[name=plan]").forEach(function (r) {
    r.addEventListener("change", function () { state.plan = r.value; update(false); });
  });
  homeEl.addEventListener("input", function () { update(false); });
  spendEl.addEventListener("input", function () { update(false); });
  root.querySelector("#share").addEventListener("click", function (e) {
    var b = e.target;
    var done = function () { b.textContent = "Link copied ✓"; setTimeout(function () { b.textContent = "Copy link to this budget"; }, 2000); };
    if (navigator.clipboard) navigator.clipboard.writeText(location.href).then(done, done); else done();
  });

  load();
  update(true);
})();
