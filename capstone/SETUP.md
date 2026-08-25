# Setup Guide

## Local environment

```powershell
cd .\capstone
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Environment variables

Copy `.env.example` to `.env.local` and configure the values for the local PostgreSQL and LLM setup.

## Database setup

```sql
CREATE USER capstone_user WITH PASSWORD 'replace-local-password';
CREATE DATABASE capstone OWNER capstone_user;
CREATE DATABASE capstone_test OWNER capstone_user;
```

## Run app

```powershell
uvicorn app.main:app --reload --port 8000
```
