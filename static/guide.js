// guide.js – tab 0: draws each example rule with the rule viewer when it is opened.
(function () {
  "use strict";
  for (const block of document.querySelectorAll(".guide-rule")) {
    let drawn = false;
    block.addEventListener("toggle", async () => {
      if (!block.open || drawn) return;
      drawn = true;
      const view = block.querySelector(".guide-rule-view");
      view.textContent = "Loading…";
      try {
        const response = await fetch(`/api/rules/${encodeURIComponent(block.dataset.ruleId)}/gml`);
        if (!response.ok) throw new Error("The rule file could not be loaded.");
        RuleView.render(view, RuleView.parse(await response.text()));
      } catch (err) {
        view.textContent = err.message;
        drawn = false;
      }
    });
  }
})();
