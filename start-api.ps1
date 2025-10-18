# FastAPI Server Startup Script for PowerShell
# This script activates the virtual environment and starts the FastAPI server

Write-Host "Starting PantryCopilot FastAPI Server..." -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "Error: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "Warning: .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please add your GOOGLE_API_KEY to the .env file" -ForegroundColor Cyan
    exit 1
}

# Check if API key is set
$apiKey = Select-String -Path ".env" -Pattern "GOOGLE_API_KEY=.+" -Quiet
if (-not $apiKey) {
    Write-Host "Warning: GOOGLE_API_KEY not set in .env file!" -ForegroundColor Yellow
    Write-Host "Please add your Google API key to continue" -ForegroundColor Cyan
    Write-Host "Get your key from: https://aistudio.google.com/app/apikey" -ForegroundColor Cyan
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Start the server
Write-Host ""
Write-Host "Starting FastAPI server..." -ForegroundColor Cyan
Write-Host "API will be available at:" -ForegroundColor Green
Write-Host "  - API: http://localhost:8000" -ForegroundColor White
Write-Host "  - Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - ReDoc: http://localhost:8000/redoc" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python main.py
