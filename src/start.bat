@echo off
:: Navigate to the directory where the Python module is located
call C:\ProgramData\anaconda3\Scripts\activate F:\python_env
cd /d F:\imcf_eda
git checkout main
cd /d F:\imcf_eda\src
:: Run the Python file as a module
python -m imcf_eda.run all

echo.
echo Script has finished running. Press any key to exit...
pause