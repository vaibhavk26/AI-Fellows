# Local PostgreSQL Setup

This guide configures PostgreSQL on Windows for the Capstone project.

The project uses two local databases:

- `capstone`: development database used while running the API locally.
- `capstone_test`: isolated database for automated tests.

Production uses a separate, hosted database and is not created on a developer machine.

## 1. Install PostgreSQL

Open PowerShell and install PostgreSQL with Windows Package Manager:

```powershell
winget install PostgreSQL.PostgreSQL
```

If `winget` is unavailable or cannot locate the package, download the Windows installer from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/).

In the installer:

1. Keep **PostgreSQL Server** and **Command Line Tools** selected.
2. Keep the default port, `5432`.
3. Choose and securely store a password for the `postgres` administrator account.
4. Complete the installation.

## 2. Confirm the PostgreSQL service is running

Close and reopen PowerShell, then run:

```powershell
Get-Service postgresql*
```

The PostgreSQL service should have a status of `Running`. If it is stopped, start it:

```powershell
Get-Service postgresql* | Start-Service
```

## 3. Connect as the PostgreSQL administrator

Run the following command and enter the password selected during installation:

```powershell
psql -U postgres -h localhost
```

If PowerShell does not recognize `psql`, run it using the installation path. Adjust the version number if necessary:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost
```

## 4. Create the project user and databases

At the `postgres=#` prompt, run the following SQL. Replace `your-local-password` with a strong local password.

```sql
CREATE USER capstone_user WITH PASSWORD 'your-local-password';
CREATE DATABASE capstone OWNER capstone_user;
CREATE DATABASE capstone_test OWNER capstone_user;
```

List the databases to confirm they were created, then exit `psql`:

```sql
\l
\q
```

## 5. Verify the development database connection

Connect using the newly created project user:

```powershell
psql -U capstone_user -h localhost -d capstone
```

Enter the password for `capstone_user`. A successful connection displays a `capstone=>` prompt. Exit with:

```sql
\q
```

## 6. Configure the application

In the `capstone` directory, create or update `.env.local` with credentials that match the password used in step 4:

```text
database_url=postgresql+psycopg2://capstone_user:your-local-password@localhost:5432/capstone
test_database_url=postgresql+psycopg2://capstone_user:your-local-password@localhost:5432/capstone_test
```

Do not commit `.env.local` or share its password.

## Troubleshooting

| Problem | Resolution |
| --- | --- |
| `psql` is not recognized | Reopen PowerShell after installation, or use the full executable path shown in step 3. |
| Connection refused | Verify the PostgreSQL service is running with `Get-Service postgresql*`. |
| Password authentication failed | Confirm the username, password, host, and port in `.env.local` match the PostgreSQL user created in step 4. |
| Port `5432` is already in use | Choose a different unused port during installation and update both application URLs to use it. |