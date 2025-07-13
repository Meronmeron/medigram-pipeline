@echo off
REM Ethiopian Medical Business Data Platform Setup Script for Windows
REM This script helps you set up the project quickly

echo 🚀 Setting up Ethiopian Medical Business Data Platform...

REM Check if Docker is installed
echo [INFO] Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

echo [SUCCESS] Docker and Docker Compose are installed

REM Check if Python is installed
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Python is not installed. This is optional for local development.
) else (
    echo [SUCCESS] Python is installed
)

REM Create necessary directories
echo [INFO] Creating project directories...

mkdir data\raw 2>nul
mkdir data\processed 2>nul
mkdir models 2>nul
mkdir logs 2>nul
mkdir dbt\models 2>nul
mkdir dbt\macros 2>nul
mkdir dbt\profiles 2>nul
mkdir scripts 2>nul
mkdir tests 2>nul
mkdir app\api 2>nul
mkdir app\core 2>nul
mkdir app\models 2>nul
mkdir app\services 2>nul
mkdir app\utils 2>nul

echo [SUCCESS] All directories created

REM Setup environment file
echo [INFO] Setting up environment configuration...

if exist .env (
    echo [WARNING] .env file already exists. Skipping environment setup.
) else (
    if exist env.template (
        copy env.template .env >nul
        echo [SUCCESS] Created .env file from template
        echo [WARNING] Please edit .env file with your actual configuration values
    ) else (
        echo [ERROR] env.template file not found. Please create .env file manually.
    )
)

REM Create initial configuration files
echo [INFO] Creating initial configuration files...

REM Create dbt profiles.yml
if not exist dbt\profiles\profiles.yml (
    (
        echo ethiopian_medical:
        echo   target: dev
        echo   outputs:
        echo     dev:
        echo       type: postgres
        echo       host: localhost
        echo       port: 5432
        echo       user: "{{ env_var('POSTGRES_USER') }}"
        echo       pass: "{{ env_var('POSTGRES_PASSWORD') }}"
        echo       dbname: "{{ env_var('POSTGRES_DB') }}"
        echo       schema: public
        echo       threads: 4
        echo       keepalives_idle: 0
        echo       search_path: public
        echo       role: null
        echo       sslmode: prefer
        echo     prod:
        echo       type: postgres
        echo       host: "{{ env_var('POSTGRES_HOST') }}"
        echo       port: 5432
        echo       user: "{{ env_var('POSTGRES_USER') }}"
        echo       pass: "{{ env_var('POSTGRES_PASSWORD') }}"
        echo       dbname: "{{ env_var('POSTGRES_DB') }}"
        echo       schema: public
        echo       threads: 4
        echo       keepalives_idle: 0
        echo       search_path: public
        echo       role: null
        echo       sslmode: require
    ) > dbt\profiles\profiles.yml
    echo [SUCCESS] Created dbt profiles.yml
)

REM Create dbt_project.yml
if not exist dbt\dbt_project.yml (
    (
        echo name: 'ethiopian_medical'
        echo version: '1.0.0'
        echo config-version: 2
        echo.
        echo profile: 'ethiopian_medical'
        echo.
        echo model-paths: ["models"]
        echo analysis-paths: ["analyses"]
        echo test-paths: ["tests"]
        echo seed-paths: ["seeds"]
        echo macro-paths: ["macros"]
        echo snapshot-paths: ["snapshots"]
        echo.
        echo target-path: "target"
        echo clean-targets:
        echo   - "target"
        echo   - "dbt_packages"
        echo.
        echo models:
        echo   ethiopian_medical:
        echo     staging:
        echo       +materialized: view
        echo     marts:
        echo       +materialized: table
    ) > dbt\dbt_project.yml
    echo [SUCCESS] Created dbt_project.yml
)

REM Test Docker setup
echo [INFO] Testing Docker setup...
docker-compose config >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose configuration has errors
    pause
    exit /b 1
) else (
    echo [SUCCESS] Docker Compose configuration is valid
)

REM Display next steps
echo.
echo 🎉 Setup completed successfully!
echo.
echo 📋 Next steps:
echo 1. Edit .env file with your actual configuration:
echo    - TELEGRAM_API_ID
echo    - TELEGRAM_API_HASH
echo    - TELEGRAM_BOT_TOKEN
echo    - SECRET_KEY
echo    - JWT_SECRET_KEY
echo.
echo 2. Start the platform:
echo    docker-compose up -d
echo.
echo 3. Access the services:
echo    - FastAPI: http://localhost:8000
echo    - Dagster: http://localhost:3000
echo    - PostgreSQL: localhost:5432
echo.
echo 4. Check the logs:
echo    docker-compose logs -f
echo.
echo 📚 For more information, see README.md
echo.
pause 