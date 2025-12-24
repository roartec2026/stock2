@echo off
setlocal enabledelayedexpansion
REM Batch file to push the whole project to git repository
REM This script adds all changes, commits, and pushes to remote

echo ============================================================
echo Git Push Script - ROARSTAR Project
echo ============================================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH!
    echo Please install Git from https://git-scm.com/
    pause
    exit /b 1
)

echo Git found!
echo.

REM Check if we're in a git repository
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
    echo ERROR: Not a git repository!
    echo Please initialize git first: git init
    pause
    exit /b 1
)

for /f "tokens=*" %%b in ('git branch --show-current') do set branch_name=%%b
echo Current branch: !branch_name!
echo.

REM Show status
echo Checking repository status...
git status --short
echo.

REM Add all changes
echo Adding all changes to staging...
git add .
if errorlevel 1 (
    echo ERROR: Failed to add files!
    pause
    exit /b 1
)

echo Files added successfully!
echo.

REM Check if there are changes to commit
git diff --cached --quiet
if errorlevel 1 (
    REM There are changes to commit
    echo Changes detected. Enter commit message:
    echo (Leave empty to use default message)
    set /p commit_msg="Commit message: "
    
    if "!commit_msg!"=="" (
        set commit_msg=Update project files - %date% %time%
    )
    
    echo.
    echo Committing changes with message: "!commit_msg!"
    git commit -m "!commit_msg!"
    if errorlevel 1 (
        echo ERROR: Failed to commit changes!
        pause
        exit /b 1
    )
    
    echo Commit successful!
    echo.
) else (
    echo No changes to commit.
    echo.
)

REM Push to remote
echo Pushing to remote repository (branch: !branch_name!)...
git push origin !branch_name!
if errorlevel 1 (
    echo.
    echo Attempting to set upstream and push...
    git push -u origin !branch_name!
    if errorlevel 1 (
        echo ERROR: Push failed!
        pause
        exit /b 1
    )
)

echo.
echo ============================================================
echo Push completed successfully!
echo ============================================================
echo.
pause

