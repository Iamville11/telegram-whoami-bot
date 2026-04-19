@echo off
echo Initializing Git repository...
git init

echo Adding files...
git add .

echo Creating first commit...
git commit -m "Initial commit: Telegram Who Am I bot"

echo Adding GitHub remote...
git remote add origin https://github.com/YOUR_USERNAME/telegram-whoami-bot.git

echo Pushing to GitHub...
git branch -M main
git push -u origin main

echo Done! Your bot is now on GitHub.
pause
