# Capstone deployment on Railway

This guide deploys the Capstone application as three Railway services in one Railway project and environment:

1. **Streamlit** — the public user interface.
2. **FastAPI** — private API called by the Streamlit server.
3. **PostgreSQL** — private application database.

The API also needs a persistent Railway Volume for its FAISS curriculum index. This guide follows the current repository layout: both Python services use `capstone/` as their Railway root directory. It assumes you have a GitHub repository containing the code and a Railway account.

> Railway menus and account plans can change. If a label differs slightly, use the linked Railway documentation. Review Railway pricing and resource limits in your account before inviting users.

## Before you begin

- Make sure the code you intend to deploy has been pushed to GitHub. Railway deploys the repository branch you select.
- Confirm that `capstone/data/curriculum/physics.pdf` and `mathematics.pdf` are present and text-readable. The ingestion script expects those exact paths for `--all`.
- Keep `.env.local`, API keys, generated secrets, and local database credentials out of Git. The repository ignores `.env.local`; only enter production secrets in Railway's Variables interface.
- Decide who is allowed to use the app. **The current signup form permits a registrant to select the teacher role.** Restrict teacher account creation before sharing the app broadly; otherwise someone who finds the public app may create a teacher account.
- This deployment uses the local FAISS store with one API replica. Do not scale the API to multiple replicas while relying on one local index volume.

The app's local commands and curriculum ingestion process are also documented in [SETUP.md](../capstone/SETUP.md).

## 1. Create a Railway project

1. Sign in to [Railway](https://railway.com/).
2. Create a new project. Choose a blank project or the dashboard option to create a project without deploying a template.
3. Give it a clear name, such as `capstone-production`.
4. Use the **production** environment for the shared deployment. Keep experiments in a separate Railway environment so they cannot accidentally share production variables or data.
5. Link your GitHub account if Railway asks for access to the repository.

Railway scopes private networking and service-variable references to services in the same project and environment. See [Railway best practices](https://docs.railway.com/overview/best-practices).

## 2. Add PostgreSQL

1. In the project canvas, choose **New** (or the `+` button), then add a **PostgreSQL** service.
2. Wait until its deployment is successful.
3. Open the PostgreSQL service's **Variables** tab. Railway supplies connection values, including `DATABASE_URL`.
4. Do not generate a public database address. The API connects over Railway's private network.
5. In the database service's backup settings, enable a backup schedule appropriate for your data. Before relying on backups, perform a restore drill into a non-production database.

Railway's PostgreSQL service is private by default and provides `DATABASE_URL` for other services in the project. See [Railway PostgreSQL](https://docs.railway.com/databases/postgresql) and [backup and restore](https://docs.railway.com/guides/postgres-backups-restores).

## 3. Create the FastAPI service

1. From the project canvas, choose **New** → **GitHub Repo** (the wording may appear as “Deploy from GitHub repo”).
2. Select the repository containing this code. If prompted, choose the branch you want to deploy.
3. Rename the new service to **api**. Use this exact name for the variable reference later, or adjust the reference to match your chosen name.
4. Open the API service's **Settings** and set **Root Directory** to:

   ```text
   /capstone
   ```

5. Set the service's **Start Command** to:

   ```sh
   python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

   Bind to `0.0.0.0` and use the API service's `PORT` variable so Railway can route traffic correctly. Define `PORT` explicitly in the API service's Variables, as described below, so the web service can reference the same value. Do not use the local `--reload` option in the deployed command. See [Railway start commands](https://docs.railway.com/deployments/start-command).

6. In **Variables**, set `RAILPACK_PYTHON_VERSION` to `3.11`. This project pins `faiss-cpu==1.7.4`; selecting a compatible runtime avoids Railpack defaulting to a newer Python version for which that older FAISS wheel may be unavailable. Set the same variable on the Streamlit service in Step 6. See [Railpack Python configuration](https://railpack.com/languages/python).

7. In **Settings** → **Deploy**, set the **Healthcheck Path** to:

   ```text
   /health
   ```

   The FastAPI app already implements this endpoint. Railway uses it to verify a new deployment before switching traffic; it is not continuous monitoring. See [Railway healthchecks](https://docs.railway.com/deployments/healthchecks).

8. Leave public networking disabled for the API. The Streamlit service will reach it through Railway's private network.

### API variables

In the API service's **Variables** tab, add these variables. Use Railway's variable picker/autocomplete for the database reference so the password is not copied manually.

| Variable | Value |
|---|---|
| `PORT` | The API's internal listening port. For an existing deployment listening on `8080`, set this to `8080`; the API start command and web service reference this variable rather than duplicating the port. |
| `DATABASE_URL` | Reference the PostgreSQL service's `DATABASE_URL`, for example `${{Postgres.DATABASE_URL}}`. Use the exact PostgreSQL service name shown in your project. |
| `JWT_SECRET_KEY` | A newly generated, long, random secret. Do not use the example/default value in the code. |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `ALLOW_TEACHER_SIGNUP` | Use the same value on the API and web services. Set `true` only during initial teacher onboarding; set it to `false` before sharing the app. If omitted, teacher signup defaults off in production. |
| `VECTOR_DB_PATH` | `/data/vectors` |
| `LLM_PROVIDER` | `groq` |
| `LLM_MODEL` | `openai/gpt-oss-20b` (or the model configured for your Groq account) |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` |
| `LLM_TIMEOUT_SECONDS` | `45` |
| `GROQ_API_KEY` | Your Groq API key, if you will use question generation. Store it only on the API service. |

Generate the JWT secret locally in PowerShell:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the output directly into the API service's `JWT_SECRET_KEY` variable. Do not put it in this deployment guide or commit it to Git.

The settings names above correspond to `app/core/config.py`. Railway variables become environment variables at runtime; Railway's `${{Service.VARIABLE}}` syntax keeps service references current. See [Railway variables](https://docs.railway.com/variables) and [variable references](https://docs.railway.com/variables/reference).

### Add persistent storage for FAISS

The API writes its FAISS index and `curriculum.metadata.json` sidecar to `VECTOR_DB_PATH`. A normal service filesystem is not durable across deploys, so attach a volume:

1. In the project canvas, add a **Volume** and attach it to the **api** service.
2. Set its **Mount Path** to:

   ```text
   /data/vectors
   ```

3. Confirm that the API service has `VECTOR_DB_PATH=/data/vectors`.
4. Keep the API at **one replica** for this deployment. The app uses a file-backed index, and extra replicas do not automatically share or coordinate separate indexes.

Railway mounts volumes when a service starts. Pre-deploy commands do not have the volume mounted, so curriculum ingestion is a later step run inside the live API service. See [Railway Volumes](https://docs.railway.com/volumes) and [pre-deploy commands](https://docs.railway.com/deployments/pre-deploy-command).

## 4. Configure database migrations

The project uses Alembic. Configure the API deployment to run migrations before each new API deployment:

1. Open API **Settings** → **Deploy**.
2. Set **Pre-Deploy Command** to:

   ```sh
   alembic upgrade head
   ```

3. Save the setting.

The API service's `DATABASE_URL` reference must be configured first. `alembic/env.py` reads that setting and applies migrations to the production database. `alembic upgrade head` is safe to run again when there are no unapplied migrations. Railway stops the deployment if the command exits unsuccessfully, so read the deploy logs if it fails; do not repeatedly retry an unexplained migration error.

Railway documents pre-deploy commands as the place for database migrations. They run with service variables and private networking but without the mounted volume. This migration does not need the FAISS volume.

## 5. Deploy and verify the API

1. Trigger a deployment from the API service's **Deployments** tab if it has not started automatically.
2. Open the deployment logs. Wait for the build, pre-deploy migration, and API startup to finish successfully.
3. Confirm the healthcheck passes.
4. Confirm the API remains private. No public API domain is needed for normal use by Streamlit.

If the build fails, first check that the root directory is `/capstone`, the start command is exact, and required dependencies are listed in `capstone/requirements.txt`. If a database error occurs, confirm that `DATABASE_URL` references the PostgreSQL service in this same project and environment.

## 6. Create the Streamlit service

1. From the same project canvas, add another **GitHub Repo** service using the same repository and branch.
2. Rename it to **web** or **streamlit**.
3. Set its **Root Directory** to:

   ```text
   /capstone
   ```

4. In **Variables**, set `RAILPACK_PYTHON_VERSION` to `3.11`, matching the API service.

5. Set its **Start Command** to:

   ```sh
   python -m streamlit run frontend/Home.py --server.address 0.0.0.0 --server.port $PORT
   ```

6. Add an `API_BASE_URL` variable with this value, replacing `api` if you named the service differently:

   ```text
   http://${{api.RAILWAY_PRIVATE_DOMAIN}}:${{api.PORT}}
   ```

   Define `PORT` explicitly in the API service's Variables (see **API variables** above) and ensure it matches the port Uvicorn listens on. The web service can then reference that configured service variable. Use `http` for private service-to-service communication. The Streamlit Python process calls FastAPI using this environment variable; browsers do not call the private API directly.

7. Add `ENVIRONMENT=production` and set `ALLOW_TEACHER_SIGNUP` to the same value as on the API service. You can create a Railway shared variable and attach it to both services, or enter the same value separately on each service. The form hides the teacher role when this is `false`; FastAPI independently rejects teacher registration. If `ALLOW_TEACHER_SIGNUP` is missing, both services default to disabled in production.

8. Generate a public domain for the Streamlit service only: **Settings** → **Networking** → **Public Networking** → **Generate Domain**. Do not share it yet.
9. Leave the Streamlit service at one replica initially. This is the simplest setup for Streamlit session state and local process resources.
10. Deploy the service and review its logs until Streamlit starts successfully.

Both services initially install `capstone/requirements.txt`, which includes backend and test dependencies as well as Streamlit. The first builds may take longer because packages such as FAISS and sentence-transformers are large. Keep the existing shared file for the first deployment; splitting service-specific requirements can be a later build optimization.

Railway private domains use `<service-name>.railway.internal`; reference variables let you construct the API URL without hardcoding its internal host or port. See [Working with Railway domains](https://docs.railway.com/networking/domains/working-with-domains).

## 7. Ingest the curriculum into production

The PDFs are source material, but the production PostgreSQL tables and FAISS volume start independently of your local development data. Run ingestion once after PostgreSQL, API variables, and the volume are ready. Do **not** run this from your local machine with `railway run`: that command injects cloud variables into a local process, but the local process cannot write to the API's mounted volume.

### Install and link the Railway CLI

On Windows, if Node.js is installed, open PowerShell and run:

```powershell
npm install --global @railway/cli
railway login
```

Complete the browser login. Then link the CLI to the project and production environment. Run these interactively from the repository directory:

```powershell
railway link
```

Choose the Capstone project and its **production** environment when prompted. If the CLI asks for a service, select **api**.

### Run ingestion inside the deployed API container

Use Railway SSH so the command runs in the API container where `/data/vectors` is mounted:

```powershell
railway ssh --service api --environment production -- python -m scripts.ingest_curriculum --all
```

Wait for completion. The command reads `data/curriculum/physics.pdf` and `data/curriculum/mathematics.pdf`, writes curriculum records to production PostgreSQL, and creates the FAISS index and metadata sidecar at `/data/vectors`. The initial run downloads the `all-MiniLM-L6-v2` embedding model and may take several minutes. Check the API service logs if it exits with an error.

Do not use `--rebuild` for initial setup. Rebuild is intended to recreate a damaged/stale FAISS index from curriculum records already in the database.

See [Railway SSH](https://docs.railway.com/cli/ssh) for service shells and single-command execution. Railway documents that this accesses the running service container; its mounted volume is available there.

## 8. Smoke-test the deployed app

Before sharing the URL, create your initial teacher accounts and then turn teacher signup off:

1. While the URL is undistributed, set `ALLOW_TEACHER_SIGNUP=true` on both services and deploy the staged changes.
2. Open the Streamlit URL and create the teacher accounts you need through the existing signup form.
3. Change `ALLOW_TEACHER_SIGNUP` to `false` on both services and deploy the staged changes. If using a shared variable, change it once and apply/redeploy both services.
4. Confirm that signup offers only Student and that a teacher-registration request is rejected by the API. Existing teacher accounts remain able to sign in and use teacher pages.
5. Only then share the Streamlit URL.

If a Railway deploy applies variable changes automatically in your project, wait for both services to finish redeploying before sharing. In any case, do not leave teacher signup enabled during public use.

Open the public Streamlit domain and work through the following checks:

1. **Frontend to API:** The Streamlit page loads without an “API unavailable” error. If not, verify `API_BASE_URL` and the exact API service name.
2. **Authentication:** Register and sign in with a test student account. Confirm logout and login work.
3. **Role access:** Verify student and teacher navigation differs by role and protected workflows reject the wrong role.
4. **Curriculum:** Confirm the curriculum-backed pages can retrieve Mathematics and Physics curriculum data.
5. **Student flow:** Complete a small exam and confirm a result is saved and can be viewed.
6. **Teacher flow:** Sign in as an authorized teacher. Verify roster, assessment creation/assignment, question retrieval, and analytics. Test generation only if `GROQ_API_KEY` is set.
7. **Persistence:** Restart or redeploy the API, then confirm curriculum retrieval still works. This checks that the FAISS index is on the volume and not only in the temporary container filesystem.

Use test accounts and non-sensitive data during these checks. The `/health` endpoint confirms API startup, but it does not verify database migrations, curriculum files, model downloads, or LLM credentials.

## 9. Backups, access, and ongoing operation

- Enable PostgreSQL backups and periodically verify that you can restore one. A backup that has never been restored is unverified.
- Back up the API's FAISS volume or keep a documented way to rebuild it from PostgreSQL source records and the unchanged curriculum PDFs. The database and vector index are separate persisted data and should both be considered in recovery planning.
- Keep API and PostgreSQL private. Only Streamlit needs a public domain for normal app usage.
- Keep `JWT_SECRET_KEY` and `GROQ_API_KEY` out of Git, screenshots, and logs. Rotate the JWT secret if it is exposed; existing access tokens will no longer validate.
- Keep `ALLOW_TEACHER_SIGNUP=false` before sharing the public URL. The API rejects teacher registrations even if a request bypasses the Streamlit form.
- Start with one API replica while using local FAISS on a volume. If you later need multiple API replicas, move vectors into a shared vector service/store and verify concurrent ingestion behavior before scaling.
- Monitor API and Streamlit deployment logs after each deploy. Railway healthchecks are used during deployment activation, not as an ongoing uptime monitor.

## Troubleshooting quick reference

| Symptom | First things to check |
|---|---|
| Railway reports no start command | Confirm the service's custom start command and `/capstone` root directory. |
| API healthcheck fails | Confirm the API binds to `0.0.0.0:$PORT`, and healthcheck path is `/health`. |
| API reports database connection error | Confirm API `DATABASE_URL` references Railway PostgreSQL in the same environment; check migration logs. |
| Streamlit says API unavailable or its API URL has a blank port | Confirm the API service has an explicitly defined `PORT` variable, that Uvicorn listens on that port, and that `API_BASE_URL` is `http://${{api.RAILWAY_PRIVATE_DOMAIN}}:${{api.PORT}}`. Confirm both services are running in the same project/environment. |
| Curriculum retrieval finds no data | Run the ingestion command in the live API container; check its logs and confirm both PDFs are present in the deployed repository. |
| Curriculum works, then disappears after redeploy | Confirm the API volume mount is `/data/vectors` and `VECTOR_DB_PATH` matches exactly. |
| Generation returns provider errors | Set a valid `GROQ_API_KEY` on the API service and verify the configured Groq model name. |
| API deploy fails during migration | Read the pre-deploy logs, confirm database access and migration state, and resolve the specific error before retrying. |

## Railway documentation referenced

- [Deploying monorepos](https://docs.railway.com/deployments/monorepo)
- [PostgreSQL](https://docs.railway.com/databases/postgresql)
- [Variables and references](https://docs.railway.com/variables/reference)
- [Private and public domains](https://docs.railway.com/networking/domains/working-with-domains)
- [Start commands](https://docs.railway.com/deployments/start-command)
- [Healthchecks](https://docs.railway.com/deployments/healthchecks)
- [Pre-deploy commands](https://docs.railway.com/deployments/pre-deploy-command)
- [Volumes](https://docs.railway.com/volumes)
- [Railway CLI SSH](https://docs.railway.com/cli/ssh)
