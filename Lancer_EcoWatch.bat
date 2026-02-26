@echo off
title EcoWatch Launcher
echo ---------------------------------------------------
echo    DEMARRAGE DE L'ECOSYSTEME ECOWATCH 📈
echo ---------------------------------------------------

:: Lancement du Worker en arrière-plan (nouvelle fenêtre)
echo [1/2] Lancement du Moteur de Scraping (Worker)...
start "EcoWatch Worker" cmd /k "python worker.py"

:: Petite pause pour laisser le worker s'initialiser
timeout /t 3 /nobreak > nul

:: Lancement du Dashboard Streamlit
echo [2/2] Lancement du Dashboard...
start "EcoWatch Dashboard" cmd /k "streamlit run dashboard.py"

echo ---------------------------------------------------
echo    TOUT EST EN LIGNE ! 🚀
echo    Ne fermez pas les fenetres noires qui se sont ouvertes.
echo ---------------------------------------------------
pause
