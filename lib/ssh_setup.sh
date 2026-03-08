# ─────────────────────────────────────────────────────────
# lib/ssh_setup.sh — SSH-specific setup for EnergyTracer
#
# Sourced (not executed) by run_experiment.sh when an SSH session
# is detected on a mac machine. Do not run this file directly.
# ─────────────────────────────────────────────────────────

# ── Why this file exists ──────────────────────────────────
#
# tmux keeps the process alive when you disconnect — that is its job
# and it works correctly. The problems addressed here are different,
# and operate at the macOS kernel level:
#
#   1. IDLE SLEEP
#      With no active user session, macOS may put the machine to sleep
#      even while tmux processes are running. caffeinate -i prevents this.
#
#   2. BACKGROUND CPU THROTTLING  ← the real cause of the ~2x slowdown
#      macOS assigns a QoS (Quality of Service) class to every process.
#      When no GUI/user session is active, background processes are
#      silently moved to QOS_CLASS_BACKGROUND, which dramatically
#      limits the CPU time they receive. tmux has no control over this.
#      caffeinate -s keeps the system in a fully "active" state and
#      prevents the kernel from downgrading QoS tiers.
#
#   3. SUDO EXPIRY FOR POWERMETRICS
#      CodeCarbon calls powermetrics internally, which requires root.
#      A standard `sudo -v` credential expires after ~15 minutes, long
#      before the experiment finishes. A temporary NOPASSWD sudoers rule
#      provides persistent, passwordless access for the script's lifetime
#      and is removed automatically on exit.

# ── sudo credentials ──────────────────────────────────────

if ! sudo -n true 2>/dev/null; then
    if ! tty -s; then
        error "sudo credentials not cached and no TTY available."
        error "Run ${BOLD}sudo -v${RST} before detaching from tmux."
        return 1
    fi
    sudo -v || { error "sudo is required for powermetrics."; return 1; }
fi

# Install a temporary NOPASSWD rule scoped to this user.
# /private/etc is the real path on macOS (not a symlink like /etc).
SUDOERS_FILE="/private/etc/sudoers.d/energytracer_tmp"
echo "$USER ALL=(ALL) NOPASSWD: ALL" | sudo tee "$SUDOERS_FILE" > /dev/null
sudo chmod 440 "$SUDOERS_FILE"

# ── caffeinate ────────────────────────────────────────────
#
# Flags:
#   -d  prevent display sleep          (keeps the session "visible")
#   -i  prevent idle sleep             (no system idle sleep)
#   -m  prevent disk sleep             (keeps I/O responsive)
#   -s  prevent system sleep (AC only) (maintains full CPU QoS tier)
#   -w $$ wait for this script's PID   (auto-exits when the script ends)
#
# Spawned as a background job so it runs for the full script duration,
# not just around individual commands. This is intentional: the QoS
# throttling applies to the entire absence of an active session, not
# only during active computation.

caffeinate -dims -w $$ &
CAFFEINATE_PID=$!

# ── Cleanup on exit ───────────────────────────────────────
# Removes the sudoers rule and kills caffeinate when the parent
# script exits, for any reason (normal exit, error, or signal).

trap 'sudo rm -f "$SUDOERS_FILE"; kill "$CAFFEINATE_PID" 2>/dev/null' EXIT
