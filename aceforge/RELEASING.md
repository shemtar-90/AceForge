# Releasing ACEForge

How to publish a new version. Once the repo is on GitHub, this is
the only process you need to follow for every release.

---

## First-time setup (do this once)

### 1. Create a GitHub account
If you don't have one: https://github.com/signup

### 2. Create a new repository
1. Go to https://github.com/new
2. Name it `ACEForge`
3. Set it to **Public** (so others can download releases)
4. Do **not** initialize with a README (you already have one)
5. Click **Create repository**

### 3. Push the code to GitHub
Open a terminal (Command Prompt or PowerShell) in the ACEForge folder:

```
git init
git add .
git commit -m "Initial release"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ACEForge.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username.

### 4. Verify the workflow file is there
On GitHub, go to your repo and confirm this file exists:
```
.github/workflows/build-release.yml
```

---

## Publishing a release

Every time you want to release a new version:

### Step 1 — Make your changes
Edit whatever code you want to change. Test locally if possible.

### Step 2 — Commit your changes
```
git add .
git commit -m "Description of what changed"
git push
```

### Step 3 — Tag the release
Tags trigger the automatic build. The tag must start with `v`:

```
git tag v1.0.0
git push origin v1.0.0
```

### Step 4 — Wait for the build (~5 minutes)
GitHub Actions will:
1. Spin up a Windows machine in the cloud
2. Install Python and all dependencies
3. Run PyInstaller to build `ACEForge.exe`
4. Bundle everything into `ACEForge_1.0.0_Windows.zip`
5. Create a GitHub Release and attach the zip

### Step 5 — Share the link
Go to your repo → **Releases** (right sidebar).
Copy the link to the release and share it with your users.

Users download the zip, extract it, and double-click `ACEForge.exe`. Done.

---

## Monitoring the build

While the build is running:
1. Go to your GitHub repo
2. Click **Actions** (top tab)
3. Click the running workflow to see live logs

If something fails, the logs tell you exactly what went wrong.

---

## Version numbering

Use semantic versioning: `vMAJOR.MINOR.PATCH`

| Change type | Example | When to use |
|------------|---------|-------------|
| Bug fix | v1.0.1 | Fixed a crash, corrected wrong SQL output |
| New feature | v1.1.0 | Added a new tab, new content type |
| Major change | v2.0.0 | Redesigned UI, breaking config changes |

---

## Updating the version number in the code

Before tagging, update the version string in two places:

**`aceforge/__init__.py`**
```python
__version__ = "1.0.1"
```

**`aceforge/app.py`**
```python
APP_VERSION = "1.0.1"
```

Then commit, push, and tag:
```
git add .
git commit -m "Bump version to 1.0.1"
git push
git tag v1.0.1
git push origin v1.0.1
```

---

## Reference files and GitHub

The reference files (`aceforge/references/*.md`, `all_spells.txt`, etc.)
are large. You have two options:

**Option A — Commit them to the repo (simplest)**
Just `git add aceforge/references/` and commit. GitHub allows files up to 100MB.
The workflow will bundle them into the release automatically.

**Option B — Git LFS (for files over 50MB)**
If any reference files are large, install Git LFS:
```
git lfs install
git lfs track "aceforge/references/all_spells.txt"
git add .gitattributes
git add aceforge/references/
git commit -m "Add reference files via LFS"
```

The `.gitignore` has commented-out lines you can uncomment to exclude
specific large files if needed.

---

## Testing a build without releasing

You can trigger the workflow manually without creating a release:
1. Go to your repo → **Actions**
2. Click **Build and Release ACEForge**
3. Click **Run workflow** → **Run workflow**

This builds the exe and makes it available as a workflow artifact
(downloadable from the Actions tab) without creating a public release.

---

## What the release page looks like

After a successful tag push, your release page will show:
- Release title: `ACEForge 1.0.0`
- Auto-generated changelog (based on commit messages since last tag)
- Your installation instructions
- A download link for `ACEForge_1.0.0_Windows.zip`

Users click the zip, extract, run. That's it.
