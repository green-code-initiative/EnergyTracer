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
    printf "  ${BOLD}Usage:${RST} $0 ${CYAN}<machine>${RST}\n"
    echo ""
    printf "  ${BOLD}Supported machines:${RST}\n"
    printf "    ${GREEN}mac${RST}       CodeCarbon + mac-silicon (zeus_apple_silicon)\n"
    printf "    ${DIM}# x86     CodeCarbon + pyRAPL      (coming soon)${RST}\n"
    printf "    ${DIM}# arm     CodeCarbon + TBD         (coming soon)${RST}\n"
    echo ""
    printf "  ${BOLD}Example:${RST} $0 mac\n"
    echo ""
    exit 1
}

# Map machine name -> architecture-specific profiler.
# Each iteration always runs both 'carbon' (cross-platform) and an
# architecture-specific profiler selected here.
#
# To add a new machine:
#   1. Add a line:   <name>)  ARCH_PROFILER="<profiler-id>" ;;
#      where <profiler-id> matches a --profiler value accepted by ET
#      (see src/utilities/parser.py for the list of choices).
#   2. Uncomment / add the entry in usage() above.
case "$1" in
    mac)  ARCH_PROFILER="mac-silicon" ;;
    # x86)  ARCH_PROFILER="x86" ;;   # TODO: implement pyRAPL profiler
    # arm)  ARCH_PROFILER="arm" ;;   # TODO: implement ARM profiler
    "")   error "Machine argument is required."; usage ;;
    *)    error "Unknown machine '${BOLD}$1${RST}'."; usage ;;
esac

MACHINE="$1"

# ── Configuration ────────────────────────────────────────

BAR_WIDTH=30

WARMUP_RUNS=10          # Number of warm-up iterations
WARMUP_N=500            # Code iterations per warm-up run

MEASURE_RUNS=30         # Number of measurement iterations
MEASURE_N=1000          # Code iterations per measurement run
COOLDOWN=60             # Sleep duration (seconds) between measurements

OUTPUT_DIR="output"

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
    _bar=""; _j=0
    while [ "$_j" -lt "$_filled" ]; do _bar="${_bar}█"; _j=$((_j + 1)); done
    _j=0
    while [ "$_j" -lt "$_empty" ]; do _bar="${_bar}░"; _j=$((_j + 1)); done
    if [ "$_cur" -gt 0 ]; then
        fmt $(( _el * (_tot - _cur) / _cur )); _eta="$_FMT"
    else
        _eta="--"
    fi
    fmt "$_el"; _el_str="$_FMT"
    # Color the bar green for filled, dim for empty.
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

# ── Sudo keep-alive ──────────────────────────────────────
# Ask for sudo upfront and refresh the timestamp every 240 s
# in the background so it never expires during the experiment.

sudo -v || { error "sudo is required for powermetrics."; exit 1; }
(while kill -0 $$ 2>/dev/null; do sudo -n true; sleep 240; done) &
SUDO_KEEPALIVE_PID=$!
trap 'kill $SUDO_KEEPALIVE_PID 2>/dev/null' EXIT

GLOBAL_START=$(date +%s)

echo ""
printf "  ${BOLD}${GREEN}⚡ EnergyTracer${RST} ${DIM}— Experiment Runner${RST}\n"
printf "  ${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}\n"
echo ""
printf "  ${BOLD}Machine${RST}      ${GREEN}%s${RST}\n" "$MACHINE"
printf "  ${BOLD}Profilers${RST}    ${CYAN}carbon${RST} + ${CYAN}%s${RST}\n" "$ARCH_PROFILER"
printf "  ${BOLD}Warm-up${RST}      %d runs × 2 profilers ${DIM}(n=%d)${RST}\n" "$WARMUP_RUNS" "$WARMUP_N"
printf "  ${BOLD}Measurement${RST}  %d runs × 2 profilers ${DIM}(n=%d)${RST}\n" "$MEASURE_RUNS" "$MEASURE_N"
printf "  ${BOLD}Cooldown${RST}     %ds between measurements\n" "$COOLDOWN"
echo ""
warn "Do not interrupt — results may be incomplete."

# ── Phase 1/2: Warm-up ──────────────────────────────────

echo ""
printf "  ${BOLD}${BLUE}▸ Phase 1/2: Warm-up${RST}\n"
echo ""

W_TOTAL=$((WARMUP_RUNS * 2))
T0=$(date +%s)

for i in $(seq 1 $WARMUP_RUNS); do
    uv run ET -p carbon -n "$WARMUP_N" -o "warmup-$i" --shuffle >/dev/null 2>&1
    show_progress $((i * 2 - 1)) "$W_TOTAL" "$T0"

    uv run ET -p "$ARCH_PROFILER" -n "$WARMUP_N" -o "warmup-$i" --shuffle >/dev/null 2>&1
    show_progress $((i * 2)) "$W_TOTAL" "$T0"
done

end_phase "$T0"

# Discard warm-up results.
[ -d "$OUTPUT_DIR" ] && rm -rf "$OUTPUT_DIR"
dim "Warm-up results discarded."

# ── Phase 2/2: Measurement ──────────────────────────────

echo ""
printf "  ${BOLD}${BLUE}▸ Phase 2/2: Measurement${RST}\n"
echo ""

M_TOTAL=$((MEASURE_RUNS * 2))
T0=$(date +%s)

for i in $(seq 1 $MEASURE_RUNS); do
    sleep "$COOLDOWN"
    uv run ET -p carbon -n "$MEASURE_N" -o "measure-$i" --shuffle >/dev/null 2>&1
    show_progress $((i * 2 - 1)) "$M_TOTAL" "$T0"

    sleep "$COOLDOWN"
    uv run ET -p "$ARCH_PROFILER" -n "$MEASURE_N" -o "measure-$i" --shuffle >/dev/null 2>&1
    show_progress $((i * 2)) "$M_TOTAL" "$T0"
done

end_phase "$T0"

# ── Summary ──────────────────────────────────────────────

GLOBAL_END=$(date +%s)
fmt $((GLOBAL_END - GLOBAL_START))

echo ""
printf "  ${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RST}\n"
printf "  ${BOLD}${GREEN}✔ Experiment complete${RST}\n"
printf "  ${BOLD}Total time${RST}   ${CYAN}%s${RST}\n" "$_FMT"
printf "  ${BOLD}Results${RST}      ${GREEN}%s/${RST}\n" "$OUTPUT_DIR"
echo ""