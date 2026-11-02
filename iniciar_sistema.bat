@echo off
title Sistema de Vision Artificial - Inspeccion de Laminas
color 0b

echo =====================================================================
echo    SISTEMA DE VISION ARTIFICIAL INDUSTRIAL - INSPECCION DE LAMINAS
echo =====================================================================
echo.
echo [1/2] Verificando dependencias y entorno Python...
python -c "import cv2, PySide6, numpy, requests; print('>> Entorno verificado exitosamente.')"
if %errorlevel% neq 0 (
    echo [ERROR] Falta alguna dependencia requerida. Instalando paquetes...
    python -m pip install -e .
)

echo [2/2] Iniciando aplicacion de inspeccion...
python src\main.py

echo.
echo Aplicacion finalizada.
pause
