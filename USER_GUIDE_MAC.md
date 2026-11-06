# LAGER on macOS – Quick Start for Chemists

LAGER runs in your web browser. You do not need to install Python or use a terminal.
In the background, it uses a free program called **Docker Desktop**.

**What you need**
- A Mac with a recent version of macOS
- About 5 GB of free disk space
- An internet connection for the first start
- Your Mac's administrator password **once**, to install Docker Desktop (or help from your IT department)

**At a glance:** install Docker Desktop and download LAGER once (Steps 1–2).
After that, starting LAGER takes three clicks (Step 3).

---

## Step 1: Install Docker Desktop (once)

1. **Check your chip type:** click the Apple menu  → **About This Mac**:
   - "Chip: Apple M1/M2/M3/M4…" → you need **Docker Desktop for Mac with Apple silicon**.
     LAGER runs slower on these Macs, because it is translated for the Apple chip (see the note below).
   - "Processor: … Intel …" → you need **Docker Desktop for Mac with Intel chip**.
2. Download that version from https://www.docker.com/products/docker-desktop/
3. Open the downloaded `Docker.dmg` and drag **Docker** into the **Applications** folder.
4. Open **Docker** from the Applications folder. Enter your administrator password if asked.
   - Accept the license agreement and keep the recommended settings.
   - You can **skip signing in** ("Continue without signing in"); LAGER does not need a Docker account.
5. Wait until Docker Desktop shows **"Engine running"** (bottom left, green).

> **Apple silicon Macs (M1–M4):** in Docker Desktop, open **Settings** (gear icon) → **General** and make sure
> **"Use Rosetta for x86_64/amd64 emulation on Apple Silicon"** is switched on. This makes LAGER noticeably faster.

---

## Step 2: Download LAGER (once)

1. In Finder, create an empty folder for LAGER's reaction rules, e.g. `LAGER_rules` in your home folder.
2. In Docker Desktop, click the **search bar at the top** and type `arinashelashen/lager`.
3. Click **Pull** next to `arinashelashen/lager`.
   LAGER is downloaded (a few GB). This takes several minutes.
4. Go to **Images** (left menu). Find `arinashelashen/lager` and click the **Run** button (▶).
   On Apple silicon Macs, a note about a different "platform" (amd64) may appear. That is expected; continue.
5. In the window that opens, click **Optional settings** and enter:
   - **Container name:** `lager`
   - **Host port:** `5001`
   - **Volumes:** click **+** and enter
     - **Host path:** the folder you created before this step (click **…** to choose it), e.g. `/Users/YOUR-NAME/LAGER_rules`
     - **Container path:** `/data/user_rules`
6. Click **Run**.

> **Why the folder?** Reaction rules that you or colleagues add on the LAGER page are saved there.
> Without it, they are lost when the container is deleted, e.g. for an update.

> **Why port 5001?** On Macs, port 5000 is usually taken by the AirPlay Receiver.

---

## Step 3: Start and open LAGER

**The first time**, LAGER is already running after Step 2.

**Every next time:**
1. Open **Docker** from the Applications folder and wait for **"Engine running"**.
2. Go to **Containers** (left menu) and click the **Start** button (▶) next to `lager`.

**To open LAGER:** in **Containers**, click the link **5001:5000** next to `lager`.
Your browser opens LAGER (http://localhost:5001). If the page does not load yet, wait a few seconds and reload it (⌘R).

---

## Step 4: Find a synthesis pathway

1. **Draw** your target molecule in the editor, or **paste its SMILES** into the field below it.
2. Click **Find pathways**.
3. Wait while the search runs. You can follow its progress on the page. Depending on the molecule, this takes from seconds to several minutes (longer on Apple silicon Macs).
4. The pathways appear as images. For each pathway you can
   - **Download PNG** (the image),
   - **Download JSON** (all steps and molecules in a machine-readable file),
   - or use **Download all (ZIP)** for everything at once.

**Your results are not stored.** Download what you need before you stop LAGER or start a new search.

---

## Step 5: Stop LAGER

1. In Docker Desktop, go to **Containers** and click the **Stop** button (■) next to `lager`.
2. To free your computer's memory, also quit Docker Desktop: click the **whale icon** in the menu bar (top right) → **Quit Docker Desktop**.

---

## Updating to a new version

When you are told that a new LAGER version is available:

1. **Containers:** stop `lager` (■), then delete it (🗑).
2. **Images:** find `arinashelashen/lager`, open the **⋮** menu and choose **Pull**.
3. Start it again as in **Step 2, points 4–6**, with the same rules folder. Your added rules are still there.

---

## Troubleshooting

| Message or problem | What to do |
|---|---|
| `arinashelashen/lager` is not found in the search | Check the spelling. Make sure you are connected to the internet. |
| "Port is already allocated" when clicking Run | Another program uses this port. Repeat Step 2, points 4–6, with **Host port** `5002`, and open http://localhost:5002 |
| The browser page does not load | Check in **Containers** that `lager` is running (green). Wait a few seconds and reload (⌘R). |
| LAGER is very slow | On Apple silicon Macs, check the Rosetta setting (see the note in Step 1). |
| "No pathway found" | LAGER could not build the molecule from the available starting materials and reactions with the standard settings. Try a related or simpler structure. |

**Questions or problems?** Contact Arina Shelashen (arishashelashen@gmail.com).
