# Git Push Script

cd d:\VSCodeAllFiles\api_t2sql

# Setup git config (chỉ cho repo này)
git config user.name "nqt1310"
git config user.email "nqt1310@example.com"

# Add all changes
git add -A

# Commit
git commit -m "Add Smart Query Frontend with Excel/CSV support

Features:
- Smart Query Mode: Upload file + requirements
- Excel/CSV file reader with SheetJS
- Auto-generate query from file data
- CORS middleware for frontend
- Frontend enable/disable config
- Debug tools and error handling
- Clean UI with gradient design"

# Push to remote
git push origin master
