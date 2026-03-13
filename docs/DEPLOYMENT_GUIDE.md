## Astraeus 2.0 — Deployment Guide

**Audience:** Engineers and operators responsible for running Astraeus in local, test, or production environments.  
**Prerequisites:** Docker and basic CLI familiarity; for manual dev, Python + Node.js installed.

This guide explains how to run Astraeus locally for development and how to deploy it to a Linux VM (e.g. AWS EC2) using Docker Compose. It assumes you are using the React frontend and FastAPI backend that live in this repository.

**See also:**
- [`docs/ARCHITECTURE_OVERVIEW.md`](ARCHITECTURE_OVERVIEW.md) — system architecture and request/response flows.
- [`docs/AWS_EC2_SETUP.md`](AWS_EC2_SETUP.md) — step‑by‑step EC2 instructions for newcomers to AWS.

---

### 1. Components and ports

- **Backend API** (`Dockerfile.api`, `server/api.py`)
  - Runs FastAPI with Uvicorn on port **8765** inside the container.
  - Exposed as `http://localhost:8765` on the host by default.
- **React frontend** (`Dockerfile.frontend`, `frontend/`)
  - Built with Vite and served by Nginx on port **80** in the container.
  - Exposed as `http://localhost:4173` on the host by default.
- **Legacy Streamlit UI** (`Dockerfile.streamlit`, `app.py`, `ui/`)
  - Optional; served on port **8501** inside the container and mapped to **8502** on the host (if you enable it).
- **Vector store data**
  - ChromaDB data directory: `data/chroma_db/` on the host.
  - Mounted into the API container at `/app/data/chroma_db`.

All of these services are wired together in `docker-compose.yml`.

---

### 2. Environment variables

Create a `.env` file in the project root (same directory as `docker-compose.yml`) if you have not already.

At minimum, you will typically set:

- `OPENROUTER_API_KEY` — default LLM API key (can be left empty if you prefer to enter a key in the sidebar per run).
- `TAVILY_API_KEY` — default web search key (can also be provided from the UI).
- `HF_TOKEN` — optional Hugging Face token for private embedding models.

The React app can work with these keys either from `.env` (backend configured) or via user‑provided keys in the sidebar, validated with the `/api/llm/test` and `/api/tavily/test` endpoints.

---

### 3. Running locally with Docker Compose

**Prerequisites**

- Docker and Docker Compose (Docker Desktop on macOS/Windows; `docker` + `docker compose` on Linux).
- A `.env` file as described above.

**Steps**

1. From the project root:

   ```bash
   mkdir -p data/chroma_db
   docker compose up -d --build
   ```

2. Verify services:

   ```bash
   docker compose ps
   docker compose logs -f api
   ```

   Press `Ctrl+C` to stop following logs.

3. Open the app in your browser:

   - React frontend: `http://localhost:4173`
   - Backend health: `http://localhost:8765/api/health`

4. (Optional) Streamlit UI

   If you keep the `streamlit` service enabled, it will be available at `http://localhost:8502`. For most workflows the React frontend is the primary UI.

5. Stop the stack:

   ```bash
   docker compose down
   ```

---

### 4. Running locally without Docker

You can also run the backend and frontend directly for development.

**Backend (FastAPI)**

1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Ensure `.env` exists in the project root.
4. Start the API:

   ```bash
   uvicorn server.api:app --reload --port 8765
   ```

5. Check health:

   - `http://localhost:8765/api/health`

**Frontend (React)**

1. From the project root:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. By default Vite will run on `http://localhost:5173` and proxy API calls to `http://localhost:8765` if you configure `VITE_API_BASE` in a `.env` file under `frontend/` or via your shell:

   ```bash
   export VITE_API_BASE=http://localhost:8765
   npm run dev
   ```

3. Open the app in your browser at Vite’s dev URL (usually `http://localhost:5173`).

---

### 5. Building images manually

If you need to build images yourself (outside of Compose), the key Dockerfiles are:

- Backend:

  ```bash
  docker build -f Dockerfile.api -t astraeus-api .
  ```

- Frontend:

  ```bash
  docker build -f Dockerfile.frontend -t astraeus-frontend .
  ```

  You can override the API base at build time:

  ```bash
  docker build -f Dockerfile.frontend \
    --build-arg VITE_API_BASE=http://localhost:8765 \
    -t astraeus-frontend .
  ```

---

### 6. Deploying to a Linux VM (e.g. AWS EC2)

The steps below summarize the production deployment flow. For a more detailed, AWS‑specific walkthrough, see `AWS_EC2_SETUP.md`.

**6.1 Create a VM**

- Provision an Ubuntu 22.04 LTS VM with:
  - 2 vCPU, 2–4 GB RAM (e.g. `t3.small` or `t3.medium` on AWS).
  - 20–30 GB disk to start.
- Open these inbound ports in the VM’s firewall / security group:
  - `22` — SSH.
  - `80` / `443` — optional for a reverse proxy (if you front the app with Nginx/Caddy).
  - `8765` — backend API (optional if not behind a proxy).
  - `4173` — React frontend.

**6.2 Install Docker on the VM**

On the VM:

```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
```

Log out and back in so the group change takes effect, then verify:

```bash
docker --version
docker compose version
```

**6.3 Copy code and configuration**

On the VM:

```bash
sudo apt install -y git
git clone <YOUR_REPO_URL> Astraeus-Multi-Agent-AI-Researcher
cd Astraeus-Multi-Agent-AI-Researcher
```

Create the data directory:

```bash
mkdir -p data/chroma_db
```

Copy your `.env` from your laptop or create it directly on the VM:

```bash
nano .env
```

Populate keys and settings as you would locally.

**6.4 Run with Docker Compose on the VM**

On the VM, in the project directory:

```bash
docker compose up -d --build
docker compose ps
```

Check logs if needed:

```bash
docker compose logs -f api
```

**6.5 Access the app**

- React frontend: `http://<VM_PUBLIC_IP>:4173`
- Backend health: `http://<VM_PUBLIC_IP>:8765/api/health`

If you enabled the Streamlit service, it will be at `http://<VM_PUBLIC_IP>:8502`.

**6.6 Optional: reverse proxy and HTTPS**

For a production‑grade setup:

- Point a domain’s A record to the VM’s public IP.
- Install Nginx or Caddy on the VM.
- Obtain TLS certificates (e.g. Let’s Encrypt).
- Route:
  - `/` → frontend container (port 4173).
  - `/api` → backend container (port 8765).

---

### 7. Quick reference table

| Environment | How to run                            | Frontend URL                     | Backend URL                          |
|------------|----------------------------------------|----------------------------------|--------------------------------------|
| Local (Docker) | `docker compose up -d --build`        | `http://localhost:4173`          | `http://localhost:8765/api/health`   |
| Local (manual) | `uvicorn server.api:app --reload` + `npm run dev` in `frontend/` | Vite dev URL (e.g. `http://localhost:5173`) | `http://localhost:8765/api/health`   |
| VM (Docker)    | `docker compose up -d --build` on VM | `http://<VM_PUBLIC_IP>:4173`     | `http://<VM_PUBLIC_IP>:8765/api/health` |


