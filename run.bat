@echo off
chcp 65001 >nul
title Boba POS System (Development / Local Mode)
color 0B

echo ===============================================================================
echo   🍵 ប្រព័ន្ធគ្រប់គ្រងការលក់តែគុជ និងភេសជ្ជៈ (Boba POS Web Application)
echo   🛠️ របៀបដំណើរការ៖ Development / Local Offline Server (ម៉ាស៊ីនផ្ទាល់)
echo ===============================================================================
echo.
echo [*] កំពុងពិនិត្យ និងដំណើរការម៉ាស៊ីនមេ Flask...
echo.
echo -------------------------------------------------------------------------------
echo   🌐 អាសយដ្ឋានសម្រាប់បើកមើល (URLs):
echo      - បើកលើកុំព្យូទ័រនេះ:       http://localhost:5000  ឬ  http://127.0.0.1:5000
echo      - បើកពីទូរស័ព្ទ/iPad (Wi-Fi): http://192.168.100.14:5000
echo.
echo   🔑 ព័ត៌មានគណនីចូលប្រើ (Demo Accounts):
echo      - 👑 Admin (អ្នកគ្រប់គ្រង):  Username: admin   /  Password: admin123
echo      - ☕ Cashier (អ្នកគិតលុយ): Username: cashier /  Password: 123456
echo -------------------------------------------------------------------------------
echo.
echo [*] ចុចបញ្ឈប់ Server ដោយចុច: Ctrl + C
echo.

:: បើក Web Browser ទៅកាន់ប្រព័ន្ធដោយស្វ័យប្រវត្តិ
start http://127.0.0.1:5000

:: ចាប់ផ្តើមដំណើរការ Flask App
python app.py

echo.
pause
