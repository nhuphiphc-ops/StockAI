@echo off
title AI Stock Dashboard - Khoi dong...
color 0B

echo.
echo  ========================================================
echo    AI STOCK INVESTMENT DASHBOARD
echo  ========================================================
echo.

:: Chuyen vao thu muc du an
cd /d "%~dp0"

:: Mo cong 8000 tren firewall (can quyen Admin - bo qua neu da co)
netsh advfirewall firewall add rule name="AI Stock Dashboard" dir=in action=allow protocol=TCP localport=8000 >nul 2>&1

echo  [*] Dang khoi dong server chia se mang LAN...
start "AI Stock Server" /min cmd /c "python main.py"

echo  [*] Cho server khoi dong (4 giay)...
ping 127.0.0.1 -n 5 >nul

:: Lay IP LAN
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "127.0.0.1" ^| findstr /v "169."') do (
    set LAN_IP=%%a
    goto :found
)
:found
set LAN_IP=%LAN_IP: =%

echo.
echo  ========================================================
echo   DASHBOARD DA KHOI DONG THANH CONG!
echo  ========================================================
echo.
echo   Tren may nay     : http://127.0.0.1:8000
echo   Mang LAN (vo):    http://%LAN_IP%:8000
echo.
echo   Huong dan cho vo:
echo   1. Ket noi cung WiFi nha
echo   2. Mo trinh duyet tren dien thoai
echo   3. Nhap dia chi: http://%LAN_IP%:8000
echo      HOAC quet ma QR tren Desktop
echo.
echo  ========================================================
echo.

:: Mo trinh duyet tren may nay
start "" "http://127.0.0.1:8000"

:: Mo anh QR de vo quet
if exist "%~dp0..\AI_Stock_QR.png" (
    start "" "%~dp0..\AI_Stock_QR.png"
)

ping 127.0.0.1 -n 6 >nul
exit
