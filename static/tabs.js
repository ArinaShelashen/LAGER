// tabs.js – the numbered step tabs at the top of the page.
// Each tab shows a short summary of its step (e.g. "89 of 90"), so nothing that is
// set in a hidden tab gets forgotten. Other scripts use:
//   LagerTabs.show("results")                     switch to a tab
//   LagerTabs.setSummary("rules", "89 of 90", "")  update a tab's summary
//       states: "" (normal), "ok", "warn", "busy"

(function () {
  "use strict";

  const tabs = [...document.querySelectorAll('.tabs [role="tab"]')];
  const names = tabs.map((t) => t.dataset.tab);

  function show(name, focus) {
    if (!names.includes(name)) name = "target";
    for (const tab of tabs) {
      const active = tab.dataset.tab === name;
      tab.setAttribute("aria-selected", active);
      tab.tabIndex = active ? 0 : -1;
      if (active && focus) tab.focus();
    }
    for (const panel of document.querySelectorAll("[data-panel]")) {
      panel.hidden = panel.dataset.panel !== name;
    }
    try { history.replaceState(null, "", `#${name}`); } catch { /* ignore */ }
    window.dispatchEvent(new CustomEvent("lager:tab", { detail: name }));
  }

  function setSummary(name, text, state) {
    const tab = tabs.find((t) => t.dataset.tab === name);
    if (!tab) return;
    const summary = tab.querySelector(".tab-summary");
    summary.textContent = text;
    summary.title = text;               // full text on hover (long SMILES are cut off)
    tab.dataset.state = state || "";
  }

  for (const tab of tabs) {
    tab.addEventListener("click", () => show(tab.dataset.tab));
    // Arrow keys move between tabs (the usual keyboard behaviour for tabs)
    tab.addEventListener("keydown", (e) => {
      const i = tabs.indexOf(tab);
      const next = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[e.key];
      if (next === undefined) return;
      e.preventDefault();
      show(names[(next + tabs.length) % tabs.length], true);
    });
  }

  // "Next: …" buttons at the bottom of the steps
  for (const button of document.querySelectorAll("[data-goto]")) {
    button.addEventListener("click", () => {
      show(button.dataset.goto);
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // Start at step 1 unless the address names a tab (e.g. #guide)
  show(names.includes(location.hash.slice(1)) ? location.hash.slice(1) : "target");
  window.LagerTabs = { show, setSummary };
})();
