// Minimal front end: draw or paste a molecule, start a search, show results.

const smilesInput = document.getElementById("smiles");
const runButton = document.getElementById("run");
const message = document.getElementById("message");
const progress = document.getElementById("progress");
const statusTitle = document.getElementById("status");
const logBox = document.getElementById("log");
const results = document.getElementById("results");
const pathwaysBox = document.getElementById("pathways");
const zipLink = document.getElementById("zip");

let editor = null;

// JSME calls this function automatically once it has loaded
function jsmeOnLoad() {
  const width = Math.min(560, document.getElementById("editor").clientWidth);
  editor = new JSApplet.JSME("editor", width + "px", "340px");
  // Drawing a molecule writes its SMILES into the text field
  editor.setAfterStructureModifiedCallback(() => {
    smilesInput.value = editor.smiles();
  });
}
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
    return;
  }
  showMessage("");
  results.hidden = true;
  pathwaysBox.innerHTML = "";
  logBox.textContent = "";
  runButton.disabled = true;

  try {
    const response = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ smiles }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not start the search.");
    progress.hidden = false;
    statusTitle.textContent = STATUS_TEXT.queued;
    poll(data.job_id);
  } catch (err) {
    showMessage(err.message, true);
    runButton.disabled = false;
  }
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
    runButton.disabled = false;
    if (job.status === "done") showResults(jobId, job);
    if (job.status === "no_pathway") {
      showMessage("No complete pathway was found for this molecule with the default settings.");
    }
    if (job.status === "error") showMessage(job.error, true);
  } catch (err) {
    showMessage(err.message, true);
    runButton.disabled = false;
  }
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
