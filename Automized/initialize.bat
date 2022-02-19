set /A start_node_port=5000
set /A nodes=3

set /A initial_node_port = start_node_port 
set /A times = nodes - 1
set /A next_node_port = start_node_port + 1
set /A final = times - 1

@echo OFF
cd ..
start cmd /k python screen.py

setlocal ENABLEDELAYEDEXPANSION
FOR /l %%i IN (0,1,%times%) DO (
    start cmd /k python node.py %%i !start_node_port! !next_node_port!
    set /A start_node_port = next_node_port
    set /A next_node_port = start_node_port + 1
    if %%i == %final% (set /A next_node_port = initial_node_port)
)
endlocal