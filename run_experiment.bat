@echo off
setlocal enabledelayedexpansion

REM ─────────────────────────────────────────────────────────
REM EnergyTracer — Experiment Runner (Windows)
REM ─────────────────────────────────────────────────────────

REM === ANSI color codes (Windows 10+ Terminal) ===
REM Using escape character via prompt trick.
for /f %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
set "RST=%ESC%[0m"
set "BOLD=%ESC%[1m"
set "DIM=%ESC%[2m"
set "RED=%ESC%[31m"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "BLUE=%ESC%[34m"
set "MAGENTA=%ESC%[35m"
set "CYAN=%ESC%[36m"

REM === Configuration ===
REM Windows only supports the cross-platform CodeCarbon profiler.
set PROFILER=carbon
set BAR_WIDTH=30
set WARMUP_RUNS=10
set WARMUP_N=500
set MEASURE_RUNS=30
set MEASURE_N=1000
set COOLDOWN=60
set OUTPUT_DIR=output

call :get_seconds GLOBAL_START

echo.
echo   %BOLD%%GREEN%# EnergyTracer%RST% %DIM%- Experiment Runner (Windows)%RST%
echo   %DIM%------------------------------------------------%RST%
echo.
echo   %BOLD%Profiler%RST%     %CYAN%carbon%RST% (CodeCarbon)
echo   %BOLD%Warm-up%RST%      %WARMUP_RUNS% runs %DIM%(n=%WARMUP_N%)%RST%
echo   %BOLD%Measurement%RST%  %MEASURE_RUNS% runs %DIM%(n=%MEASURE_N%)%RST%
echo   %BOLD%Cooldown%RST%     %COOLDOWN%s between measurements
echo.
echo   %YELLOW%!%RST%  Do not interrupt - results may be incomplete.

REM === Phase 1/3: Warm-up ===

echo.
echo   %BOLD%%BLUE%^> Phase 1/3: Warm-up%RST%
echo.

call :get_seconds T0

set /a "W_TOTAL=%WARMUP_RUNS%"
for /L %%i in (1,1,%WARMUP_RUNS%) do (
    uv run ET -p %PROFILER% -n %WARMUP_N% -o warmup-%%i --shuffle >nul 2>&1
    call :show_progress %%i !W_TOTAL! !T0!
)

call :end_phase !T0!

if exist "%OUTPUT_DIR%\" rmdir /s /q "%OUTPUT_DIR%"
echo   %DIM%Warm-up results discarded.%RST%

REM === Phase 2/3: Measurement ===

echo.
echo   %BOLD%%BLUE%^> Phase 2/3: Measurement%RST%
echo.

call :get_seconds T0

set /a "M_TOTAL=%MEASURE_RUNS%"
for /L %%i in (1,1,%MEASURE_RUNS%) do (
    timeout /t %COOLDOWN% /nobreak >nul
    uv run ET -p %PROFILER% -n %MEASURE_N% -o measure-%%i --shuffle >nul 2>&1
    call :show_progress %%i !M_TOTAL! !T0!
)

call :end_phase !T0!

REM === Phase 3/3: Analysis ===

echo.
echo   %BOLD%%BLUE%^> Phase 3/3: Analysis%RST%
echo.

uv run ET-analyzer -p %OUTPUT_DIR% -v

REM === Summary ===

call :get_seconds GLOBAL_END
set /a "_total=!GLOBAL_END! - !GLOBAL_START!"
call :fmt_duration !_total! TOTAL_STR

echo.
echo   %DIM%------------------------------------------------%RST%
echo   %BOLD%%GREEN%v Experiment complete%RST%
echo   %BOLD%Total time%RST%     %CYAN%!TOTAL_STR!%RST%
echo   %BOLD%Measurements%RST%   %GREEN%'%OUTPUT_DIR%\'%RST%
echo   %BOLD%Reports%RST%        %GREEN%'results\'%RST%
echo.

endlocal
exit /b 0

REM ============================================================
REM Subroutines
REM ============================================================

:get_seconds
REM Stores seconds since midnight in variable named %~1.
for /f "tokens=1-3 delims=:.," %%a in ("%time: =0%") do (
    set /a "%~1=(1%%a %% 100) * 3600 + (1%%b %% 100) * 60 + (1%%c %% 100)"
)
exit /b 0

:fmt_duration
REM Formats %~1 seconds into a readable string, stored in %~2.
set /a "_fh=%~1 / 3600"
set /a "_fm=(%~1 %% 3600) / 60"
set /a "_fs=%~1 %% 60"
if !_fh! gtr 0 (
    if !_fm! lss 10 set "_fm=0!_fm!"
    if !_fs! lss 10 set "_fs=0!_fs!"
    set "%~2=!_fh!h!_fm!m!_fs!s"
) else if !_fm! gtr 0 (
    if !_fs! lss 10 set "_fs=0!_fs!"
    set "%~2=!_fm!m!_fs!s"
) else (
    set "%~2=!_fs!s"
)
exit /b 0

:show_progress
REM %~1=current  %~2=total  %~3=start_seconds
call :get_seconds _NOW
set /a "_el=!_NOW! - %~3"
set /a "_pct=%~1 * 100 / %~2"
set /a "_filled=%~1 * %BAR_WIDTH% / %~2"
set /a "_empty=%BAR_WIDTH% - !_filled!"
if %~1 gtr 0 (
    set /a "_rem=!_el! * (%~2 - %~1) / %~1"
) else (
    set "_rem=0"
)
set "_bar="
for /L %%j in (1,1,!_filled!) do set "_bar=!_bar!#"
for /L %%j in (1,1,!_empty!) do set "_bar=!_bar!-"
call :fmt_duration !_el! _EL_STR
call :fmt_duration !_rem! _ETA_STR
echo   %GREEN%!_bar:~0,!_filled!~!%RST%%DIM%!_bar:~!_filled!!%RST%  %BOLD%!_pct!%%%RST%  %DIM%%~1/%~2%RST%  %CYAN%!_EL_STR!%RST%  %YELLOW%~!_ETA_STR!%RST%
exit /b 0

:end_phase
REM %~1=start_seconds
call :get_seconds _END_NOW
set /a "_dur=!_END_NOW! - %~1"
call :fmt_duration !_dur! _DUR_STR
echo.
echo   %GREEN%v%RST%  Done in %BOLD%!_DUR_STR!%RST%
exit /b 0
