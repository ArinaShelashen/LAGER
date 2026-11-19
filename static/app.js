// Front end: draw or paste a molecule, optionally upload reagents, start a search, show results.

const smilesInput = document.getElementById("smiles");
const runButton = document.getElementById("run");
const message = document.getElementById("message");
const progress = document.getElementById("progress");
const statusTitle = document.getElementById("status");
const logBox = document.getElementById("log");
const results = document.getElementById("results");
const pathwaysBox = document.getElementById("pathways");
const zipLink = document.getElementById("zip");
const reactantsStatus = document.getElementById("reactants-status");
const reactantsReport = document.getElementById("reactants-report");
const reactantsFile = document.getElementById("reactants-file");
const reactantsReset = document.getElementById("reactants-reset");
const reactantsError = document.getElementById("reactants-error");
const runSummary = document.getElementById("run-summary");
const resultsEmpty = document.getElementById("results-empty");
const resultsEmptyText = document.getElementById("results-empty-text");
const tabs = window.LagerTabs || { show() {}, setSummary() {} };

let editor = null;
let reactantsId = null;          // null = default list
let lastUpload = null;           // report of the list in use, to restore after a failed upload
let uploading = false;
let searching = false;

function updateRunButton() {
  runButton.disabled = uploading || searching;
}

// Small helper: create an element with text (safe for file and molecule names)
function el(tag, text, className) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (className) e.className = className;
  return e;
}

// JSME calls this function automatically once it has loaded
function jsmeOnLoad() {
  const width = Math.min(560, document.getElementById("editor").clientWidth || 560);
  editor = new JSApplet.JSME("editor", width + "px", "340px");
  // Drawing a molecule writes its SMILES into the text field
  editor.setAfterStructureModifiedCallback(() => {
    smilesInput.value = editor.smiles();
    updateTargetSummary();
  });
}

// ---------------------------------------------------------------------------
// Summaries in the tabs and in the bar at the bottom
// ---------------------------------------------------------------------------
function shorten(text, max) {
  return text.length > max ? text.slice(0, max - 1) + "…" : text;
}

function updateTargetSummary() {
  const smiles = smilesInput.value.trim();
  tabs.setSummary("target", smiles || "not set", smiles ? "ok" : "warn");
  runSummary.innerHTML = "";
  runSummary.append("Target: ", el("strong", smiles ? shorten(smiles, 40) : "not set"));
}
smilesInput.addEventListener("input", updateTargetSummary);

// "Try this example" buttons in the tutorial: fill in the target and go to step 1
for (const button of document.querySelectorAll("[data-example-smiles]")) {
  button.addEventListener("click", () => {
    smilesInput.value = button.dataset.exampleSmiles;
    if (editor) { try { editor.readGenericMolecularInput(smilesInput.value); } catch { /* text only */ } }
    smilesInput.value = button.dataset.exampleSmiles;
    updateTargetSummary();
    tabs.show("target");
    window.scrollTo({ top: 0 });
  });
}
updateTargetSummary();
window.jsmeOnLoad = jsmeOnLoad;
if (window.JSApplet && window.JSApplet.JSME) jsmeOnLoad(); // in case JSME loaded first

function showMessage(text, isError = false) {
  message.textContent = text;
  message.className = "message" + (isError ? " error" : "");
  message.hidden = !text;
}

const STATUS_TEXT = {
  queued: "Waiting for a free slot…",
  running: "Searching…",
  done: "Done",
  no_pathway: "No pathway found",
  error: "Something went wrong",
};

runButton.addEventListener("click", async () => {
  const smiles = smilesInput.value.trim();
  if (!smiles) {
    showMessage("Please draw a molecule or enter a SMILES.", true);
    tabs.show("target");
    return;
  }
  if (window.LagerRules && LagerRules.selectedCount() === 0) {
    showMessage("Please select at least one reaction rule.", true);
    tabs.show("rules");
    return;
  }
  showMessage("");
  results.hidden = true;
  pathwaysBox.innerHTML = "";
  logBox.textContent = "";
  searching = true;
  updateRunButton();

  try {
    const response = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ smiles, reactants_id: reactantsId, default_list: selectedDefault().value,
                             disabled_rules: window.LagerRules ? LagerRules.disabledIds() : [] }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not start the search.");
    progress.hidden = false;
    resultsEmpty.hidden = true;
    statusTitle.textContent = STATUS_TEXT.queued;
    tabs.setSummary("results", "searching…", "busy");
    tabs.show("results");
    poll(data.job_id);
  } catch (err) {
    showMessage(err.message, true);
    searching = false;
    updateRunButton();
  }
});

// ---------------------------------------------------------------------------
// Reagents upload
// ---------------------------------------------------------------------------
// The ticked default list (small or extended inventory)
function selectedDefault() {
  return document.querySelector('input[name="default-list"]:checked');
}

function showDefaultReactants() {
  const list = selectedDefault();
  reactantsId = null;
  reactantsStatus.innerHTML = "";
  reactantsStatus.append(
    "Using the default list ",
    el("strong", list.dataset.name),
    ` (${list.dataset.count} molecules).`
  );
  reactantsStatus.classList.remove("error");
  reactantsReport.hidden = true;
  reactantsReport.innerHTML = "";
  reactantsReset.hidden = true;
  tabs.setSummary("reagents", `${list.dataset.name.toLowerCase()} · ${list.dataset.count}`, "");
}

// Choosing a default list replaces an uploaded list
for (const radio of document.querySelectorAll('input[name="default-list"]')) {
  radio.addEventListener("change", () => {
    lastUpload = null;
    reactantsError.hidden = true;
    showDefaultReactants();
  });
}

// A collapsible "N entries ... " line with the names underneath
function addExpandableList(count, names, singular, plural) {
  if (!count) return;
  const details = el("details", undefined, "note warning");
  details.append(el("summary", count === 1 ? `1 ${singular}` : `${count} ${plural}`));
  const list = el("ul");
  for (const name of names) list.append(el("li", name));
  if (count > names.length) list.append(el("li", `… and ${count - names.length} more`));
  details.append(list);
  reactantsReport.append(details);
}

function showUploadedReactants(data) {
  reactantsId = data.reactants_id;
  reactantsStatus.innerHTML = "";
  reactantsStatus.append(
    "Using your list: ",
    el("strong", `${data.n_final} molecules`),
    " after cleaning."
  );
  tabs.setSummary("reagents", `your list · ${data.n_final}`, "ok");
  reactantsStatus.classList.remove("error");

  reactantsReport.innerHTML = "";
  const files = el("ul", undefined, "file-list");
  for (const f of data.files) files.append(el("li", `${f.name}: ${f.molecules} molecules read`));
  reactantsReport.append(files);

  if (data.n_pubchem > 0) {
    reactantsReport.append(el("p",
      `From SDF files: ${data.n_rdkit} structures read directly, ` +
      `${data.n_pubchem} found on PubChem by CAS number or name.`, "note"));
  }
  if (data.pubchem_unreachable) {
    reactantsReport.append(el("p",
      "PubChem could not be reached (no internet connection?), so structures that could not " +
      "be read directly were skipped. Upload the files again when you are online to include them.",
      "note warning-text"));
  }

  // (salts are split into their parts, so the cleaned list can also be longer)
  const removed = data.n_read - data.n_final - data.n_metal_complexes;
  if (removed > 0) {
    reactantsReport.append(el("p",
      removed === 1
        ? "1 entry was removed as a duplicate or invalid structure."
        : `${removed} entries were removed as duplicates or invalid structures.`, "note"));
  }
  addExpandableList(data.n_metal_complexes, data.metal_complexes,
    "entry consists only of metal ions (e.g. [Na+]) and was removed.",
    "entries consist only of metal ions (e.g. [Na+]) and were removed.");
  addExpandableList(data.n_unreadable, data.unreadable,
    "structure in your SDF file(s) could not be read and was skipped.",
    "structures in your SDF file(s) could not be read and were skipped.");
  if (data.n_salts > 0) {
    reactantsReport.append(el("p",
      `${data.n_salts} salts (e.g. KCN, NaI) were converted into their anion ([C-]#N, [I-]) ` +
      "so the reaction rules can use them.", "note"));
  }

  const links = el("p", undefined, "download-links");
  const download = el("a", "Download the cleaned list (CSV)");
  download.href = `/api/reactants/${data.reactants_id}.csv`;
  links.append(download);
  if (data.n_removed_listed > 0) {
    const removedLink = el("a", "Download all removed entries with the reason (CSV)");
    removedLink.href = `/api/reactants/${data.reactants_id}/removed.csv`;
    links.append(removedLink);
  }
  reactantsReport.append(links);

  reactantsReport.hidden = false;
  reactantsReset.hidden = false;
}

// Reading files runs in the background on the server; ask every second how far it is
async function waitForReactants(id) {
  while (true) {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    const response = await fetch(`/api/reactants/${id}`);
    if (!response.ok) throw new Error("The upload was lost (server restarted?). Please upload again.");
    const data = await response.json();
    if (data.status === "done") return data;
    if (data.status === "error") throw new Error(data.error);
    if (data.message) reactantsStatus.textContent = data.message;
  }
}

reactantsFile.addEventListener("change", async () => {
  if (!reactantsFile.files.length) return;
  const form = new FormData();
  for (const file of reactantsFile.files) form.append("files", file);
  reactantsFile.value = "";          // allows uploading the same file again later

  uploading = true;
  updateRunButton();
  reactantsError.hidden = true;
  reactantsStatus.textContent = "Uploading your file(s)…";
  tabs.setSummary("reagents", "reading files…", "busy");
  reactantsReport.hidden = true;
  reactantsReset.hidden = true;

  try {
    const response = await fetch("/api/reactants", { method: "POST", body: form });
    const started = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(started.error || "The upload failed.");
    const data = await waitForReactants(started.reactants_id);
    lastUpload = data;
    showUploadedReactants(data);
  } catch (err) {
    // Keep whatever list was used before, and explain what went wrong
    if (lastUpload) showUploadedReactants(lastUpload);
    else showDefaultReactants();
    reactantsError.textContent = err.message;
    reactantsError.hidden = false;
  } finally {
    uploading = false;
    updateRunButton();
  }
});

reactantsReset.addEventListener("click", () => {
  lastUpload = null;
  reactantsError.hidden = true;
  showDefaultReactants();
});

async function poll(jobId) {
  try {
    const response = await fetch(`/api/jobs/${jobId}`);
    if (!response.ok) throw new Error("The search was lost (server restarted?).");
    const job = await response.json();

    statusTitle.textContent = STATUS_TEXT[job.status] || job.status;
    logBox.textContent = job.log.join("\n");
    logBox.scrollTop = logBox.scrollHeight;

    if (job.status === "queued" || job.status === "running") {
      setTimeout(() => poll(jobId), 2000);
      return;
    }
    searching = false;
    updateRunButton();
    if (job.status === "done") {
      showResults(jobId, job);
      tabs.setSummary("results", `${job.n_pathways} pathway${job.n_pathways === 1 ? "" : "s"}`, "ok");
    }
    if (job.status === "no_pathway") {
      showResultsNote("No complete pathway was found for this molecule with these starting materials " +
                      "and reaction rules.");
      tabs.setSummary("results", "none found", "warn");
    }
    if (job.status === "error") {
      showResultsNote(job.error, true);
      tabs.setSummary("results", "error", "warn");
    }
  } catch (err) {
    showResultsNote(err.message, true);
    tabs.setSummary("results", "error", "warn");
    searching = false;
    updateRunButton();
  }
}

// A note in the results tab (no pathway found, errors)
function showResultsNote(text, isError) {
  resultsEmpty.hidden = false;
  resultsEmptyText.textContent = text;
  resultsEmptyText.className = isError ? "message error" : "hint";
}

function showResults(jobId, job) {
  zipLink.href = `/api/jobs/${jobId}/all.zip`;
  for (let n = 1; n <= job.n_pathways; n++) {
    const base = `/api/jobs/${jobId}/pathway/${n}`;
    const div = document.createElement("div");
    div.className = "pathway";
    div.innerHTML = `
      <h3>Pathway ${n}</h3>
      ${job.has_png[n - 1] ? `<img src="${base}.png" alt="Pathway ${n}">` : ""}
      <div class="links">
        ${job.has_png[n - 1] ? `<a href="${base}.png?download=1">Download PNG</a>` : ""}
        <a href="${base}.json">Download JSON</a>
      </div>`;
    pathwaysBox.appendChild(div);
  }
  results.hidden = false;
}
