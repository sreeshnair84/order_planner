@echo off
echo Running manufacturer assignment migration...
cd /d "%~dp0backend"
python scripts/migrate_manufacturer_assignment.py
if %ERRORLEVEL% EQU 0 (
    echo Migration completed successfully!
) else (
    echo Migration failed with error code %ERRORLEVEL%
)
pause
