@echo off
title CloudSync Multi-Cloud Disaster Recovery Platform
echo ======================================================================
echo           Starting CloudSync Multi-Cloud DR & Failover Platform
echo ======================================================================
echo.

echo [1/3] Building and starting Multi-Cloud Docker containers...
docker compose up -d --build

echo.
echo [2/3] Waiting for AWS, Azure nodes and Nginx Edge Ingress...
timeout /t 6 /nobreak >nul

echo.
echo [3/3] Opening CloudSync Dashboard in your default browser...
start http://localhost:8070

echo.
echo ======================================================================
echo CloudSync is running at: http://localhost:8070
echo To run automated DR tests: python test_failover.py
echo To view logs: docker compose logs -f
echo To stop: docker compose down
echo ======================================================================
pause
