---
id: hpc_data_transfer
name: HPC Data Transfer via SSH
description: |
  Transfer data between local machine and HPC clusters (e.g. Stanford Sherlock)
  that require interactive authentication (password + Duo/MFA). Uses pexpect
  for automated login and SSH ControlMaster for persistent connection reuse.
tags: [ssh, hpc, rsync, data-transfer, sherlock, duo]
---

# HPC Data Transfer via SSH

Transfer data to/from HPC clusters that require interactive authentication
(password + Duo two-factor). This workflow establishes a single authenticated
SSH connection, then reuses it for all subsequent transfers without re-authenticating.

## Prerequisites

```python
# pexpect is required for interactive SSH authentication
import pexpect  # usually pre-installed with Python
```

The user's `~/.ssh/config` should have the HPC host configured, e.g.:

```
Host sherlock
  HostName login.sherlock.stanford.edu
  User wzxu
```

## Workflow

### Step 1: Establish SSH ControlMaster Connection

Use `pexpect` to handle the interactive password + Duo prompts, then keep the
connection alive via SSH ControlMaster. All subsequent SSH/rsync/scp commands
will reuse this connection without re-authenticating.

```python
import pexpect
import sys

CONTROL_PATH = "/tmp/sherlock-ssh"
SSH_HOST = "sherlock"  # as configured in ~/.ssh/config

def establish_ssh_connection(password: str, control_path: str = CONTROL_PATH, host: str = SSH_HOST):
    """
    Establish a persistent SSH ControlMaster connection with Duo MFA.
    The user must approve the Duo push on their phone.
    """
    child = pexpect.spawn(
        f'ssh -o ControlMaster=yes -o ControlPath={control_path} '
        f'-o ControlPersist=3600 {host} "echo CONNECTED_OK"',
        timeout=60
    )
    child.logfile_sys = sys.stdout.buffer

    idx = child.expect(['[Pp]assword:', 'CONNECTED_OK', pexpect.EOF, pexpect.TIMEOUT], timeout=30)
    if idx == 0:
        child.sendline(password)

        idx2 = child.expect(['Duo', 'CONNECTED_OK', '[Pp]assword:', pexpect.EOF, pexpect.TIMEOUT], timeout=30)
        if idx2 == 0:
            # Send '1' to select Duo Push (option 1)
            child.sendline('1')
            # Wait for user to approve on phone
            idx3 = child.expect(['CONNECTED_OK', 'Success', pexpect.EOF, pexpect.TIMEOUT], timeout=120)
            if idx3 not in [0, 1]:
                raise RuntimeError(f"Duo approval failed or timed out: {child.before}")
        elif idx2 == 1:
            pass  # Connected without Duo
        elif idx2 == 2:
            raise RuntimeError("Password rejected")
        else:
            raise RuntimeError(f"Unexpected response: {child.before}")
    elif idx == 1:
        pass  # Already connected

    child.expect(pexpect.EOF, timeout=30)
    child.close()

    if child.exitstatus != 0:
        raise RuntimeError(f"SSH connection failed with exit status {child.exitstatus}")

    return True
```

> [!IMPORTANT]
> The user MUST approve the Duo push on their phone within ~60 seconds.
> Ask the user for their password before calling this function. Do not store it.

### Step 2: Verify Connection

```python
import subprocess

def ssh_cmd(cmd: str, control_path: str = CONTROL_PATH, host: str = SSH_HOST):
    """Run a command on the remote host using the persistent connection."""
    result = subprocess.run(
        ["ssh", "-o", f"ControlPath={control_path}", host, cmd],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout.strip()

# Verify
print(ssh_cmd("echo connected"))  # Should print "connected"
```

### Step 3: Transfer Data

Use `rsync` with the ControlMaster socket for efficient, resumable transfers.

```bash
# Download: remote → local
rsync -avz --progress \
  -e "ssh -o ControlPath=/tmp/sherlock-ssh" \
  sherlock:/remote/path/ \
  /local/path/

# Upload: local → remote
rsync -avz --progress \
  -e "ssh -o ControlPath=/tmp/sherlock-ssh" \
  /local/path/ \
  sherlock:/remote/path/
```

#### Parallel Downloads

For multiple independent directories, run rsync in parallel:

```python
import subprocess

transfers = [
    ("/oak/remote/dir1/", "/local/dir1/"),
    ("/oak/remote/dir2/", "/local/dir2/"),
    ("/oak/remote/dir3/", "/local/dir3/"),
]

procs = []
for remote, local in transfers:
    p = subprocess.Popen([
        "rsync", "-avz", "--progress",
        "-e", f"ssh -o ControlPath={CONTROL_PATH}",
        f"{SSH_HOST}:{remote}", local
    ])
    procs.append((remote, p))

# Wait for all to complete
for remote, p in procs:
    p.wait()
    print(f"{'OK' if p.returncode == 0 else 'FAILED'}: {remote}")
```

#### Resume Interrupted Transfers

rsync is resumable by default. If a transfer is interrupted, re-run the same
command — it will skip already-transferred files and resume partial ones.

After transfer, verify file counts match:

```python
remote_count = int(ssh_cmd(f"find {remote_path} -type f | wc -l"))
local_count = len(list(Path(local_path).rglob("*")))
assert remote_count == local_count, f"Mismatch: remote={remote_count}, local={local_count}"
```

### Step 4: Clean Up

The ControlMaster connection persists for 1 hour (ControlPersist=3600).
To close it manually:

```bash
ssh -o ControlPath=/tmp/sherlock-ssh -O exit sherlock
```

## Key Parameters

| Parameter | Value | Purpose |
|---|---|---|
| `ControlMaster=yes` | Enable connection sharing | First connection becomes the master |
| `ControlPath=/tmp/sherlock-ssh` | Socket file path | All subsequent connections use this socket |
| `ControlPersist=3600` | Keep alive 1 hour | Connection stays open after initial session ends |

## Troubleshooting

- **"Permission denied"**: ControlMaster session expired. Re-run Step 1.
- **rsync missing files**: Re-run the same rsync command — it will only transfer missing/changed files.
- **Duo timeout**: Increase the pexpect timeout in the `expect` call (default 120s).
- **Multiple HPC hosts**: Use different `ControlPath` values for each host.
