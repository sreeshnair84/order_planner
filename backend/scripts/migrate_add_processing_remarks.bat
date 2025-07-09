@echo off
echo Adding processing_remarks column to order_sku_items table...
echo.

REM Set environment variables for database connection
REM Update these values according to your database configuration
set DB_HOST=localhost
set DB_PORT=5432
set DB_NAME=order_planner
set DB_USER=postgres
set DB_PASSWORD=your_password_here

echo Database Configuration:
echo Host: %DB_HOST%
echo Port: %DB_PORT%
echo Database: %DB_NAME%
echo User: %DB_USER%
echo.

REM Run the migration script
python "%~dp0add_processing_remarks_column.py"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Migration completed successfully!
    echo The processing_remarks column has been added to the order_sku_items table.
) else (
    echo.
    echo Migration failed! Please check the error messages above.
)

echo.
pause
