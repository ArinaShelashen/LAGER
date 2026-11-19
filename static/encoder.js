// encoder.js – "Start from example reactions": example reactions -> draft forward rule.
//   a. Check reactions: canonical SMILES, balance (SynRBL proposes missing molecules)
//   b. Map atoms: SynKit's possible atom mappings; the user picks one per reaction
//   c. Build rule: reaction centre (+ context) as GML, suggested conditions, MØD test
//   d. "Use this rule": the GML goes into step 1 (rule-forward), where the existing
//      form continues (edit, create retrosynthetic rule, check, save).

(function () {
  "use strict";

  const MAX_EXAMPLES = 4;
  const details = document.getElementById("rule-add");
  const unavailable = document.getElementById("encode-unavailable");
  const body = document.getElementById("encode-body");
  const inputs = document.getElementById("encode-inputs");
  const addButton = document.getElementById("encode-add");
  const prepareButton = document.getElementById("encode-prepare");
  const message = document.getElementById("encode-message");
  const balanceBox = document.getElementById("encode-balance");
  const mappingBox = document.getElementById("encode-mapping");
  const resultBox = document.getElementById("encode-result");
  const forwardInput = document.getElementById("rule-forward");
  const descriptionInput = document.getElementById("rule-description");

  let prepared = [];        // answer of /prepare, one entry per reaction
  let mapped = [];          // answer of /map
  let built = null;         // answer of /build
  let usedReactions = [];   // the balanced reactions that were mapped

  function el(tag, text, className) {
    const e = document.createElement(tag);
    if (text !== undefined) e.textContent = text;
    if (className) e.className = className;
    return e;
  }

  function setMessage(text, kind) {
    message.textContent = text;
    message.className = "message" + (kind ? ` ${kind}` : "");
    message.hidden = !text;
  }

  async function post(action, payload) {
    const response = await fetch(`/api/encode/${action}`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "Something went wrong.");
    return data;
  }

  // Run a step with the button disabled and a progress message
  async function busy(button, text, work) {
    button.disabled = true;
    setMessage(text);
    try { await work(); setMessage(""); }
    catch (err) { setMessage(err.message, "error"); }
    finally { button.disabled = false; }
  }

  function drawRule(container, gml) {
    container.innerHTML = "";
    try { RuleView.render(container, RuleView.parse(gml)); }
    catch (err) { container.appendChild(el("p", `This rule cannot be drawn: ${err.message}`, "message error")); }
  }

  // Later steps depend on earlier ones: clear them when something earlier changes
  function resetFrom(step) {
    if (step <= 1) { balanceBox.innerHTML = ""; prepared = []; }
    if (step <= 2) { mappingBox.innerHTML = ""; mapped = []; }
    if (step <= 3) { resultBox.innerHTML = ""; built = null; }
  }

  // -------------------------------------------------------------------------
  // Is the encoder environment there? (asked once, when the form is opened)
  // -------------------------------------------------------------------------
  let statusChecked = false;
  details.addEventListener("toggle", async () => {
    if (!details.open || statusChecked) return;
    statusChecked = true;
    try {
      const data = await (await fetch("/api/encode/status")).json();
      if (!data.available) {
        unavailable.textContent = "Creating rules from example reactions is not available on this " +
                                  `installation: ${data.message}`;
        unavailable.hidden = false;
        body.hidden = true;
      }
    } catch { /* the buttons will show the error */ }
  });

  // -------------------------------------------------------------------------
  // a. Example reactions
  // -------------------------------------------------------------------------
  function addRow(value) {
    const row = el("div", undefined, "encode-row");
    const input = el("input");
    input.type = "text";
    input.spellcheck = false;
    input.value = value || "";
    input.placeholder = inputs.children.length ? "another example of the same reaction"
                                               : "e.g. CC(=O)O.CO>>CC(=O)OC.O";
    input.setAttribute("aria-label", `Example reaction ${inputs.children.length + 1}`);
    input.addEventListener("input", () => resetFrom(1));
    const draw = el("button", "Draw", "link-button");
    draw.addEventListener("click", () => openEditor(input));
    const remove = el("button", "Remove", "link-button");
    remove.addEventListener("click", () => {
      if (input === drawingInto) closeEditor();
      if (inputs.children.length > 1) row.remove(); else input.value = "";
      resetFrom(1);
      updateAddButton();
    });
    row.append(input, draw, remove);
    inputs.appendChild(row);
    updateAddButton();
    return input;
  }
  function updateAddButton() { addButton.hidden = inputs.children.length >= MAX_EXAMPLES; }

  // One JSME editor in reaction mode, shared by all rows: drawing writes the
  // reaction SMILES into the row whose "Draw" button was clicked
  const drawPanel = document.getElementById("encode-draw");
  const drawTitle = document.getElementById("encode-draw-title");
  let reactionEditor = null;
  let drawingInto = null;          // the input that receives the drawing

  function openEditor(input) {
    if (!(window.JSApplet && window.JSApplet.JSME)) {
      setMessage("The drawing editor has not loaded (it needs an internet connection). " +
                 "Please paste the reaction SMILES instead.", "error");
      return;
    }
    drawingInto = input;
    const number = reactionInputs().indexOf(input) + 1;
    drawTitle.textContent = `Drawing example ${number}: draw the reactants, then the reaction arrow ` +
                            "(arrow button in the toolbar), then the products. The SMILES is filled in automatically.";
    drawPanel.hidden = false;
    if (!reactionEditor) {
      const width = Math.min(640, drawPanel.clientWidth || 640);
      reactionEditor = new JSApplet.JSME("encode-editor", width + "px", "360px",
                                         { options: "reaction,multipart" });
      reactionEditor.setAfterStructureModifiedCallback(() => {
        if (!drawingInto) return;
        drawingInto.value = reactionEditor.smiles();
        resetFrom(1);
      });
    }
    // Show what is already in the row (if JSME can read it), otherwise start empty
    const current = drawingInto.value.trim();
    reactionEditor.reset();
    if (current) {
      try { reactionEditor.readGenericMolecularInput(current); } catch { /* start empty */ }
    }
    drawPanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function closeEditor() {
    drawingInto = null;
    drawPanel.hidden = true;
  }
  document.getElementById("encode-draw-close").addEventListener("click", closeEditor);
  addButton.addEventListener("click", () => addRow().focus());
  addRow();

  const reactionInputs = () => [...inputs.querySelectorAll("input")];

  prepareButton.addEventListener("click", () => {
    const reactions = reactionInputs().map((i) => i.value.trim()).filter(Boolean);
    if (!reactions.length) { setMessage("Please paste at least one reaction SMILES.", "error"); return; }
    resetFrom(1);
    busy(prepareButton, "Checking the reactions…", async () => {
      prepared = (await post("prepare", { reactions })).reactions;
      showBalance();
    });
  });

  function showBalance() {
    balanceBox.innerHTML = "";
    const box = el("div", undefined, "encode-box");
    box.appendChild(el("h4", "Reactions"));
    let anyError = false, anyAdded = false;

    prepared.forEach((r, i) => {
      const item = el("div", undefined, "encode-item");
      item.appendChild(el("p", `Reaction ${i + 1}`, "encode-item-title"));
      if (r.error) {
        anyError = true;
        item.appendChild(el("p", r.error, "message error"));
      } else if (r.balanced) {
        item.appendChild(el("p", `✓ Balanced: ${r.rsmi}`, "encode-ok"));
      } else {
        anyAdded = true;
        // difference = products − reactants: positive = missing in the reactants
        const atoms = (sign) => Object.entries(r.difference).filter(([, n]) => n * sign > 0)
          .map(([e, n]) => `${Math.abs(n)} ${e}`).join(", ");
        const lines = ["Not balanced."];
        if (atoms(1)) lines.push(`Missing in the reactants (or too many in the products): ${atoms(1)}.`);
        if (atoms(-1)) lines.push(`Missing in the products (or too many in the reactants): ${atoms(-1)}.`);
        const dq = r.charge_difference;
        if (dq) lines.push(`The total charge of the products is ${Math.abs(dq)} ${dq > 0 ? "higher" : "lower"} ` +
                           "than that of the reactants.");
        for (const line of lines) item.appendChild(el("p", line, "warning-text"));
        item.appendChild(el("p", r.proposal
          ? `SynRBL suggests adding: ${r.added.join(" , ")}. Please check that this is chemically correct ` +
            "and edit the reaction if needed (e.g. HCl instead of [H+].[Cl-])."
          : "SynRBL could not balance it. Please add the missing molecules yourself.", "hint small"));
        const input = el("input");
        input.type = "text";
        input.spellcheck = false;
        input.value = r.proposal || r.rsmi;
        input.dataset.index = i;
        input.className = "encode-balanced";
        input.setAttribute("aria-label", `Balanced reaction ${i + 1}`);
        input.addEventListener("input", () => resetFrom(2));
        item.appendChild(input);
      }
      box.appendChild(item);
    });

    const actions = el("div", undefined, "actions");
    const approve = el("label", undefined, "check-line");
    const approveBox = el("input");
    approveBox.type = "checkbox";
    approve.append(approveBox, document.createTextNode(" I checked the added molecules."));
    const mapButton = el("button", "Map atoms");
    mapButton.disabled = anyError || anyAdded;
    approveBox.addEventListener("change", () => { mapButton.disabled = anyError || !approveBox.checked; });
    if (anyAdded) box.appendChild(approve);
    if (anyError) box.appendChild(el("p", "Correct the reactions above and click “Check reactions” again.", "hint small"));
    actions.appendChild(mapButton);
    box.appendChild(actions);
    balanceBox.appendChild(box);

    mapButton.addEventListener("click", () => {
      usedReactions = prepared.map((r, i) => {
        const edited = balanceBox.querySelector(`.encode-balanced[data-index="${i}"]`);
        return edited ? edited.value.trim() : r.rsmi;
      });
      resetFrom(2);
      busy(mapButton, "Mapping the atoms (up to 10 seconds per reaction)…", async () => {
        mapped = (await post("map", { reactions: usedReactions })).reactions;
        showMapping();
      });
    });
  }

  // -------------------------------------------------------------------------
  // b. Atom mappings: one choice per reaction
  // -------------------------------------------------------------------------
  function showMapping() {
    mappingBox.innerHTML = "";
    const box = el("div", undefined, "encode-box");
    box.appendChild(el("h4", "Atom mapping and reaction centre"));
    box.appendChild(el("p", "Each picture shows the reaction centre (bonds broken in red, formed in green) " +
                            "with its neighbouring atoms. Numbers are atom numbers. If several mappings are " +
                            "possible, choose the one that matches the chemistry.", "hint small"));
    let anyError = false;

    mapped.forEach((r, i) => {
      const item = el("div", undefined, "encode-item");
      item.appendChild(el("p", `Reaction ${i + 1}: ${r.rsmi}`, "encode-item-title"));
      if (r.error) {
        anyError = true;
        item.appendChild(el("p", r.error, "message error"));
        box.appendChild(item);
        return;
      }
      if (r.warning) item.appendChild(el("p", r.warning, "warning-text"));
      const n = r.candidates.length;
      if (n > 1) item.appendChild(el("p", `${n} atom mappings are possible – please choose one.`, "warning-text"));

      // Preselect when there is no real choice: one mapping, or only one fits the other examples
      const consistent = r.candidates.filter((c) => c.consistent);
      const preselect = n === 1 ? 0 : consistent.length === 1 ? r.candidates.indexOf(consistent[0]) : -1;

      r.candidates.forEach((c, k) => {
        const card = el("label", undefined, "candidate");
        const radio = el("input");
        radio.type = "radio";
        radio.name = `mapping-${i}`;
        radio.value = k;
        radio.checked = k === preselect;
        radio.addEventListener("change", () => resetFrom(3));
        const head = el("div", undefined, "candidate-head");
        head.append(radio, el("strong", n > 1 ? `Mapping ${String.fromCharCode(65 + k)}` : "Mapping"));
        if (c.consistent === true) head.appendChild(el("span", "same centre in all examples", "rule-badge ok"));
        if (c.consistent === false) head.appendChild(el("span", "not found in the other examples", "rule-badge warn"));
        card.appendChild(head);
        const changes = el("ul", undefined, "candidate-changes");
        for (const ch of c.changes) changes.appendChild(el("li", ch));
        card.appendChild(changes);
        const picture = el("div");
        card.appendChild(picture);
        item.appendChild(card);
        drawRule(picture, c.gml);
      });
      box.appendChild(item);
    });

    if (!anyError) {
      const options = el("div", undefined, "encode-options");
      const radiusLabel = el("label", "Context around the reaction centre ");
      const radius = el("select");
      for (const [v, t] of [["0", "none – reaction centre only"], ["1", "neighbouring atoms (1 bond)"],
                            ["2", "2 bonds"]]) {
        const o = el("option", t); o.value = v; radius.appendChild(o);
      }
      radius.value = "1";
      radiusLabel.appendChild(radius);
      const hLabel = el("label", undefined, "check-line");
      const hBox = el("input"); hBox.type = "checkbox";
      hLabel.append(hBox, document.createTextNode(" Include hydrogens in the context " +
        "(stricter: e.g. only primary amines). Without it, use the H-count conditions below."));
      box.append(options);
      options.append(radiusLabel, hLabel);

      const buildButton = el("button", "Build rule");
      const actions = el("div", undefined, "actions");
      actions.appendChild(buildButton);
      box.appendChild(actions);
      radius.addEventListener("change", () => resetFrom(3));
      hBox.addEventListener("change", () => resetFrom(3));

      buildButton.addEventListener("click", () => {
        const chosen = mapped.map((r, i) => {
          const radio = box.querySelector(`input[name="mapping-${i}"]:checked`);
          return radio ? r.candidates[Number(radio.value)].mapped : null;
        });
        if (chosen.includes(null)) { setMessage("Please choose an atom mapping for every reaction.", "error"); return; }
        resetFrom(3);
        busy(buildButton, "Building the rule and testing it with MØD…", async () => {
          built = await post("build", { mapped: chosen, radius: Number(radius.value), context_h: hBox.checked });
          showResult();
        });
      });
    }
    mappingBox.appendChild(box);
  }

  // -------------------------------------------------------------------------
  // c. The draft rule, suggested conditions, test
  // -------------------------------------------------------------------------
  // Add conditions before the last "]" of a rule
  function withConditions(gml, snippets) {
    if (!snippets.length) return gml;
    const end = gml.lastIndexOf("]");
    const indented = snippets.map((s) => s.split("\n").map((line) => "\t" + line).join("\n")).join("\n");
    return gml.slice(0, end).replace(/\s*$/, "\n") + indented + "\n" + gml.slice(end);
  }

  function showTests(container, tests) {
    container.innerHTML = "";
    const list = el("ul", undefined, "encode-tests");
    for (const t of tests) {
      list.appendChild(el("li", t.ok
        ? `✓ ${t.reaction}`
        : `✗ ${t.reaction} – not produced: ${t.missing.join(", ")}`, t.ok ? "encode-ok" : "message error"));
    }
    container.appendChild(list);
  }

  function showResult() {
    resultBox.innerHTML = "";
    const box = el("div", undefined, "encode-box");
    box.appendChild(el("h4", "Draft rule (forward reaction)"));
    for (const note of built.notes) box.appendChild(el("p", note, "warning-text"));
    const picture = el("div");
    box.appendChild(picture);
    drawRule(picture, built.gml);

    box.appendChild(el("p", "MØD test – the rule turns the reactants of each example into its products:", "hint small"));
    const tests = el("div");
    box.appendChild(tests);
    showTests(tests, built.tests);

    const checked = [];
    if (built.suggestions.length) {
      box.appendChild(el("p", "Conditions that are true for every example. Tick the ones that are needed " +
                              "for the reaction to work (e.g. “O has exactly 1 H neighbour” = alcohol or " +
                              "acid, not ether or ester). Leave the others unticked – you can still " +
                              "edit the rule in step 1.", "hint small"));
      const list = el("ul", undefined, "encode-suggestions");
      for (const s of built.suggestions) {
        const li = el("li");
        const label = el("label", undefined, "check-line");
        const cb = el("input"); cb.type = "checkbox";
        cb.addEventListener("change", () => {
          if (cb.checked) checked.push(s.gml); else checked.splice(checked.indexOf(s.gml), 1);
        });
        label.append(cb, document.createTextNode(" " + s.text));
        li.appendChild(label);
        list.appendChild(li);
      }
      box.appendChild(list);
    }

    const actions = el("div", undefined, "actions");
    const testButton = el("button", "Test again with the ticked conditions", "button secondary");
    const useButton = el("button", "Use this rule in step 1");
    if (built.suggestions.length) actions.appendChild(testButton);
    actions.appendChild(useButton);
    box.appendChild(actions);
    resultBox.appendChild(box);

    testButton.addEventListener("click", () => busy(testButton, "Testing with MØD…", async () => {
      const data = await post("test", { gml: withConditions(built.gml, checked), reactions: usedReactions });
      showTests(tests, data.tests);
    }));

    useButton.addEventListener("click", () => {
      forwardInput.value = withConditions(built.gml, checked);
      forwardInput.dispatchEvent(new Event("input"));          // rules.js redraws the preview
      if (!descriptionInput.value.trim()) {
        descriptionInput.value = `Created from: ${usedReactions.join(" ; ")}`.slice(0, 1000);
      }
      setMessage("The rule is in step 1. Review it, add or edit conditions if needed, then click " +
                 "“Create retrosynthetic rule”.", "success");
      forwardInput.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  }
})();
