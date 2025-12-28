@echo off
if "%1"=="" (
    echo Usage: Show_Graph.bat [type]
    echo Types:
    echo   normal - Show graph without SMA
    echo   sma    - Show graph with SMA
    exit /b 1
)

if /i "%1"=="normal" (
    python "TSA_Traveler_Throughput.py" Show_Graph
) else if /i "%1"=="sma" (
    python "TSA_Traveler_Throughput.py" Show_Graph_With_SMA
) else (
    echo Invalid graph type: %1
    echo Valid types are: normal, sma
    exit /b 1
)