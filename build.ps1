#!/usr/bin/env pwsh

Write-Host "Building PantryCopilot for deployment..." -ForegroundColor Green

# Build frontend
Write-Host "Building frontend..." -ForegroundColor Yellow
Set-Location frontend
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Frontend build failed!" -ForegroundColor Red
    exit 1
}

# Copy static files to backend
Write-Host "Copying static files to backend..." -ForegroundColor Yellow
Set-Location ..
Remove-Item -Path "backend\static" -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item -Path "frontend\out" -Destination "backend\static" -Recurse

Write-Host "Build complete! Static files copied to backend/static" -ForegroundColor Green