@echo off
title Push CloudSync Platform to GitHub
echo ======================================================================
echo           Pushing CloudSync Multi-Cloud DR Platform to GitHub
echo ======================================================================
echo.

git init
git branch -M main
git config user.name "divyakumari1107"
git config user.email "divyakumari1107@users.noreply.github.com"

git remote remove origin 2>nul
git remote add origin https://github.com/divyakumari1107/CloudSync-Platform.git

echo.
echo Adding files to Git staging...
git add .

echo.
echo Committing files...
git commit -m "feat: complete multi-cloud disaster recovery platform spanning AWS, Azure, Terraform, Ansible & Nginx"

echo.
echo Pushing to GitHub (https://github.com/divyakumari1107/CloudSync-Platform.git)...
git push -u origin main

echo.
echo ======================================================================
echo Done! If prompted, authenticate with your GitHub credentials or PAT.
echo ======================================================================
pause
