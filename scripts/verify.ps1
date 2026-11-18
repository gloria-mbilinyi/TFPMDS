$ErrorActionPreference = 'Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    & .\.venv\Scripts\python.exe -m pytest backend\tests -q --junitxml=docs\evidence\backend-junit.xml
    if ($LASTEXITCODE -ne 0) { throw 'Backend tests failed.' }
    Push-Location frontend
    try {
        npm test -- --reporter=default --reporter=junit --outputFile=../docs/evidence/frontend-junit.xml
        if ($LASTEXITCODE -ne 0) { throw 'Frontend tests failed.' }
        npm run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
        npm run typecheck:e2e
        if ($LASTEXITCODE -ne 0) { throw 'Playwright harness typecheck failed.' }
    } finally { Pop-Location }
    & .\.venv\Scripts\python.exe scripts\validate_uml.py
    if ($LASTEXITCODE -ne 0) { throw 'UML validation failed.' }
} finally { Pop-Location }
