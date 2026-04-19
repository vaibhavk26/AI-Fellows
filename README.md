# 🚀 AI-Fellows – Team Git Workflow Guide

Welcome to the **AI-Fellows repository** on GitHub.
This guide defines the **standard workflow** everyone must follow to collaborate smoothly.

---

# 🌿 Branch Strategy

```text
main        → final / stable code
dev-<name>  → individual workspace
```

### Examples:

* `dev-vaibhav`
* `dev-amol`
* `dev-tushar`
* `dev-anguraj`
* `dev-rahul`

---

# 🚫 Ground Rules

* ❌ Do NOT push directly to `main`
* ✅ Always work in your own branch (`dev-<name>`)
* ✅ Always create a Pull Request (PR) to merge into `main`
* ✅ Pull latest code before starting work

---

# 🔁 Daily Workflow (Follow Every Time)

## 1️⃣ Get Latest Code

```bash
git checkout main
git pull origin main
```

---

## 2️⃣ Switch to Your Branch

### Option A — Using Git command

```bash
git checkout dev-yourname
```

### Option B — Using VS Code (Recommended for beginners)

* Look at **bottom-left corner** in VS Code
* Click on current branch name (e.g., `main`)
* Select your branch: `dev-yourname`

👉 Always confirm you are on your branch before starting work.

---

## 3️⃣ Sync Your Branch with Main

```bash
git merge main
```

---

## 4️⃣ Do Your Work

* Add/modify code
* Complete assignments
* Create new files if needed

---

## 5️⃣ Commit Your Changes

```bash
git add .
git commit -m "your message"
```

### ✅ Good Commit Message Examples

```bash
git commit -m "Added assignment 1 solution for stacks"
git commit -m "Implemented basic list operations"
git commit -m "Fixed bug in file handling logic"
git commit -m "Refactored code for better readability"
git commit -m "Added comments and documentation"
```

### ❌ Avoid

```bash
git commit -m "update"
git commit -m "final"
git commit -m "changes"
```

---

## 6️⃣ Push Your Branch

```bash
git push origin dev-yourname
```

---

## 7️⃣ Create Pull Request (PR)

* Go to GitHub
* Select your branch
* Click **"Compare & Pull Request"**
* Add description
* Request review

---

## 8️⃣ Merge to Main

* Get at least 1 review (recommended)
* Merge PR into `main`

---

# 🔄 Before Starting Any New Work

Always run:

```bash
git checkout main
git pull origin main

git checkout dev-yourname
git merge main
```

---

# ⚠️ Merge Conflicts (If Happens)

If you see:

```text
<<<<<<< HEAD
your code
=======
other code
>>>>>>> main
```

### Fix it:

1. Edit file and resolve conflict
2. Save file

```bash
git add .
git commit -m "Resolved merge conflict"
```

---

# 🧠 Quick Cheat Sheet

```bash
# Start work
git checkout main
git pull origin main
git checkout dev-yourname
git merge main

# After work
git add .
git commit -m "your message"
git push origin dev-yourname
```

---

# 🎯 Goal

* Clean collaboration
* No conflicts
* Easy tracking of work
* Learn real-world Git workflow

---

# 🚀 Final Note

Always check your branch in VS Code before coding ⚠️

If unsure:

* Ask before pushing
* Don’t guess and break `main` 😄

Let’s keep the repo clean and professional!

