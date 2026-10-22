@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set REPO=vibe-knowledge-video-skill
echo ==== 发布 %REPO% 到 GitHub ====
echo.

where git >nul 2>nul || (echo [错误] 没找到 git，请先安装 Git for Windows & pause & exit /b 1)

rem ---- 提交者信息（只写入本仓库，不改全局）----
for /f "delims=" %%i in ('git config user.name 2^>nul') do set GN=%%i
for /f "delims=" %%i in ('git config user.email 2^>nul') do set GE=%%i
if not exist .git (
  git init -q
  git branch -M main 2>nul
)
if "!GN!"=="" (
  set /p GN=输入提交者名字（会公开显示，例如 GitHub 用户名）: 
  git config user.name "!GN!"
)
if "!GE!"=="" (
  echo 输入提交邮箱。想隐藏真实邮箱可用: 用户名@users.noreply.github.com
  set /p GE=邮箱: 
  git config user.email "!GE!"
)

git add -A
git diff --cached --quiet || git commit -q -m "Initial release: vibe-knowledge-video skill"
git branch -M main
echo [OK] 本地提交完成
echo.

rem ---- 有 gh 就一键建仓库并推送 ----
where gh >nul 2>nul
if %errorlevel%==0 (
  gh auth status >nul 2>nul || gh auth login --web -h github.com
  git remote get-url origin >nul 2>nul && (git push -u origin main) || (gh repo create %REPO% --public --source . --remote origin --push --description "Claude skill: beat-synced science explainer videos with Remotion")
  goto done
)

rem ---- 没有 gh：网页建空仓库 + git push（会弹出 GitHub 登录窗口）----
set /p GHUSER=输入你的 GitHub 用户名: 
echo.
echo 请在浏览器打开 https://github.com/new
echo   Repository name 填: %REPO%
echo   选 Public，不要勾选 Add a README / .gitignore / license
echo   点 Create repository 后回到这里
start "" https://github.com/new
pause
git remote remove origin >nul 2>nul
git remote add origin https://github.com/!GHUSER!/%REPO%.git
echo 正在推送，如果弹出登录窗口请选择 Sign in with your browser 登录 GitHub ...
git push -u origin main

:done
echo.
if %errorlevel%==0 (echo ==== 完成！仓库已发布 ====) else (echo ==== 推送失败，把上面的报错截图发给 Claude ====)
pause
