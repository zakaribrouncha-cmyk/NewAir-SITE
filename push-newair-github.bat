@echo off
chcp 65001 >nul
cls
echo ========================================
echo  PUSH DU SITE NEWAIR VERS GITHUB
echo ========================================
echo.
echo Ce fichier doit etre place dans le dossier du site,
echo la ou il y a index.html, assets et video.
echo.
if not exist "index.html" (
  echo ERREUR: index.html introuvable ici.
  echo Mets ce fichier .bat dans le dossier air-exact puis relance.
  echo.
  pause
  exit /b 1
)
if not exist "assets" (
  echo ERREUR: dossier assets introuvable ici.
  echo Mets ce fichier .bat dans le dossier air-exact puis relance.
  echo.
  pause
  exit /b 1
)
if not exist "video" (
  echo ATTENTION: dossier video introuvable. Le site peut marcher sans video mais le fond sera manquant.
  echo.
)

git --version >nul 2>&1
if errorlevel 1 (
  echo ERREUR: Git n'est pas installe ou pas reconnu.
  echo Installe Git pour Windows puis relance ce fichier.
  echo.
  pause
  exit /b 1
)

echo Initialisation Git...
git init
git branch -M main
git remote remove origin >nul 2>&1
git remote add origin https://github.com/zakaribrouncha-cmyk/NewAir-SITE.git

echo.
echo Ajout des fichiers...
git add -A

echo.
echo Creation du commit...
git commit -m "Upload New Air site"

echo.
echo Envoi vers GitHub...
git push -u origin main --force

echo.
echo ========================================
echo TERMINE. Va sur GitHub et actualise avec F5.
echo Puis sur Render: Manual Deploy > Deploy latest commit.
echo ========================================
echo.
pause
