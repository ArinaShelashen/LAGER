# LAGER on Windows – Quick Start for Chemists

LAGER runs in your web browser. You do not need to install Python or use a terminal.
In the background, it uses a free program called **Docker Desktop**.

**What you need**
- A Windows 10 or 11 laptop
- About 5 GB of free disk space
- An internet connection for the first start
- Administrator rights **once**, to install Docker Desktop (or help from your IT department)

**At a glance:** install Docker Desktop and download LAGER once (Steps 1–2).
After that, starting LAGER takes three clicks (Step 3).

---

## Step 1: Install Docker Desktop (once)

1. **Check your processor type:** open **Settings → System → About** and look at **System type**:
   - "x64-based processor" → you need **AMD64** (almost all laptops with Intel or AMD processors)
   - "ARM-based processor" → you need **ARM64** (some laptops with Qualcomm Snapdragon processors).
     LAGER is slower on these laptops and may not work on all of them.
2. Download **Docker Desktop for Windows** in that version from https://www.docker.com/products/docker-desktop/
3. Run the installer and keep the default settings (including **"Use WSL 2"**).
4. Restart your computer when asked.
5. Open **Docker Desktop** from the Start menu.
   - Accept the license agreement.
   - You can **skip signing in** ("Continue without signing in"); LAGER does not need a Docker account.
6. Wait until Docker Desktop shows **"Engine running"** (bottom left, green).

> **If your IT department installs Docker Desktop for you:** ask them to add your Windows account to the
> **docker-users** group. Without it, Docker Desktop cannot start LAGER for you.

---

## Step 2: Download LAGER (once)

1. In File Explorer, create an empty folder for LAGER's reaction rules, e.g. `C:\Users\YOUR-NAME\LAGER_rules`.
2. In Docker Desktop, click the **search bar at the top** and type `USERNAME/lager`.
3. Click **Pull** next to `USERNAME/lager`.
   LAGER is downloaded (a few GB). This takes several minutes.
4. Go to **Images** (left menu). Find `USERNAME/lager` and click the **Run** button (▶).
5. In the window that opens, click **Optional settings** and enter:
   - **Container name:** `lager`
   - **Host port:** `5000`
   - **Volumes:** click **+** and enter
     - **Host path:** the folder you created before this step (click **…** to choose it), e.g. `C:\Users\YOUR-NAME\LAGER_rules`
     - **Container path:** `/data/user_rules`
6. Click **Run**.

> **Why the folder?** Reaction rules that you or colleagues add on the LAGER page are saved there.
> Without it, they are lost when the container is deleted, e.g. for an update.

> If Windows asks whether Docker may access the network, choose **Cancel** / **Don't allow**.
> LAGER works without it, and your molecules stay on your computer.

---

## Step 3: Start and open LAGER

**The first time**, LAGER is already running after Step 2.

**Every next time:**
1. Open **Docker Desktop** and wait for **"Engine running"**.
2. Go to **Containers** (left menu) and click the **Start** button (▶) next to `lager`.

**To open LAGER:** in **Containers**, click the link **5000:5000** next to `lager`.
Your browser opens LAGER (http://localhost:5000). If the page does not load yet, wait a few seconds and refresh it (F5).

---

## Step 4: Find a synthesis pathway

1. **Draw** your target molecule in the editor, or **paste its SMILES** into the field below it.
2. Click **Find pathways**.
3. Wait while the search runs. You can follow its progress on the page. Depending on the molecule, this takes from seconds to several minutes.
4. The pathways appear as images. For each pathway you can
   - **Download PNG** (the image),
   - **Download JSON** (all steps and molecules in a machine-readable file),
   - or use **Download all (ZIP)** for everything at once.

**Your results are not stored.** Download what you need before you stop LAGER or start a new search.

---

## Step 5: Stop LAGER

1. In Docker Desktop, go to **Containers** and click the **Stop** button (■) next to `lager`.
2. To free your computer's memory, also quit Docker Desktop: right-click the **whale icon** in the taskbar (bottom right) → **Quit Docker Desktop**.

---

## Updating to a new version

When you are told that a new LAGER version is available:

1. **Containers:** stop `lager` (■), then delete it (🗑).
2. **Images:** find `USERNAME/lager`, open the **⋮** menu and choose **Pull**.
3. Start it again as in **Step 2, points 4–6**, with the same rules folder. Your added rules are still there.

---

## Troubleshooting

| Message or problem | What to do |
|---|---|
| Docker Desktop: "Virtualization support not detected" | Virtualization must be enabled in the computer's BIOS. Ask your IT department. |
| Docker Desktop: "You are not allowed to use Docker" | Your account is not in the **docker-users** group. Ask your IT department (see Step 1). |
| `USERNAME/lager` is not found in the search | Check the spelling. Make sure you are connected to the internet. |
| "Port is already allocated" when clicking Run | Another program uses port 5000. Repeat Step 2, points 4–6, with **Host port** `5001`, and open http://localhost:5001 |
| The browser page does not load | Check in **Containers** that `lager` is running (green). Wait a few seconds and refresh (F5). |
| "No pathway found" | LAGER could not build the molecule from the available starting materials and reactions with the standard settings. Try a related or simpler structure. |

**Questions or problems?** Contact Arina Shelashen (arina@bioinf.uni-leipzig.de).
