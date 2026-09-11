@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================================
REM PROYECTO ORION - FLUJO COMPLETO AUTOMATICO (Windows)
REM ============================================================
REM Este script ejecuta todo el flujo de Orion con un solo clic:
REM   1. Activa el entorno virtual
REM   2. Configura encoding UTF-8
REM   3. Pregunta el modo de ejecucion
REM   4. Ejecuta el flujo seleccionado
REM   5. Opcionalmente abre el dashboard
REM ============================================================

title Orion - Flujo Completo

echo.
echo ============================================================
echo   ORION - SISTEMA DE DETECCION DE HURTO DE ENERGIA
echo ============================================================
echo.

REM ============================================================
REM 1. VERIFICAR QUE ESTAMOS EN LA CARPETA CORRECTA
REM ============================================================

if not exist "scripts\ejecutar_flujo_completo.py" (
    echo [ERROR] No se encuentra el proyecto Orion en esta carpeta.
    echo.
    echo Asegurate de ejecutar este script desde la raiz del proyecto.
    echo Carpeta actual: %CD%
    echo.
    pause
    exit /b 1
)

echo [OK] Proyecto encontrado en: %CD%
echo.

REM ============================================================
REM 2. VERIFICAR QUE EL ENTORNO VIRTUAL EXISTE
REM ============================================================

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] No se encuentra el entorno virtual .venv
    echo.
    echo Crea el entorno virtual primero:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [OK] Entorno virtual encontrado
echo.

REM ============================================================
REM 3. ACTIVAR ENTORNO VIRTUAL
REM ============================================================

echo Activando entorno virtual...
call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo [ERROR] No se pudo activar el entorno virtual
    pause
    exit /b 1
)

echo [OK] Entorno virtual activado
echo.

REM ============================================================
REM 4. CONFIGURAR ENCODING UTF-8
REM ============================================================

set PYTHONIOENCODING=utf-8
set LANG=C.UTF-8
set LC_ALL=C.UTF-8

echo [OK] Encoding configurado a UTF-8
echo.

REM ============================================================
REM 5. MENU DE OPCIONES
REM ============================================================

echo ============================================================
echo   SELECCIONA EL MODO DE EJECUCION
echo ============================================================
echo.
echo   [1] Flujo completo (limpiar + generar + procesar + entrenar)
echo   [2] Solo ejecutar flujo completo (sin limpiar)
echo   [3] Solo ejecutar tuberia diaria
echo   [4] Solo ejecutar bucle cerrado
echo   [5] Solo procesar cola de datos
echo   [6] Solo crear datos de entrenamiento
echo   [7] Ver dashboard (solo ver, sin ejecutar flujo)
echo   [8] Limpiar sistema
echo   [0] Salir
echo.

set /p opcion="Ingresa una opcion (0-8): "

echo.

REM ============================================================
REM 6. EJECUTAR SEGUN OPCION
REM ============================================================

if "%opcion%"=="0" goto :salir
if "%opcion%"=="1" goto :flujo_limpio
if "%opcion%"=="2" goto :flujo_completo
if "%opcion%"=="3" goto :tuberia
if "%opcion%"=="4" goto :bucle
if "%opcion%"=="5" goto :cola
if "%opcion%"=="6" goto :entrenamiento
if "%opcion%"=="7" goto :dashboard
if "%opcion%"=="8" goto :limpiar

echo [ERROR] Opcion no valida
goto :menu

REM ============================================================
REM OPCION 1: FLUJO COMPLETO CON LIMPIEZA
REM ============================================================

:flujo_limpio
echo ============================================================
echo   EJECUTANDO: Limpiar + Flujo completo
echo ============================================================
echo.
echo ADVERTENCIA: Se eliminaran todos los datos procesados y brutos.
set /p confirmar="Estas seguro? (s/n): "
if /i not "%confirmar%"=="s" goto :menu

echo.
echo [PASO 1/2] Limpiando sistema...
python scripts\limpiar_sistema.py
if errorlevel 1 (
    echo [ERROR] Fallo la limpieza
    pause
    goto :menu
)

echo.
echo [PASO 2/2] Ejecutando flujo completo...
python scripts\ejecutar_flujo_completo.py
if errorlevel 1 (
    echo [ERROR] Fallo el flujo completo
    pause
    goto :menu
)

echo.
echo [OK] Flujo completado exitosamente
goto :preguntar_dashboard

REM ============================================================
REM OPCION 2: FLUJO COMPLETO SIN LIMPIEZA
REM ============================================================

:flujo_completo
echo ============================================================
echo   EJECUTANDO: Flujo completo
echo ============================================================
echo.
python scripts\ejecutar_flujo_completo.py
if errorlevel 1 (
    echo [ERROR] Fallo el flujo completo
    pause
    goto :menu
)

echo.
echo [OK] Flujo completado exitosamente
goto :preguntar_dashboard

REM ============================================================
REM OPCION 3: TUBERIA DIARIA
REM ============================================================

:tuberia
echo ============================================================
echo   EJECUTANDO: Tuberia diaria
echo ============================================================
echo.
python scripts\ejecutar_tuberia_diaria.py
if errorlevel 1 (
    echo [ERROR] Fallo la tuberia diaria
    pause
    goto :menu
)

echo.
echo [OK] Tuberia diaria completada
goto :preguntar_dashboard

REM ============================================================
REM OPCION 4: BUCLE CERRADO
REM ============================================================

:bucle
echo ============================================================
echo   EJECUTANDO: Bucle cerrado
echo ============================================================
echo.
python scripts\ejecutar_bucle_cerrado.py
if errorlevel 1 (
    echo [ERROR] Fallo el bucle cerrado
    pause
    goto :menu
)

echo.
echo [OK] Bucle cerrado completado
goto :preguntar_dashboard

REM ============================================================
REM OPCION 5: PROCESAR COLA
REM ============================================================

:cola
echo ============================================================
echo   EJECUTANDO: Procesar cola de datos
echo ============================================================
echo.
python scripts\procesar_cola_datos.py --procesar
if errorlevel 1 (
    echo [ERROR] Fallo el procesamiento de la cola
    pause
    goto :menu
)

echo.
echo [OK] Cola procesada exitosamente
goto :preguntar_dashboard

REM ============================================================
REM OPCION 6: CREAR DATOS DE ENTRENAMIENTO
REM ============================================================

:entrenamiento
echo ============================================================
echo   EJECUTANDO: Crear datos de entrenamiento
echo ============================================================
echo.
python scripts\crear_datos_entrenamiento.py
if errorlevel 1 (
    echo [ERROR] Fallo la creacion de datos
    pause
    goto :menu
)

echo.
echo [OK] Datos de entrenamiento creados
goto :preguntar_dashboard

REM ============================================================
REM OPCION 7: DASHBOARD
REM ============================================================

:dashboard
echo ============================================================
echo   EJECUTANDO: Dashboard
echo ============================================================
echo.
echo Iniciando dashboard de Orion...
echo.
echo Se abrira en tu navegador: http://localhost:8501
echo.
echo Para detener el dashboard: presiona Ctrl + C
echo.
streamlit run scripts\tablero_orion.py
goto :menu

REM ============================================================
REM OPCION 8: LIMPIAR SISTEMA
REM ============================================================

:limpiar
echo ============================================================
echo   EJECUTANDO: Limpiar sistema
echo ============================================================
echo.
echo ADVERTENCIA: Se eliminaran todos los datos procesados.
python scripts\limpiar_sistema.py
if errorlevel 1 (
    echo [ERROR] Fallo la limpieza
    pause
    goto :menu
)

echo.
echo [OK] Sistema limpiado
goto :menu

REM ============================================================
REM PREGUNTAR SI ABRIR DASHBOARD
REM ============================================================

:preguntar_dashboard
echo.
echo ============================================================
set /p ver_dashboard="Deseas abrir el dashboard? (s/n): "
if /i "%ver_dashboard%"=="s" goto :dashboard

echo.
pause
exit /b 0

REM ============================================================
REM SALIR
REM ============================================================

:salir
echo.
echo Saliendo de Orion...
echo.
exit /b 0