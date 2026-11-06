# LAGER on Linux – Quick Start

LAGER runs in your web browser. It uses **Docker**, so you do not need to install MØD, Python or any other dependency yourself.

**What you need**
- A Linux computer with an Intel or AMD (x86-64) processor
- About 5 GB of free disk space
- An internet connection for the first start
- Administrator rights (`sudo`) **once**, to install Docker (or help from your IT department)

---

## Step 1: Install Docker (once)

**Check first:** if Docker is already installed and you are allowed to use it, this command prints a "Hello from Docker!" message, and you can go straight to Step 2:

```bash
docker run --rm hello-world
```

Otherwise:

1. Install **Docker Engine** following the instructions for your distribution:
   https://docs.docker.com/engine/install/
   (On Ubuntu and Debian, the distribution package also works: `sudo apt install docker.io`.)
2. Allow your user to run Docker without `sudo`:
   ```bash
   sudo usermod -aG docker $USER
   ```
3. **Log out and log in again** (or restart), so the change takes effect.
4. Test it with `docker run --rm hello-world`.

> On a shared or managed computer, ask your administrator to add your account to the **docker** group.

---

## Step 2: Download the LAGER start script (once)

```bash
curl -O https://raw.githubusercontent.com/ArinaShelashen/LAGER/BRANCH/start_lager.sh
chmod +x start_lager.sh
```

---

## Step 3: Start LAGER

```bash
./start_lager.sh
```

- **The first start takes several minutes**, because LAGER is downloaded (a few GB). Later starts take a few seconds.
- Your browser opens **http://localhost:5000** with LAGER. If it does not open by itself, open this address manually.
- **Keep the terminal window open while you work.**

LAGER is only reachable from your own computer, not from the network.

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

Press **Enter** in the terminal window where LAGER is running.

---

## Updates

The start script checks for a new LAGER version on every start and downloads it automatically.
Reaction rules added on the LAGER page are kept in the Docker volume `lager_rules` and survive updates.
Without an internet connection, the version already on your computer is used.

---

## Without the start script

The start script only runs these commands, which you can also use directly:

```bash
docker pull arinashelashen/lager:latest
docker run --rm --name lager -p 127.0.0.1:5000:5000 -v lager_rules:/data/user_rules arinashelashen/lager:latest
```

Then open http://localhost:5000. Stop LAGER with **Ctrl+C**.

---

## Troubleshooting

| Message or problem | What to do |
|---|---|
| "Docker is not running (or you have no permission to use it)" | Start Docker with `sudo systemctl start docker`. If it is running, your user is not in the **docker** group (see Step 1, points 2–3). |
| "permission denied … docker.sock" | Your user is not in the **docker** group, or you have not logged out and in again since adding it. |
| "Is port 5000 already used by another program?" | Start LAGER on another port: `LAGER_PORT=5001 ./start_lager.sh`, then open http://localhost:5001 |
| The browser page does not load | Wait a few seconds and reload. On the first start, wait until the download has finished. |
| "No pathway found" | LAGER could not build the molecule from the available starting materials and reactions with the standard settings. Try a related or simpler structure. |

**Questions or problems?** Contact Arina Shelashen (arishashelashen@gmail.com).
