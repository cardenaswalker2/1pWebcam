@echo off
title Sistema de Inspeccion Optica - Laminas y Tejas Translucidas
color 0b

echo =====================================================================
echo   SISTEMA DE INSPECCION OPTICA INDUSTRIAL - TEJAS TRANSLUCIDAS
echo =====================================================================
echo.
echo [*] Inicializando modulos de vision artificial y telemetria espectral...
echo [*] Atajo para demostracion tecnica de diagnostico: [Ctrl + X] o tecla [X]
echo.

python demo_transparentes\main.py

echo.
echo Sistema finalizado.
pause
