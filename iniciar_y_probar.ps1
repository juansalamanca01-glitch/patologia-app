# =====================================================================
# Script de Puesta en Marcha y Prueba de Endpoints - PathoLab
# =====================================================================
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "       INICIALIZANDO PROYECTO PATOLOGIA-APP (PathoLab)     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Ubicar el directorio backend
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$backendDir = Join-Path $scriptDir "backend"

if (-not (Test-Path $backendDir)) {
    # Si ya esta dentro de backend
    if (Test-Path "manage.py") {
        $backendDir = (Get-Location).Path
    } else {
        Write-Host "[ERROR] No se encontro la carpeta 'backend'." -ForegroundColor Red
        exit 1
    }
}

Set-Location $backendDir
Write-Host "[OK] Directorio de trabajo: $backendDir" -ForegroundColor Green

# 2. Verificar Python
try {
    $pyVersion = python --version 2>&1
    Write-Host "[OK] Python detectado: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python no esta instalado o no se encuentra en el PATH." -ForegroundColor Red
    exit 1
}

# 3. Instalar dependencias
Write-Host "`n[1/4] Verificando e instalando librerias necesarias..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
Write-Host "[OK] Dependencias de Python listas." -ForegroundColor Green

# 4. Migraciones de Base de Datos
Write-Host "`n[2/4] Aplicando migraciones de base de datos..." -ForegroundColor Yellow
python manage.py migrate --noinput
Write-Host "[OK] Base de datos actualizada." -ForegroundColor Green

# 5. Cargar datos de prueba (14 patologias + usuarios)
Write-Host "`n[3/4] Creando usuarios de prueba y 14 plantillas medicas..." -ForegroundColor Yellow
python manage.py seed_data

# 6. Iniciar servidor Django si no esta corriendo
Write-Host "`n[4/4] Verificando servidor local en el puerto 8000..." -ForegroundColor Yellow
$portActive = Test-NetConnection -ComputerName 127.0.0.1 -Port 8000 -InformationLevel Quiet

if (-not $portActive) {
    Write-Host "Iniciando servidor Django en nueva ventana..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backendDir'; python manage.py runserver"
    Write-Host "Esperando 5 segundos a que el servidor termine de encender..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
} else {
    Write-Host "[OK] El servidor Django ya se encuentra encendido en http://127.0.0.1:8000" -ForegroundColor Green
}

# 7. Prueba automatica de los Endpoints
Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "          PROBANDO LOS 2 ENDPOINTS EN VIVO                " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

try {
    # Test Endpoint 1: Login
    Write-Host "`n[PROBANDO ENDPOINT 1] POST /api/auth/login/..." -ForegroundColor Yellow
    $loginBody = @{ username = "patologo1"; password = "patologo1234" } | ConvertTo-Json
    $loginResp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login/" -Method Post -Body $loginBody -ContentType "application/json; charset=utf-8"
    
    Write-Host "[STATUS 200 OK] Login exitoso!" -ForegroundColor Green
    Write-Host " - Medico: $($loginResp.user.nombre_completo)" -ForegroundColor White
    Write-Host " - Rol: $($loginResp.user.rol)" -ForegroundColor White
    Write-Host " - Token obtenido: $($loginResp.access.Substring(0, 35))..." -ForegroundColor DarkGray
    
    $token = $loginResp.access
    $headers = @{ Authorization = "Bearer $token" }

    # Test Endpoint 2: Crear Informe
    Write-Host "`n[PROBANDO ENDPOINT 2] POST /api/informes/ (Creacion con texto automatico)..." -ForegroundColor Yellow
    $casoNum = "PAT-TEST-" + (Get-Random -Minimum 1000 -Maximum 9999)
    $informeData = @{
        numero_caso = $casoNum
        patologia = 1
        tipo_muestra = "Biopsia escisional"
        datos_ingresados = @{
            localizacion = "Espalda region escapular derecha"
            tipo_muestra = "Escisional"
            dimensiones = "2.0 x 1.5 x 0.5 cm"
            color = "Pigmentado"
            bordes = "Bien definidos"
            superficie = "Lisa"
            hallazgos_adicionales = "Sin sangrado ni ulceracion"
        }
        notas = "Prueba automatica de validacion"
    } | ConvertTo-Json -Depth 5

    $utf8Bytes = [System.Text.Encoding]::UTF8.GetBytes($informeData)
    $informeResp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/informes/" -Method Post -Body $utf8Bytes -ContentType "application/json; charset=utf-8" -Headers $headers

    Write-Host "[STATUS 201 CREATED] Informe creado exitosamente!" -ForegroundColor Green
    Write-Host " - Caso ID: $($informeResp.id) | Numero: $($informeResp.numero_caso)" -ForegroundColor White
    Write-Host " - Patologia: $($informeResp.patologia_nombre)" -ForegroundColor White
    Write-Host " - Estado: $($informeResp.estado)" -ForegroundColor White
    Write-Host "`n--- TEXTO MACROSCOPICO GENERADO AUTOMATICAMENTE ---" -ForegroundColor Magenta
    Write-Host $informeResp.texto_generado -ForegroundColor White
    Write-Host "---------------------------------------------------" -ForegroundColor Magenta

    Write-Host "`n>>> TODO ESTA FUNCIONANDO PERFECTAMENTE! <<<" -ForegroundColor Green
    Write-Host "Ya puedes abrir Postman o importar PathoLab_API.postman_collection.json" -ForegroundColor Cyan

} catch {
    Write-Host "`n[ERROR AL PROBAR ENDPOINTS]: $($_.Exception.Message)" -ForegroundColor Red
}
