# 🎮 Tic-Tac-Toe Gradio Web App

A full-featured Tic-Tac-Toe web application built with Python and Gradio, ready for free permanent deployment on [Render](https://render.com).

## 🌟 Features
- 👥 Player vs Player (PvP)
- 🤖 Player vs AI (PvE)
- 🟢 Easy, 🟡 Medium, and 🔴 Hard (Minimax AI)
- 🏆 Score tracking across rounds
- 🔄 New Board & Winning Board highlights
- 🗑️ Score resets

---

## 🚀 How to Deploy on Render (Step-by-Step)

### Step 1: Push to GitHub
1. Create a new repository on [GitHub](https://github.com/new) (e.g. `tic-tac-toe`).
2. Run the following commands in this directory:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/tic-tac-toe.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render
1. Go to [dashboard.render.com](https://dashboard.render.com) and log in.
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository (`tic-tac-toe`).
4. Fill in the settings:
   - **Name**: `tic-tac-toe` (or any name you like)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Instance Type**: `Free`
5. Click **Deploy Web Service**!

Render will build and deploy your app. Once deployed, you will get a permanent public link like:
`https://tic-tac-toe-xxxx.onrender.com`
