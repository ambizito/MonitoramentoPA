@echo off
chcp 65001 >nul

REM Define o caminho para o executável e o diretório de trabalho
set EXECUTABLE_PATH="C:\Users\AndreAzevedo\Source\Repos\ProcessoAgil\ProcessoAgil.Logins\bin\Debug\ProcessoAgil.Logins.exe"
set WORKING_DIR="C:\Users\AndreAzevedo\Source\Repos\ProcessoAgil\ProcessoAgil.Logins\bin\Debug"

if not exist %EXECUTABLE_PATH% (
    echo ERRO: O arquivo ProcessoAgil.Logins.exe não foi encontrado no caminho especificado.
    exit /b
)

REM Verifica se o arquivo de tokens foi fornecido como argumento
if "%~1"=="" (
    echo ERRO: Nenhum arquivo de tokens especificado.
    echo Uso: executar_tokens.bat caminho\para\tokens.txt
    exit /b
)

set TOKENS_FILE=%~1

if not exist "%TOKENS_FILE%" (
    echo ERRO: O arquivo %TOKENS_FILE% não foi encontrado.
    exit /b
)

REM Muda o diretório para o diretório de trabalho necessário
cd /d %WORKING_DIR%

echo Iniciando o processamento dos tokens do arquivo %TOKENS_FILE%...

for /F "usebackq delims=" %%i in ("%TOKENS_FILE%") do (
    echo Executando token_id %%i...
    "%EXECUTABLE_PATH%" -id %%i --rodar
    if errorlevel 1 (
        echo ERRO ao executar o token_id %%i.
    ) else (
        echo Token_id %%i concluído com sucesso.
    )
)
echo Todos os tokens foram processados.
