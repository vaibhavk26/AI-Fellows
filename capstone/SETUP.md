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
'''Start PostgreSQL
'''Open PowerShell as Administrator:
Get-Service *postgres*

'''Find the service name, such as postgresql-x64-18, then start it:
Start-Service postgresql-x64-18

'''Open PostgreSQL’s SQL shell. Enter password set at the time of database creation when prompted to enter password.
psql -U postgres -h localhost

```sql
CREATE USER capstone_user WITH PASSWORD 'replace-local-password';
CREATE DATABASE capstone OWNER capstone_user;
CREATE DATABASE capstone_test OWNER capstone_user;
```

## Run app

```powershell
uvicorn app.main:app --reload --port 8000
```
