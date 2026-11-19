// rules.js – reaction rule list (tick/untick, folders, view) and the "add your own rule" form.
// app.js asks LagerRules.disabledIds() when a search starts.
//
// The user's "rule setup" (which rules are ticked, which folder each rule is in) is kept
// in this browser and can be saved to / loaded from a JSON file:
//   {"format": "LAGER rule setup", "version": 1, "saved": "2026-11-19",
//    "rules": [{"id": "...", "name": "...", "folder": "Protection", "used": true}, ...]}
// folder "" = not in a folder. Rules without a folder chosen by the user (e.g. rules added
// later) go into the automatic folders (see autoFolders).

(function () {
  "use strict";

  const statusLine = document.getElementById("rules-status");
  const list = document.getElementById("rules-list");
  const filterInput = document.getElementById("rules-filter");
  const STORAGE_KEY = "lager.ruleSetup";
  const SETUP_FORMAT = "LAGER rule setup";
  const NEW_FOLDER = "\u0000new";      // value of the "New folder…" menu entry

  let rules = [];                      // [{id, name, source, author, description, created}]
  let disabled = new Set();            // rule ids the user switched off
  let folderOf = {};                   // rule id -> folder chosen by the user ("" = no folder)
  loadSetup();
  let deleteNeedsPassword = false;
  let selectedId = null;               // rule shown in the panel below the list
  const openGroups = new Set();        // folders the user opened
  const detail = document.getElementById("rule-detail");

  // Remember the setup in this browser (save it to a file to keep it for sure)
  function loadSetup() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
      if (saved) {
        disabled = new Set(saved.disabled || []);
        folderOf = saved.folders || {};
      } else {                         // earlier versions kept only the unticked rules
        disabled = new Set(JSON.parse(localStorage.getItem("lager.disabledRules") || "[]"));
      }
    } catch { /* start with the defaults */ }
  }
  function saveSetup() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify({ disabled: [...disabled], folders: folderOf })); }
    catch { /* ignore */ }
  }

  function el(tag, text, className) {
    const e = document.createElement(tag);
    if (text !== undefined) e.textContent = text;
    if (className) e.className = className;
    return e;
  }

  const ruleUrl = (id) => `/api/rules/${encodeURIComponent(id)}`;

  // -------------------------------------------------------------------------
  // Rule list
  // -------------------------------------------------------------------------
  async function loadRules(openId) {
    try {
      const response = await fetch("/api/rules");
      const data = await response.json();
      rules = data.rules;
      deleteNeedsPassword = data.delete_needs_password;
      const known = new Set(rules.map((r) => r.id));
      for (const id of [...disabled]) if (!known.has(id)) disabled.delete(id);
      for (const id of Object.keys(folderOf)) if (!known.has(id)) delete folderOf[id];
      renderList();
      if (openId) select(openId, true);
      else if (selectedId && !known.has(selectedId)) select(null);
    } catch (err) {
      statusLine.textContent = "The reaction rules could not be loaded.";
      statusLine.classList.add("error");
    }
  }

  function updateStatus() {
    const used = rules.length - disabled.size;
    statusLine.classList.toggle("error", used === 0);
    statusLine.textContent = used === 0
      ? "No reaction rules selected – please select at least one."
      : `Using ${used} of ${rules.length} reaction rules.`;
    if (window.LagerTabs) {
      LagerTabs.setSummary("rules", `${used} of ${rules.length}`, used === 0 ? "warn" : "");
    }
  }

  // Automatic folders by name: all protections, all deprotections, otherwise the first word
  function groupKey(rule) {
    const words = rule.name.toLowerCase().split(/\s+/);
    if (words.includes("deprotection")) return "deprotection";
    if (words.includes("protection")) return "protection";
    return words[0];
  }

  function groupLabel(key, members) {
    if (key === "protection") return "Protection";
    if (key === "deprotection") return "Deprotection";
    const firsts = members.map((r) => r.name.split(/\s+/)[0]);
    return firsts.find((w) => w !== w.toLowerCase()) || firsts[0];    // "Mitsunobu", not "mitsunobu"
  }

  // rule id -> automatic folder name ("" if the name is used by only one rule)
  function autoFolders() {
    const groups = new Map();
    for (const rule of rules) {
      const key = groupKey(rule);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(rule);
    }
    const result = {};
    for (const [key, members] of groups) {
      const label = members.length > 1 ? groupLabel(key, members) : "";
      for (const rule of members) result[rule.id] = label;
    }
    return result;
  }

  // rule id -> folder shown: the user's choice, otherwise the automatic folder
  function currentFolders() {
    const auto = autoFolders();
    const result = {};
    for (const rule of rules) result[rule.id] = Object.hasOwn(folderOf, rule.id) ? folderOf[rule.id] : auto[rule.id];
    return result;
  }

  function folderNames() {
    return [...new Set(Object.values(currentFolders()).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }));
  }

  function renderList() {
    const query = filterInput.value.trim().toLowerCase();
    const matches = (rule) => !query ||
      `${rule.name} ${rule.id} ${rule.author || ""} ${rule.description || ""}`.toLowerCase().includes(query);
    list.innerHTML = "";

    // Folders are made from all rules, so a folder keeps its rules while searching
    const folders = currentFolders();
    const groups = new Map();    // folder name -> rules
    const entries = [];          // [sort name, element]
    for (const rule of rules) {
      const folder = folders[rule.id];
      if (!folder) {
        if (matches(rule)) entries.push([rule.name, ruleRow(rule)]);
        continue;
      }
      if (!groups.has(folder)) groups.set(folder, []);
      groups.get(folder).push(rule);
    }
    for (const [label, members] of groups) {
      const shownMembers = members.filter(matches);
      if (shownMembers.length) entries.push([label, groupRow(label, members, shownMembers, Boolean(query))]);
    }
    entries.sort((a, b) => a[0].localeCompare(b[0], undefined, { sensitivity: "base" }));
    for (const [, element] of entries) list.appendChild(element);
    if (!entries.length) list.appendChild(el("li", "No rules match your search.", "rules-empty"));
    updateStatus();
  }

  // A folder: tick/untick all its rules, click the name to open it
  function groupRow(label, members, shownMembers, searching) {
    const key = label;
    const li = el("li", undefined, "rule-group");
    const head = el("div", undefined, "rule-head");
    const box = document.createElement("input");
    box.type = "checkbox";
    box.setAttribute("aria-label", `Use all ${label} rules`);
    const toggle = el("button", "", "rule-name group-toggle");
    const count = el("span", "", "rule-badge");
    const rename = el("button", "Rename", "link-button group-rename");
    rename.title = "Rename this folder";
    head.append(box, toggle, count, rename);
    const inner = el("ul", undefined, "rule-group-list");
    li.append(head, inner);

    const refresh = () => {
      const used = members.filter((r) => !disabled.has(r.id)).length;
      box.checked = used === members.length;
      box.indeterminate = used > 0 && used < members.length;
      count.textContent = `${used} of ${members.length} used`;
    };
    for (const rule of shownMembers) inner.appendChild(ruleRow(rule, refresh));
    refresh();

    const setOpen = (open) => {
      if (open) openGroups.add(key); else openGroups.delete(key);
      inner.hidden = !open;
      toggle.textContent = `${open ? "▾" : "▸"} ${label}`;
      toggle.setAttribute("aria-expanded", open);
    };
    li.openGroup = () => setOpen(true);
    setOpen(searching || openGroups.has(key) || members.some((r) => r.id === selectedId));
    toggle.addEventListener("click", () => setOpen(inner.hidden));
    rename.addEventListener("click", () => {
      const name = (window.prompt("New name of the folder (an existing name merges the folders):", label) || "").trim();
      if (!name || name === label) return;
      for (const r of members) folderOf[r.id] = name.slice(0, 80);
      if (openGroups.delete(label)) openGroups.add(name.slice(0, 80));
      saveSetup();
      renderList();
    });
    box.addEventListener("change", () => {
      for (const r of members) { if (box.checked) disabled.delete(r.id); else disabled.add(r.id); }
      for (const b of inner.querySelectorAll('input[type="checkbox"]')) b.checked = box.checked;
      saveSetup();
      refresh();
      updateStatus();
    });
    return li;
  }

  function ruleRow(rule, onToggle) {
    const li = el("li", undefined, "rule-row");
    const head = el("div", undefined, "rule-head");

    const box = document.createElement("input");
    box.type = "checkbox";
    box.checked = !disabled.has(rule.id);
    box.setAttribute("aria-label", `Use ${rule.name}`);
    box.addEventListener("change", () => {
      if (box.checked) disabled.delete(rule.id); else disabled.add(rule.id);
      saveSetup();
      updateStatus();
      if (onToggle) onToggle();
    });

    const name = el("button", rule.name, "rule-name");
    name.title = "Show the rule";
    name.setAttribute("aria-pressed", rule.id === selectedId);
    head.append(box, name);
    if (rule.id === selectedId) li.classList.add("selected");
    li.dataset.id = rule.id;

    if (rule.source === "user") {
      const meta = ["added", rule.author && `by ${rule.author}`, rule.created].filter(Boolean).join(" ");
      head.append(el("span", meta, "rule-badge"));
    }
    li.appendChild(head);
    name.addEventListener("click", () => select(rule.id === selectedId ? null : rule.id));
    return li;
  }

  // Show one rule in the panel below the list (click the name again to close it)
  function select(id, scrollIntoView) {
    selectedId = id;
    for (const row of list.querySelectorAll(".rule-row")) {
      const on = row.dataset.id === id;
      row.classList.toggle("selected", on);
      row.querySelector(".rule-name").setAttribute("aria-pressed", on);
      if (on && row.closest(".rule-group")) row.closest(".rule-group").openGroup();
      if (on && scrollIntoView) row.scrollIntoView({ block: "nearest" });
    }
    const rule = rules.find((r) => r.id === id);
    detail.hidden = !rule;
    if (rule) {
      showRule(rule, detail);
      if (scrollIntoView) detail.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } else {
      detail.innerHTML = "";
    }
  }

  let shownDirection = "retro";          // which direction the rule panel shows

  async function showRule(rule, viewer) {
    viewer.innerHTML = "";
    viewer.appendChild(el("p", "Loading…", "hint"));
    const forward = shownDirection === "forward";
    const query = forward ? "?direction=forward" : "";
    try {
      const response = await fetch(`${ruleUrl(rule.id)}/gml${query}`);
      if (selectedId !== rule.id) return;           // another rule was clicked meanwhile
      const gml = response.ok ? await response.text() : null;
      if (!response.ok && !forward) throw new Error("The rule file could not be loaded.");
      viewer.innerHTML = "";

      const header = el("div", undefined, "rule-detail-head");
      header.appendChild(el("h3", rule.name));
      const close = el("button", "Close", "link-button");
      close.addEventListener("click", () => select(null));
      header.appendChild(close);
      viewer.appendChild(header);
      if (rule.description) viewer.appendChild(el("p", rule.description, "rule-description"));
      viewer.appendChild(folderPicker(rule));

      // Switch: retrosynthetic rule (used by the search) / forward reaction
      const toggle = el("div", undefined, "direction-toggle");
      for (const [value, label] of [["retro", "Retrosynthetic rule (used by the search)"],
                                    ["forward", "Forward reaction (side-reaction check)"]]) {
        const b = el("button", label, value === shownDirection ? "active" : "");
        b.addEventListener("click", () => { shownDirection = value; showRule(rule, viewer); });
        toggle.appendChild(b);
      }
      viewer.appendChild(toggle);

      const picture = el("div");
      viewer.appendChild(picture);
      if (gml === null) {
        picture.appendChild(el("p", "There is no forward version of this rule.", "hint"));
        return;
      }
      try {
        RuleView.render(picture, RuleView.parse(gml));
      } catch (err) {
        picture.appendChild(el("p", `This rule cannot be drawn: ${err.message}`, "message error"));
      }

      const links = el("p", undefined, "rule-links");
      const download = el("a", "Download .gml");
      download.href = `${ruleUrl(rule.id)}/gml${query || "?"}${query ? "&" : ""}download=1`;
      const showText = el("button", "Show GML text", "link-button");
      const text = el("pre", gml, "rule-gml-text");
      text.hidden = true;
      showText.addEventListener("click", () => {
        text.hidden = !text.hidden;
        showText.textContent = text.hidden ? "Show GML text" : "Hide GML text";
      });
      links.append(download, showText);
      if (rule.source === "user") {
        const del = el("button", "Delete this rule", "link-button danger");
        del.addEventListener("click", () => deleteRule(rule));
        links.append(del);
      }
      viewer.append(links, text);
    } catch (err) {
      viewer.innerHTML = "";
      viewer.appendChild(el("p", err.message, "message error"));
    }
  }

  // "Folder: [menu]" in the rule panel: move the rule to another folder
  function folderPicker(rule) {
    const label = el("label", "Folder ", "folder-picker");
    const menu = document.createElement("select");
    const add = (value, text) => { const o = el("option", text); o.value = value; menu.appendChild(o); };
    add("", "(no folder)");
    for (const name of folderNames()) add(name, name);
    add(NEW_FOLDER, "New folder…");
    const current = currentFolders()[rule.id] || "";
    menu.value = current;
    menu.addEventListener("change", () => {
      let name = menu.value;
      if (name === NEW_FOLDER) {
        name = (window.prompt("Name of the new folder:") || "").trim().slice(0, 80);
        if (!name) { menu.value = current; return; }
      }
      folderOf[rule.id] = name;
      saveSetup();
      renderList();
      label.replaceWith(folderPicker(rule));
    });
    label.appendChild(menu);
    return label;
  }

  // -------------------------------------------------------------------------
  // Save the setup to a file / load it from a file / back to the automatic folders
  // -------------------------------------------------------------------------
  const setupMessage = document.getElementById("setup-message");

  document.getElementById("setup-save").addEventListener("click", () => {
    const folders = currentFolders();
    const data = {
      format: SETUP_FORMAT, version: 1, saved: new Date().toISOString().slice(0, 10),
      rules: rules.map((r) => ({ id: r.id, name: r.name, folder: folders[r.id] || "", used: !disabled.has(r.id) })),
    };
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 1)], { type: "application/json" }));
    link.download = "lager_rule_setup.json";
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    setupMessage.textContent = "";
  });

  const setupFile = document.getElementById("setup-file");
  setupFile.addEventListener("change", async () => {
    const file = setupFile.files[0];
    setupFile.value = "";                       // the same file can be loaded again
    if (!file) return;
    try {
      let data;
      try { data = JSON.parse(await file.text()); }
      catch { throw new Error("The file could not be read (it is not a JSON file)."); }
      if (!data || data.format !== SETUP_FORMAT || !Array.isArray(data.rules)) {
        throw new Error("This is not a LAGER rule setup file.");
      }
      const known = new Set(rules.map((r) => r.id));
      const applied = new Set();
      let unknown = 0;
      for (const entry of data.rules) {
        if (!entry || typeof entry.id !== "string" || !known.has(entry.id)) { unknown += 1; continue; }
        folderOf[entry.id] = typeof entry.folder === "string" ? entry.folder.trim().slice(0, 80) : "";
        if (entry.used === false) disabled.add(entry.id); else disabled.delete(entry.id);
        applied.add(entry.id);
      }
      saveSetup();
      renderList();
      const notInFile = rules.length - applied.size;
      setupMessage.className = "message success";
      setupMessage.textContent = `Loaded the setup of ${applied.size} rules from ${file.name}.`
        + (unknown ? ` ${unknown} rules in the file do not exist in this LAGER and were skipped.` : "")
        + (notInFile ? ` ${notInFile} rules are not in the file (e.g. added later); they are unchanged.` : "");
    } catch (err) {
      setupMessage.className = "message error";
      setupMessage.textContent = err.message;
    }
  });

  document.getElementById("setup-reset").addEventListener("click", () => {
    if (!window.confirm("Put all rules back into the automatic folders? Ticks are not changed.")) return;
    folderOf = {};
    saveSetup();
    renderList();
    if (selectedId) select(selectedId);
    setupMessage.className = "message";
    setupMessage.textContent = "All rules are back in the automatic folders.";
  });

  async function deleteRule(rule) {
    const headers = {};
    if (deleteNeedsPassword) {
      const password = window.prompt(`Password to delete "${rule.name}":`);
      if (password === null) return;
      headers["X-Admin-Password"] = password;
    } else if (!window.confirm(`Delete the rule "${rule.name}" for everyone?`)) {
      return;
    }
    const response = await fetch(ruleUrl(rule.id), { method: "DELETE", headers });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) { window.alert(data.error || "The rule could not be deleted."); return; }
    select(null);
    disabled.delete(rule.id);
    delete folderOf[rule.id];
    saveSetup();
    loadRules();
  }

  filterInput.addEventListener("input", renderList);
  document.getElementById("rules-all").addEventListener("click", () => {
    for (const r of visibleRules()) disabled.delete(r.id);
    saveSetup(); renderList();
  });
  document.getElementById("rules-none").addEventListener("click", () => {
    for (const r of visibleRules()) disabled.add(r.id);
    saveSetup(); renderList();
  });
  // "Select all/none" act on the rules currently shown (respects the search)
  function visibleRules() {
    const query = filterInput.value.trim().toLowerCase();
    return rules.filter((r) => !query ||
      `${r.name} ${r.id} ${r.author || ""} ${r.description || ""}`.toLowerCase().includes(query));
  }

  // -------------------------------------------------------------------------
  // Add your own rule: 1. forward reaction  ->  2. retrosynthetic rule (checked)
  // -------------------------------------------------------------------------
  const nameInput = document.getElementById("rule-name");
  const authorInput = document.getElementById("rule-author");
  const descriptionInput = document.getElementById("rule-description");
  const forwardInput = document.getElementById("rule-forward");
  const forwardMessage = document.getElementById("forward-message");
  const forwardPreview = document.getElementById("forward-preview");
  const fileInput = document.getElementById("rule-file");
  const turnButton = document.getElementById("rule-turn");
  const inverseStep = document.getElementById("inverse-step");
  const inverseReport = document.getElementById("inverse-report");
  const inverseInput = document.getElementById("rule-inverse");
  const inversePreview = document.getElementById("inverse-preview");
  const approved = document.getElementById("rule-approved");
  const checkButton = document.getElementById("rule-check");
  const saveButton = document.getElementById("rule-save");
  const message = document.getElementById("rule-message");

  try { authorInput.value = localStorage.getItem("lager.author") || ""; } catch { /* ignore */ }

  function setMessage(target, text, kind) {
    target.textContent = text;
    target.className = "message" + (kind ? ` ${kind}` : "");
    target.hidden = !text;
  }

  // Live preview while typing (drawn in the browser; MØD checks on "Check"/"Save")
  function livePreview(input, preview, messageBox, onChange) {
    let timer = null;
    const update = () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        preview.innerHTML = "";
        if (!input.value.trim()) { setMessage(messageBox, ""); return; }
        try {
          RuleView.render(preview, RuleView.parse(input.value));
          setMessage(messageBox, "");
        } catch (err) {
          setMessage(messageBox, `The rule cannot be read yet: ${err.message}`, "error");
        }
      }, 300);
    };
    input.addEventListener("input", () => { update(); if (onChange) onChange(); });
    return update;
  }
  const updateForwardPreview = livePreview(forwardInput, forwardPreview, forwardMessage, () => {
    if (!inverseStep.hidden) {
      setMessage(message, "You changed the forward reaction. Click “Create retrosynthetic rule” " +
                          "again to update the retrosynthetic rule.", "warning-text");
    }
  });
  const updateInversePreview = livePreview(inverseInput, inversePreview, message, () => {
    approved.checked = false;            // edited → needs to be checked again
    saveButton.disabled = true;
  });

  fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];
    fileInput.value = "";
    if (!file) return;
    forwardInput.value = await file.text();
    if (!nameInput.value.trim()) nameInput.value = file.name.replace(/\.gml$/i, "");
    updateForwardPreview();
  });

  async function post(url, body) {
    const response = await fetch(url, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "Something went wrong.");
    return data;
  }

  // A condition as a sentence, from its GML snippet
  function conditionText(snippet) {
    try {
      const rule = RuleView.parse(`rule [ context [ node [ id 0 label "C" ] ] ${snippet} ]`);
      return RuleView.describeConstraint(rule.constraints[0]).text;
    } catch {
      return snippet;
    }
  }

  // Add a condition to the end of a rule (before its last "]"), by default the retrosynthetic one
  function insertCondition(snippet, input = inverseInput) {
    const text = input.value;
    const end = text.lastIndexOf("]");
    const indented = snippet.split("\n").map((line) => "\t" + line).join("\n");
    input.value = end < 0 ? text + "\n" + indented
                          : text.slice(0, end).replace(/\s*$/, "\n") + indented + "\n" + text.slice(end);
    input.dispatchEvent(new Event("input"));
  }

  // "Add condition": a condition typed as GML text, e.g. constrainAdj [ … ]
  function conditionField(prefix, ruleInput, messageBox) {
    const field = document.getElementById(`${prefix}-condition`);
    const add = () => {
      const snippet = field.value.trim();
      if (!snippet) return;
      try {
        const parsed = RuleView.parse(`rule [ context [ node [ id 0 label "C" ] ] ${snippet} ]`);
        if (!snippet.startsWith("constrain") || parsed.constraints.length !== 1) throw new Error();
      } catch {
        setMessage(messageBox, "This is not one condition in GML, e.g. " +
                               'constrainAdj [ id 2 op "=" count 1 nodeLabels [ label "O" ] ]', "error");
        return;
      }
      if (!ruleInput.value.trim()) {
        setMessage(messageBox, "Write or create the rule first, then add conditions to it.", "error");
        return;
      }
      insertCondition(snippet, ruleInput);
      field.value = "";
    };
    document.getElementById(`${prefix}-condition-add`).addEventListener("click", add);
    field.addEventListener("keydown", (e) => { if (e.key === "Enter") add(); });
  }
  conditionField("forward", forwardInput, forwardMessage);
  conditionField("inverse", inverseInput, message);

  function showInverseReport(result) {
    inverseReport.innerHTML = "";
    const box = el("div", undefined, "inverse-report");
    const n = result.copied.length + result.adjusted.length;
    box.appendChild(el("p", n || result.review.length
      ? "The left and right sides were swapped. Conditions are checked on the left side, " +
        "so they were translated to the other molecule:"
      : "The left and right sides were swapped. The rule has no conditions.", "note"));

    const list = el("ul");
    for (const s of result.copied) {
      list.appendChild(el("li", `Copied unchanged: ${conditionText(s)}`));
    }
    for (const a of result.adjusted) {
      list.appendChild(el("li", `Translated: ${conditionText(a.from)}  →  ${conditionText(a.to)}`));
    }
    if (list.children.length) box.appendChild(list);

    if (result.review.length) {
      box.appendChild(el("p", "These conditions could not be translated automatically and were " +
                              "NOT added. Add them if they apply to the retrosynthetic direction " +
                              "(you can edit the text afterwards):", "warning-text"));
      const reviewList = el("ul");
      for (const s of result.review) {
        const li = el("li", conditionText(s) + " ");
        const add = el("button", "Add to rule", "link-button");
        add.addEventListener("click", () => { insertCondition(s); add.disabled = true; add.textContent = "added"; });
        li.appendChild(add);
        reviewList.appendChild(li);
      }
      box.appendChild(reviewList);
    }
    box.appendChild(el("p", "Chemistry can need different conditions in the two directions – " +
                            "edit the rule below if necessary.", "note"));
    inverseReport.appendChild(box);
  }

  turnButton.addEventListener("click", async () => {
    turnButton.disabled = true;
    setMessage(message, "");
    try {
      const result = await post("/api/rules/turn-around", { gml: forwardInput.value });
      inverseInput.value = result.gml;
      showInverseReport(result);
      inverseStep.hidden = false;
      approved.checked = false;
      saveButton.disabled = true;
      updateInversePreview();
      inverseStep.scrollIntoView({ behavior: "smooth", block: "start" });
    } catch (err) {
      setMessage(forwardMessage, err.message, "error");
    } finally {
      turnButton.disabled = false;
    }
  });

  approved.addEventListener("change", () => { saveButton.disabled = !approved.checked; });

  checkButton.addEventListener("click", async () => {
    checkButton.disabled = true;
    setMessage(message, "Checking both rules with MØD…");
    try {
      await post("/api/rules/check", { forward_gml: forwardInput.value, inverse_gml: inverseInput.value });
      setMessage(message, "MØD can read both rules. ✓", "success");
    } catch (err) {
      setMessage(message, err.message, "error");
    } finally {
      checkButton.disabled = false;
    }
  });

  saveButton.addEventListener("click", async () => {
    if (!nameInput.value.trim()) { setMessage(message, "Please give the rule a name.", "error"); return; }
    saveButton.disabled = true;
    setMessage(message, "Checking and saving the rule…");
    try {
      const data = await post("/api/rules", {
        name: nameInput.value, author: authorInput.value, description: descriptionInput.value,
        forward_gml: forwardInput.value, inverse_gml: inverseInput.value,
      });
      try { localStorage.setItem("lager.author", authorInput.value); } catch { /* ignore */ }
      setMessage(message, `Saved as "${data.rule.name}". It is now in the list above and used in searches.`,
                 "success");
      for (const input of [nameInput, descriptionInput, forwardInput, inverseInput]) input.value = "";
      forwardPreview.innerHTML = ""; inversePreview.innerHTML = ""; inverseReport.innerHTML = "";
      inverseStep.hidden = true;
      approved.checked = false;
      filterInput.value = "";
      await loadRules(data.rule.id);
    } catch (err) {
      setMessage(message, err.message, "error");
      saveButton.disabled = !approved.checked;
    }
  });

  loadRules();

  window.LagerRules = {
    disabledIds: () => [...disabled],
    selectedCount: () => rules.length - disabled.size,
  };
})();
