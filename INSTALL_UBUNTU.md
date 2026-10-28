# Installing srd on Ubuntu 24.04

**srd v1.3 — October 2026**

---

## Requirements

- Ubuntu 24.04 LTS
- Python 3.9 or later (Python 3.12 is the default on Ubuntu 24.04)
- rsync (installed by default)
- pipx (recommended installer)

Check your Python version:

```bash
python3 --version
```

---

## Before installing: remove old versions

If srd was previously installed via pip or by copying a script, remove those copies first:

```bash
pipx uninstall smpl-replicate-directory 2>/dev/null
sudo rm -f /usr/local/bin/srd
```

Then confirm nothing is left:

```bash
which -a srd
```

---

## Install via pipx (recommended)

```bash
pip3 install --break-system-packages pipx   # if pipx is not already installed
pipx install git+https://github.com/Stanford-Media-Preservation-Lab/srd.git
```

Make sure pipx's bin directory is on your PATH. Add this to `~/.bashrc` or `~/.zshrc` if needed:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Verify:

```bash
srd --version
```

---

## Configuration

No script editing required. Add three lines to `~/.bashrc` or `~/.zshrc` (your sysadmin can give you the server hostname):

```bash
export SRD_REMOTE_HOST="your-server-hostname"
export SRD_REMOTE_USER="your_server_username"
export SRD_LOG_DIR="/home/yourname/srd_logs"
```

Then reload:

```bash
source ~/.bashrc   # or source ~/.zshrc
```

`SRD_REMOTE_HOST` is the SSH hostname of the remote server. `SRD_REMOTE_USER` is your username on the remote server.
`SRD_LOG_DIR` is where srd will save log, tree, and CSV files. It will be created automatically if it does not exist.

These variables persist across upgrades — you will never need to edit the script again after setting them.

---

## Duo two-factor authentication

The staging server requires Duo two-factor authentication. srd handles this using SSH ControlMaster — you authenticate once interactively, and all subsequent SSH connections and rsync transfers reuse that session transparently.

**Before running any SFTP or push transfer, open a persistent SSH session:**

```bash
srd --open-ssh
```

Approve the Duo prompt (typically option 1 for a push notification). The session is held open in the background.

Run srd normally in any other terminal:

```bash
srd /path/on/server/request-0001 /media/yourname/RAID_1/260219
```

**The control socket does not survive a reboot.** After restarting your workstation, run `srd --open-ssh` again before your first transfer of the session.

If you forget, srd will tell you clearly:

```
✗ SSH control socket not found
  Run:  srd --open-ssh  and approve the Duo prompt first.
```

---

## Updating

```bash
pipx upgrade smpl-replicate-directory
```

---

## Finding the installed cli.py

If you ever need to inspect the installed script directly:

```bash
find ~/.local/pipx -name "cli.py" -path "*/srd/*"
```
