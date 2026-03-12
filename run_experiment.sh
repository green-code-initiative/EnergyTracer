#!/usr/bin/env sh

# ─────────────────────────────────────────────────────────
# EnergyTracer — Experiment Runner
# ─────────────────────────────────────────────────────────

# ── ANSI colors ──────────────────────────────────────────

RST="\033[0m"
BOLD="\033[1m"
DIM="\033[2m"

RED="\033[31m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
MAGENTA="\033[35m"
CYAN="\033[36m"
WHITE="\033[37m"

# ── Logging helpers ──────────────────────────────────────

info()  { printf "  ${CYAN}ℹ${RST}  %b\n" "$*"; }
ok()    { printf "  ${GREEN}✔${RST}  %b\n" "$*"; }
warn()  { printf "  ${YELLOW}⚠${RST}  %b\n" "$*"; }
error() { printf "  ${RED}✖${RST}  %b\n" "$*"; }
dim()   { printf "  ${DIM}%b${RST}\n" "$*"; }

# ── Argument parsing ─────────────────────────────────────

usage() {
    echo ""
    printf "  ${BOLD}Usage:${RST} $0 ${CYAN}<mode>${RST}\n"
    echo ""
    printf "  ${BOLD}Supported modes:${RST}\n"
    printf "    ${GREEN}carbon${RST}    CodeCarbon only (cross-platform)\n"
    printf "    ${GREEN}mac${RST}       mac profiler only (Apple Silicon)\n"
    printf "    ${GREEN}both${RST}      CodeCarbon + mac (Apple Silicon)\n"
    echo ""
    printf "  ${BOLD}Examples:${RST}\n"
    printf "    $0 carbon    ${DIM}# Any platform: runs CodeCarbon only${RST}\n"
    printf "    $0 mac       ${DIM}# Apple Silicon: runs mac profiler only${RST}\n"
    printf "    $0 both      ${DIM}# Apple Silicon: runs both profilers${RST}\n"
    echo ""
    exit 1
}

# Map mode -> profiler list.
#   carbon → runs 'carbon' only
#   mac    → runs 'mac' only
#   both   → runs both 'carbon' and 'mac'
case "$1" in
    carbon)
        MACHINE="carbon"
        PROFILERS="carbon"
        ;;
    mac)
        MACHINE="mac"
        PROFILERS="mac"
        ;;
    both)
        MACHINE="mac"
        PROFILERS="carbon mac"
        ;;
    "")   error "Mode argument is required."; usage ;;
    *)    error "Unknown mode '${BOLD}$1${RST}'."; usage ;;
esac

NUM_PROFILERS=$(echo $PROFILERS | wc -w | tr -d ' ')

# ── Configuration ────────────────────────────────────────

BAR_WIDTH=30

WARMUP_RUNS=10          # Number of warm-up iterations
WARMUP_N=500            # Code iterations per warm-up run

MEASURE_RUNS=30         # Number of measurement iterations
MEASURE_N=1000          # Code iterations per measurement run
COOLDOWN=60             # Sleep duration (seconds) between measurements

OUTPUT_DIR="output"

# ── SSH detection & setup ─────────────────────────────────
# $SSH_CLIENT / $SSH_TTY / $SSH_CONNECTION are set by sshd and
# inherited by tmux child processes — they survive detach/reattach.
# When detected, we source lib/ssh_setup.sh which handles:
#   - sudo persistence (NOPASSWD sudoers rule for powermetrics)
#   - caffeinate (prevents both idle sleep and background CPU throttling)
# See lib/ssh_setup.sh for the full rationale.

IS_SSH=0
if [ -n "$SSH_CLIENT" ] || [ -n "$SSH_TTY" ] || [ -n "$SSH_CONNECTION" ]; then
    IS_SSH=1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$IS_SSH" = "1" ] && echo "$PROFILERS" | grep -q mac; then
    # shellcheck source=lib/ssh_setup.sh
    . "$SCRIPT_DIR/lib/ssh_setup.sh" || exit 1
fi

# ── Helpers ──────────────────────────────────────────────

# Formats seconds into a compact duration string.
# Result stored in _FMT (no subprocess spawned).
fmt() {
    _t=$1; _h=$((_t / 3600)); _m=$((_t % 3600 / 60)); _s=$((_t % 60))
    if [ "$_h" -gt 0 ]; then
        [ "$_m" -lt 10 ] && _m="0$_m"
        [ "$_s" -lt 10 ] && _s="0$_s"
        _FMT="${_h}h${_m}m${_s}s"
    elif [ "$_m" -gt 0 ]; then
        [ "$_s" -lt 10 ] && _s="0$_s"
        _FMT="${_m}m${_s}s"
    else
        _FMT="${_s}s"
    fi
}

# Overwrites the current terminal line with a colored progress bar + ETA.
# Usage: show_progress <current> <total> <start_epoch>
show_progress() {
    _cur=$1; _tot=$2; _t0=$3
    _now=$(date +%s); _el=$((_now - _t0))
    _pct=$((_cur * 100 / _tot))
    _filled=$((_cur * BAR_WIDTH / _tot))
    _empty=$((BAR_WIDTH - _filled))
    if [ "$_cur" -gt 0 ]; then
        fmt $(( _el * (_tot - _cur) / _cur )); _eta="$_FMT"
    else
        _eta="--"
    fi
    fmt "$_el"; _el_str="$_FMT"
    _bar_f=""; _bar_e=""; _j=0
    while [ "$_j" -lt "$_filled" ]; do _bar_f="${_bar_f}█"; _j=$((_j + 1)); done
    _j=0
    while [ "$_j" -lt "$_empty" ]; do _bar_e="${_bar_e}░"; _j=$((_j + 1)); done
    printf "\r  ${GREEN}%s${DIM}%s${RST} ${BOLD}%3d%%${RST}  ${DIM}%d/%d${RST}  ${CYAN}⏱ %-8s${RST}  ${YELLOW}⏳ %-8s${RST}" \
        "$_bar_f" "$_bar_e" "$_pct" "$_cur" "$_tot" "$_el_str" "$_eta"
}

# Clears the progress line and prints phase completion time.
end_phase() {
    _now=$(date +%s); fmt $((_now - $1))
    printf "\r%80s\r" ""
    ok "Done in ${BOLD}$_FMT${RST}"
}

# ── Banner ───────────────────────────────────────────────

GLOBAL_START=$(date +%s)

echo ""
printf "  ${BOLD}${GREEN}⚡ EnergyTracer${RST} ${DIM}— Experiment Runner${RST}\n"
printf "  ${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}\n"
echo ""
printf "  ${BOLD}Machine${RST}      ${GREEN}%s${RST}\n" "$MACHINE"
printf "  ${BOLD}Mode${RST}         %s\n" "$([ "$IS_SSH" = "1" ] && printf "${CYAN}SSH (tmux)${RST}" || printf "${MAGENTA}Local${RST}")"
printf "  ${BOLD}Profilers${RST}    ${CYAN}%s${RST}\n" "$PROFILERS"
printf "  ${BOLD}Warm-up${RST}      %d runs × %d profiler(s) ${DIM}(n=%d)${RST}\n" "$WARMUP_RUNS" "$NUM_PROFILERS" "$WARMUP_N"
printf "  ${BOLD}Measurement${RST}  %d runs × %d profiler(s) ${DIM}(n=%d)${RST}\n" "$MEASURE_RUNS" "$NUM_PROFILERS" "$MEASURE_N"
printf "  ${BOLD}Cooldown${RST}     %ds between measurements\n" "$COOLDOWN"
echo ""
warn "Do not interrupt — results may be incomplete."
if [ "$IS_SSH" = "1" ]; then
    info "SSH mode: caffeinate active (PID ${CAFFEINATE_PID}), sudo NOPASSWD in place."
fi

# ── Phase 1/3: Warm-up ──────────────────────────────────

echo ""
printf "  ${BOLD}${BLUE}▸ Phase 1/3: Warm-up${RST}\n"
echo ""

W_TOTAL=$((WARMUP_RUNS * NUM_PROFILERS))
T0=$(date +%s)
_w_done=0

for i in $(seq 1 $WARMUP_RUNS); do
    for _p in $PROFILERS; do
        uv run ET -p "$_p" -n "$WARMUP_N" -o "warmup-$i" --shuffle >/dev/null 2>&1
        _w_done=$((_w_done + 1))
        show_progress "$_w_done" "$W_TOTAL" "$T0"
    done
done

end_phase "$T0"

# Discard warm-up results.
# sudo is required in SSH mode because powermetrics (run as root) may
# have created files owned by root inside the output directory.
if [ -d "$OUTPUT_DIR" ]; then
    if [ "$IS_SSH" = "1" ]; then
        sudo rm -rf "$OUTPUT_DIR"
    else
        rm -rf "$OUTPUT_DIR"
    fi
fi
dim "Warm-up results discarded."

# ── Phase 2/3: Measurement ──────────────────────────────

echo ""
printf "  ${BOLD}${BLUE}▸ Phase 2/3: Measurement${RST}\n"
echo ""

M_TOTAL=$((MEASURE_RUNS * NUM_PROFILERS))
T0=$(date +%s)
_m_done=0

for i in $(seq 1 $MEASURE_RUNS); do
    for _p in $PROFILERS; do
        sleep "$COOLDOWN"
        uv run ET -p "$_p" -n "$MEASURE_N" -o "measure-$i" --shuffle >/dev/null 2>&1
        _m_done=$((_m_done + 1))
        show_progress "$_m_done" "$M_TOTAL" "$T0"
    done
done

end_phase "$T0"

# ── Phase 3/3: Analysis ──────────────────────────────────

echo ""
printf "  ${BOLD}${BLUE}▸ Phase 3/3: Analysis${RST}\n"
echo ""

uv run ET-analyzer -p "$OUTPUT_DIR" -v

# ── Summary ──────────────────────────────────────────────

GLOBAL_END=$(date +%s)
fmt $((GLOBAL_END - GLOBAL_START))

echo ""
printf "  ${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}\n"
printf "  ${BOLD}${GREEN}✔ Experiment complete${RST}\n"
printf "  ${BOLD}Total time${RST}   ${CYAN}%s${RST}\n" "$_FMT"
printf "  ${BOLD}Measurements${RST} ${GREEN}%s/${RST}\n" "$OUTPUT_DIR"
printf "  ${BOLD}Reports${RST}      ${GREEN}results/${RST}\n"
echo ""
