# 🎫 Support Desk - Databricks App

Una aplicación de soporte técnico construida con Flask y Lakebase (Postgres gestionado por Databricks).

## Características

* **Gestión de Tickets**: Crea, visualiza y actualiza tickets de soporte
* **Mensajería**: Agrega mensajes a los tickets para seguimiento
* **Estados**: Maneja estados de tickets (OPEN, IN_PROGRESS, RESOLVED, CLOSED)
* **UI Moderna**: Interfaz de usuario limpia y responsiva
* **Integración Databricks**: Usa identidad del usuario autenticado

## Arquitectura

```
├── app_tickets.py       # Flask API para gestión de tickets
├── db.py               # Operaciones de base de datos usando lakebase.py
├── lakebase.py         # Cliente de conexión a Postgres
├── app.yaml            # Configuración de Databricks App
├── requirements.txt    # Dependencias Python
├── setup_secrets.py    # Script para configurar secretos
└── templates/
    └── tickets.html    # Interfaz de usuario
```

## Configuración

### 1. Crear tablas en Lakebase

Las tablas se crean automáticamente al iniciar la app:

```sql
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ticket_messages (
    message_id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(ticket_id),
    message_text TEXT NOT NULL,
    author TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 2. Configurar secretos

Ejecuta el script para almacenar la URL de Lakebase:

```bash
python setup_secrets.py
```

Esto creará:
- Scope: `database`
- Key: `lakebase-url`
- Valor: Tu connection string de Postgres

### 3. Desplegar la app

```bash
databricks apps create support-desk
databricks apps deploy support-desk --source-code-path .
```

## Endpoints API

### GET /tickets
Lista todos los tickets

### GET /tickets/:id
Obtiene un ticket específico

### GET /tickets/:id/messages
Obtiene todos los mensajes de un ticket

### POST /tickets
Crea un nuevo ticket
```json
{
  "title": "Unable to access account",
  "created_by": "user@example.com"
}
```

### POST /tickets/:id/messages
Agrega un mensaje a un ticket
```json
{
  "message_text": "I've reset your password",
  "author": "support@example.com"
}
```

### PUT /tickets/:id/status
Actualiza el estado de un ticket
```json
{
  "status": "RESOLVED"
}
```

## Desarrollo Local

1. Instala dependencias:
```bash
pip install -r requirements.txt
```

2. Configura variables de entorno:
```bash
export LAKEBASE_SECRET_SCOPE="database"
export LAKEBASE_SECRET_KEY="lakebase-url"
```

3. Ejecuta la app:
```bash
python app_tickets.py
```

4. Abre http://localhost:8000

## Stack Tecnológico

* **Backend**: Flask (Python)
* **Base de Datos**: Lakebase (Postgres gestionado)
* **Frontend**: HTML/CSS/JavaScript vanilla
* **Autenticación**: Databricks Apps (X-Forwarded-Email header)
* **Deployment**: Databricks Apps

## Notas

* La identidad del usuario se obtiene automáticamente del header `X-Forwarded-Email` en producción
* En desarrollo local, usa el SDK de Databricks para obtener el usuario actual
* Los estados válidos son: `OPEN`, `IN_PROGRESS`, `RESOLVED`, `CLOSED`

---

### ARCHIVADO - Documentación anterior de Massive API

### 1. Create a Massive.com account and get an API key (LEGACY)

1. Go to [https://massive.com](https://massive.com) and sign up for a new account (or log in if you already have one).
2. Once logged in, open your account/workspace **Settings** (or **Developer** / **API** section, depending on Massive's current UI).
3. Find **API Keys** and click **Create API Key** (or **Generate New Key**).
4. Give the key a name (e.g. `databricks-app`) and copy the generated key value immediately — most providers only show it once.
5. Keep this key handy for step 3 (Store your secrets) below. Do **not** put it in code, `.env` committed to git, or anywhere else in plaintext.

> If Massive's console differs from the steps above, look for **API Keys**, **Tokens**, or **Credentials** under your account/organization settings — the key is what authenticates requests to `https://api.massive.com` in `massive_client.py`.

### 2. Create a Lakebase instance and a native-password role

1. In your Databricks workspace, go to **Catalog** (left sidebar) and select the **Lakebase** tab (or search "Lakebase" in the workspace search bar).
2. Click **Create Lakebase instance** (sometimes labeled **Create database instance**).
   - Give it a name (e.g. `massive-sync-db`).
   - Choose the capacity/compute size and region appropriate for your workload (defaults are fine to start).
   - Click **Create** and wait for the instance to reach the **Available**/**Running** state.
3. Open the newly created instance, then go to the **Roles & Databases** tab (sometimes called **Permissions** or **Roles**).
4. **Enable native (password) authentication** for the instance if it isn't already on:
   - Look for an authentication setting such as **Native passwords** or **Password authentication** and toggle/enable it. By default some Lakebase instances only support OAuth/token-based auth — you need password auth enabled so the role below gets a static password instead of a short-lived token.
5. **Create a new role**:
   - Click **Add role** / **Create role**.
   - Choose **Password** as the authentication method (not OAuth).
   - Name the role (e.g. `massive_app`) and let Databricks generate (or set) a password.
6. **Copy the connection URL** shown for the role. It will look like:

   ```
   postgresql://<role>:<password>@<host>.database.cloud.databricks.com:5432/databricks_postgres?sslmode=require
   ```

   Keep this URL — you'll paste it into `setup_secrets.py`'s prompt in the next step.

### 3. Store your secrets

Run once from a **Databricks notebook** in your workspace (no CLI needed):

1. Create a new notebook (or open the Git folder you'll create in step 5, once it's cloned) and attach it to any running cluster.
2. In a cell, run:

   ```python
   %sh python setup_secrets.py
   ```

   or open a terminal from the notebook (**Run** > **Open terminal**, if enabled on your cluster) and run `python setup_secrets.py` there.

This prompts (via `getpass`, so nothing is echoed or written to disk/shell history) for:
- Your **Massive API key** (from step 1) → stored as secret `massive/api-key`
- Your **Lakebase connection URL** (from step 2) → stored as secret `database/lakebase-url`

### 4. Configure environment variables (local dev)

Copy `.env.example` to `.env` and paste your Lakebase URL as `LAKEBASE_URL` for local runs:

```bash
cp .env.example .env
```

For deployment, `app.yaml` already pulls `LAKEBASE_URL` from the `database/lakebase-url` secret automatically — no manual editing needed there.

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run locally

```bash
python app.py
```

### 7. Create a Git folder in Databricks and deploy the app (no CLI required)

All of this is done through the Databricks workspace UI:

1. **Create a Git folder**:
   - In the Databricks workspace sidebar, click **Workspace** > **Create** > **Git folder** (in older UIs this is called **Repos** > **Add Repo**).
   - Paste the Git URL of this project's repository (e.g. your GitHub/GitLab remote for this codebase).
   - Choose a folder name and click **Create Git folder**. Databricks will clone the repo directly into your workspace — this becomes the source for your app.

2. **Create the Databricks App**:
   - In the sidebar, go to **Compute** > **Apps** (or search "Apps" in the workspace search bar).
   - Click **Create app**, then choose **Custom** (or "From scratch").
   - Give the app a name (e.g. `massive-lakebase-sync`).

3. **Point the app at your Git folder**:
   - When prompted for the source code location, select **Workspace files** / **Git folder** and browse to the Git folder you created in step 1 (the folder containing `app.py` and `app.yaml`).
   - Databricks will read `app.yaml` from that folder automatically to configure the `command` and `env` (including the `LAKEBASE_URL`, `MASSIVE_API_BASE_URL`, and secret scope/key references).

4. **Deploy**:
   - Click **Deploy** (or **Create and deploy**) in the Apps UI. Databricks will build and start the app using the Git folder's current contents — no `databricks` CLI commands are needed.
   - Whenever you update the code, pull the latest changes into the Git folder (**Git folder** > **Pull**, via the UI) and click **Deploy** again in the Apps UI to redeploy.

5. Once deployed, open the app's URL from the Apps UI and hit `GET /healthz` to confirm it's running, then try `POST /sync` to pull data from Massive into Lakebase.

## Endpoints

- `GET /healthz` - health check
- `GET /records?limit=100` - read synced records from Lakebase
- `POST /sync?batch_size=500` with optional JSON body `{"path": "/records"}` - pull from Massive API and upsert into Lakebase
- `GET /watchlist` - get the current user's watchlist symbols with last known price
- `POST /watchlist` - add/update a symbol on the current user's watchlist

## Enabling Change Data Feed (CDF) for Postgres tables

Lakebase supports **Change Data Feed (CDF)**, a managed way to stream row-level inserts/updates/deletes
from your Lakebase Postgres tables into Unity Catalog Delta tables (no Debezium, no custom connectors).
CDF is enabled per-**schema** in the `databricks_postgres` database, and every table in that schema that
meets two conditions is picked up automatically: it has `REPLICA IDENTITY FULL` set, and it has at least
one row.

### 1. Set `REPLICA IDENTITY FULL` on the tables you want to track

By default, Postgres only logs primary-key columns on change. To capture full row contents (needed for
CDF), enable `REPLICA IDENTITY FULL` on each table — including `watchlist` and `massive_records` from
this app:

```sql
ALTER TABLE watchlist REPLICA IDENTITY FULL;
ALTER TABLE massive_records REPLICA IDENTITY FULL;
```

Run this once per table, either from a Databricks SQL editor connected to your Lakebase instance, or
from a `psql` session using your `LAKEBASE_URL`. Any new table you add later (e.g. via `ensure_table`-style
helpers in `app.py`) needs the same `ALTER TABLE ... REPLICA IDENTITY FULL` statement run once before it
will be included in the feed. Tables with the setting but zero rows are skipped until the first row is
inserted, then picked up automatically.

You can confirm which tables currently qualify by querying:

```sql
SELECT * FROM wal2delta.tables;
```

### 2. Start CDF from the Lakebase UI

1. In your Databricks workspace, open the **Lakebase** tab for your instance.
2. Go to **Lakebase CDF** and click **Start**.
3. Select the `databricks_postgres` database and the schema containing your tables (the default
   schema, `public`, works — it's inside `databricks_postgres`).
4. Choose the Unity Catalog destination schema/catalog where the CDF history tables should land.
5. Confirm — the UI shows a preview of qualifying tables (e.g. `watchlist`, `massive_records`) and
   their sync status before you start.

Once running, each qualifying table gets a corresponding Delta table named `lb_<table_name>_history`
(e.g. `lb_watchlist_history`) in Unity Catalog, updated roughly every 15 seconds. Each row includes
metadata columns (`_pg_change_type`, `_pg_lsn`, `_pg_xid`, `_timestamp`, `_sort_by`) describing the
change, so downstream Delta Live Tables/pipelines can build Silver/Gold layers off the append-only
history.

> **Note:** Disabling CDF is lossy — changes made while it's off aren't captured, and re-enabling
> triggers a full resync (every row reloaded as an `insert`). There's no per-table exclusion option
> within an enabled schema; the only way to keep a table out of the feed is to not set
> `REPLICA IDENTITY FULL` on it.

## Notes

- Lakebase auth uses a single `LAKEBASE_URL` secret pointing at a native Postgres role with a
  static, non-expiring password — no token refresh logic needed in `lakebase.py`.
- The Massive API pagination in `massive_client.py` assumes a `{"items": [...], "next_cursor": ...}`
  cursor-based shape. Adjust `paginated_get` to match the real API's pagination contract.
- For very large batch upserts, consider `psycopg2.extras.execute_values` instead of per-row inserts.
