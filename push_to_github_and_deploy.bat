@echo off
chcp 65001 >nul
title POS Tea - One-Click Push to GitHub & Deploy to Vercel
color 0A

echo ===============================================================================
echo   🚀 កម្មវិធីស្វ័យប្រវត្តិ៖ រុញកូដទៅ GitHub និង Deploy ទៅកាន់ Vercel.com
echo   ☕ Boba & Beverage POS System - Auto Deploy Tool
echo ===============================================================================
echo.

:: 1. ពិនិត្យមើល Git
where git >nul 2>nul
if %errorlevel% neq 0 (
    color 0C
    echo [កំហុស] រកមិនឃើញកម្មវិធី Git ក្នុងកុំព្យូទ័រនេះទេ!
    echo សូមដំឡើង Git ជាមុនសិន: https://git-scm.com/
    echo.
    pause
    exit /b
)

:: 2. ពិនិត្យមើលថាតើមាន Git Repository ឬនៅ
if not exist ".git" (
    echo [*] កំពុងបង្កើត Git Repository ថ្មី (git init)...
    git init -b main
    echo.
)

:: 3. ពិនិត្យមើល Remote Origin
git remote get-url origin >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] មិនទាន់មាន Link GitHub Repository នៅឡើយទេ។
    set /p REPO_URL="សូម Paste Link GitHub Repo របស់អ្នក (ឧ. https://github.com/username/repo.git): "
    if defined REPO_URL (
        git remote add origin %REPO_URL%
        echo [+] បានភ្ជាប់ទៅកាន់: %REPO_URL%
    ) else (
        echo [កំហុស] អ្នកមិនបានបញ្ចូល Link GitHub ទេ!
        pause
        exit /b
    )
    echo.
)

:: 4. បញ្ចូលសារ Commit (Message)
echo -------------------------------------------------------------------------------
echo [*] កំពុងរៀបចំ File ទាំងអស់ដើម្បី Push...
echo.
set /p USER_MSG="សូមវាយអត្ថន័យនៃការ Update (ឬចុច Enter យកលំនាំដើម): "

if "%USER_MSG%"=="" (
    set USER_MSG=Update POS Tea System - %date% %time%
)

echo.
echo [*] កំពុង Add Files (git add .)...
git add .

echo [*] កំពុងបង្កើត Commit: "%USER_MSG%"...
git commit -m "%USER_MSG%"

echo.
echo [*] កំពុង Push ឡើងទៅកាន់ GitHub (Branch: main)...
git branch -M main
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ===============================================================================
    echo   🎉 ជោគជ័យ! (SUCCESS)
    echo   -------------------------------------------------------------------------
    echo   ✅ កូដត្រូវបាន Push ទៅកាន់ GitHub រួចរាល់ដោយជោគជ័យ!
    echo   🚀 Vercel នឹងចាប់ផ្ដើម Deploy ដោយស្វ័យប្រវត្តិក្នុងរយៈពេលប្រហែល ១ នាទី។
    echo.
    echo   🌐 ពិនិត្យមើលវេបសាយផ្ទាល់: https://pos-six-murex.vercel.app
    echo   📊 ពិនិត្យមើល Vercel Dashboard: https://vercel.com/
    echo ===============================================================================
) else (
    color 0C
    echo.
    echo ===============================================================================
    echo   ⚠️ ការ Push មិនទាន់បានសម្រេច! (PUSH FAILED)
    echo   -------------------------------------------------------------------------
    echo   ប្រសិនបើទើបតែភ្ជាប់ដំបូង សូមពិនិត្យមើលថាអ្នកបាន Login GitHub រួចរាល់ហើយឬនៅ
    echo   ឬសាកល្បងម្ដងទៀតដោយរើសកែ Link Remote GitHub ឱ្យបានត្រឹមត្រូវ។
    echo ===============================================================================
)

echo.
echo ចុចប៊ូតុងណាមួយដើម្បីបិទផ្ទាំងនេះ...
pause >nul
