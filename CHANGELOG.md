# Changelog

## Unreleased

- Server hostname is now read from the `SRD_REMOTE_HOST` environment variable instead of being hardcoded; srd exits with a clear message if it (or `SRD_REMOTE_USER`) is unset in SFTP/push modes
- Documentation and examples use placeholder hostnames, usernames and paths
- Fix stale install URL in `INSTALL_UBUNTU.md`
- New optional `SRD_DEST_MODE` env var sets the permissions of everything pushed to the server: the folder created by `--push --create-dest` and the files/folders rsync copies into it (default remains `777`, exactly as before; other modes give files the same mode without execute bits)
- Security: remote paths and filenames are now shell-quoted in all commands run on the server (previously a space, `;` or `'` in a path or filename could break or alter the command)
- SSH control socket moved from `/tmp` to `~/.ssh/` (private to the user). **Run `srd --open-ssh` again after upgrading.**
- Fix: remote statistics script had a bash syntax error (`[[` without spaces); fixed
- Fix: server-side MD5 mismatch / missing sidecar / unreadable sidecar messages printed the literal text `{rel}` instead of the filename
- Fix: clear error message (instead of a traceback) when `SRD_LOG_DIR` is unset or cannot be created

## v1.2 — September 2026

- Pre-flight sidecar check: warns before transfer if any source files lack `.md5` sidecars; prompts halt or continue
- Source path retry prompt: if source directory is not found (e.g. unmounted drive), srd prompts to mount and retry without restarting
- File count logic corrected: extra files at destination produce a yellow NOTE rather than a FAIL; FAIL only when destination has fewer files than source
- Integrity verification scoped to remote manifest (not local manifest)
- Fix: directory timestamp permission error on push resolved with `--omit-dir-times`
- Fix: missing `full_source_bytes` field in TransferStats
- Package renamed from `smpl-replicate-directory` to `srd`
- Install source moved to org repo: `Stanford-Media-Preservation-Lab/srd`

## v1.1 — May 2026

- `--version` / `-v` flag
- `--role` filter with rsync include/exclude rules, case-insensitive matching, and nested directory support
- Role code validation before transfer begins
- Transfer size display scoped to active role filter
- Live MD5 progress; purple two-line progress bars; HH:MM:SS duration display
- Colored help text; directory tree recovery
- `SRD_REMOTE_USER` env var for remote server username
- `SRD_LOG_DIR` env var for log output directory — no script editing required after install

## v1.0 — initial release

- Three transfer modes: pull from server (SFTP), local disk-to-disk, push to server
- MD5 sidecar verification after every transfer
- SSH ControlMaster for Duo two-factor authentication (macOS and Ubuntu)
- Role code filtering (`--role pm`, `--role sl`, etc.)
- `--create-dest`, `--resume`, `--compress`, `--csv` flags
- Cross-platform: single codebase for macOS and Ubuntu 24.04

## v0.1.0 — initial commit