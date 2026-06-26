# AWS EC2 setup guide for Astraeus 2.0

This guide walks you through creating a Linux VM on AWS EC2 from scratch, then deploying Astraeus (Docker) on it. No prior AWS experience assumed.

---

## Prerequisites

- **AWS account**: Sign up at [aws.amazon.com](https://aws.amazon.com) if you don’t have one.
- **Local machine**: Terminal and SSH (macOS/Linux have these; on Windows use PowerShell or WSL).

---

## Part 1: Create an EC2 instance (VM)

### 1.1 Log in and open EC2

1. Go to [console.aws.amazon.com](https://console.aws.amazon.com) and sign in.
2. In the top search bar, type **EC2** and open **EC2** (under Services).
3. Make sure the **region** (top-right, e.g. "N. Virginia", "Mumbai") is where you want the server. You can change it from the dropdown.

### 1.2 Launch an instance

1. In the left sidebar, click **Instances**.
2. Click the orange **Launch instance** button.

### 1.3 Name and OS

- **Name**: e.g. `astraeus-server` (optional but useful).
- **Application and OS Images (AMI)**:
  - Leave **Quick Start** selected.
  - Choose **Ubuntu**.
  - Pick **Ubuntu Server 22.04 LTS** (64-bit x86). Do not pick ARM unless you know you want it.

### 1.4 Instance type

- Under **Instance type**, choose **t3.small** (2 vCPU, 2 GB RAM) for light use, or **t3.medium** (2 vCPU, 4 GB RAM) for more comfortable runs.
- Smaller types (e.g. t3.micro) can work but may be slow for builds and pipeline runs.

### 1.5 Key pair (required for SSH)

1. Under **Key pair (login)**, click **Create new key pair**.
2. **Key pair name**: e.g. `astraeus-key`.
3. **Key pair type**: **RSA**.
4. **Private key format**: **.pem** (for SSH on Mac/Linux).
5. Click **Create key pair**. A `.pem` file will download; store it somewhere safe (e.g. `~/.ssh/astraeus-key.pem`). You cannot download it again.

### 1.6 Network settings

1. Expand **Network settings**.
2. **Create security group** (leave selected).
3. **Security group name**: e.g. `astraeus-sg`.
4. **Inbound rules** – add these by clicking **Add security group rule** for each:

| Type        | Port / Range | Source    | Purpose        |
|------------|-------------|-----------|----------------|
| SSH        | 22          | My IP     | SSH from your PC |
| Custom TCP | 80          | Anywhere  | HTTP (browser) |
| Custom TCP | 443         | Anywhere  | HTTPS          |
| Custom TCP | 8765        | Anywhere  | Backend API (optional, for direct API access) |
| Custom TCP | 4173        | Anywhere  | React frontend (optional) |
| Custom TCP | 8502        | Anywhere  | Streamlit (host port; container 8501) |

- **Source “My IP”**: use it for SSH so only your current IP can connect. For “Anywhere” AWS will show `0.0.0.0/0` (any internet IP). You can restrict 8765/4173/8501 to “My IP” later for security.
5. Leave **Outbound** as default (all traffic allowed).

### 1.7 Storage

- **Configure storage**: **40 GB gp3** minimum recommended (see disk space note in Part 3). You can increase later if builds fail with “no space left on device”.

### 1.8 Launch

1. Scroll down and click **Launch instance**.
2. Click the instance ID in the success message (or go to **Instances**). Wait until **Instance state** is **Running** and **Status check** is **2/2 checks passed** (may take 1–2 minutes).

---

## Part 2: Get the VM’s address and connect (SSH)

### 2.1 Public IP or DNS

1. In **Instances**, select your instance.
2. In the details below, note **Public IPv4 address** (or **Public IPv4 DNS**). Example: `54.123.45.67` or `ec2-54-123-45-67.compute-1.amazonaws.com`.  
   This is your **VM_PUBLIC_IP** (or hostname) for the next steps.

### 2.2 SSH from your laptop

1. Move the key somewhere standard (if you didn’t already):
   ```bash
   mkdir -p ~/.ssh
   mv ~/Downloads/astraeus-key.pem ~/.ssh/
   chmod 400 ~/.ssh/astraeus-key.pem
   ```
2. Connect (replace with your key path and VM address):
   ```bash
   ssh -i ~/.ssh/astraeus-key.pem ubuntu@<VM_PUBLIC_IP>
   ```
   Example:
   ```bash
   ssh -i ~/.ssh/astraeus-key.pem ubuntu@54.123.45.67
   ```
3. When asked “Are you sure you want to continue connecting?”, type `yes`.
4. You should see a prompt like `ubuntu@ip-172-31-xx-xx:~$`. You are now on the VM.

---

## Part 2b: Allocate an Elastic IP (recommended)

The **auto-assigned public IP** changes every time you **Stop** and **Start** the instance. For a stable URL (e.g. for `.env` and sharing), attach an **Elastic IP**.

1. In the EC2 console left menu, click **Elastic IPs** (under **Network & Security**).
2. Click **Allocate Elastic IP address** → **Allocate**.
3. Select the new address → **Actions** → **Associate Elastic IP address**.
4. **Resource type:** Instance.
5. **Instance:** select your Astraeus server (e.g. `astraeus-server`).
6. **Private IP:** leave blank (uses the primary private IP).
7. Click **Associate**.

Use the **Elastic IP** as your `VM_PUBLIC_IP` in `.env` (`VITE_API_BASE`, `ALLOWED_ORIGINS`) and rebuild the frontend if you change it.

**Cost:** Free while the Elastic IP is **associated with a running instance**. If you release it or leave it unattached, AWS may charge a small hourly fee.

**Tip:** After stop/start, the Elastic IP stays the same; only the auto-assigned IP would have changed without this step.

---

## Part 3: Install Docker and Docker Compose on the VM

Run these on the VM (after SSH):

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker (official script)
curl -fsSL https://get.docker.com | sudo sh

# Allow your user to run docker without sudo (optional)
sudo usermod -aG docker ubuntu

# Verify
docker --version
docker compose version
```

If you ran `usermod -aG docker ubuntu`, log out and SSH back in so the group change applies. Then:

```bash
docker ps
docker compose version
```

### Disk space warning

Docker images for this project are large:

- The **API** image includes `sentence-transformers`, PyTorch, and related ML dependencies.
- The **Streamlit** container also pulls in PyTorch (~3 GB layer).

**Minimum recommended EBS root volume: 40 GB** (not 20 GB). If `docker compose build` fails with **no space left on device**:

1. **AWS Console** → EC2 → **Volumes** → select the instance root volume → **Actions** → **Modify volume** → increase to **40 GB** or more → confirm.
2. **SSH into the VM** and expand the filesystem (Ubuntu, typical NVMe root device):

   ```bash
   sudo growpart /dev/nvme0n1 1
   sudo resize2fs /dev/nvme0n1p1
   df -h /
   ```

   If your device name differs, run `lsblk` and adjust (`/dev/xvda1` on older instances).

3. Free Docker cache:

   ```bash
   sudo docker system prune -af
   ```

4. Retry the build:

   ```bash
   cd ~/Multi-Agent-AI-Researcher-FullStack
   sudo docker compose up -d --build
   ```

### Public deploy security (`.env`)

On a **public** EC2 URL, add:

```env
CORS_STRICT=true
ALLOWED_ORIGINS=http://<VM_PUBLIC_IP>:4173
```

Leave `OPENROUTER_API_KEY` empty so visitors use sidebar keys. A server-side key is not sent to the browser, but open `POST /api/run` can still **spend your credits** without rate limits being a full substitute.

---

## Part 4: Put your app on the VM

### Option A: Clone from Git (recommended)

On the VM:

```bash
sudo apt install -y git
git clone https://github.com/kunalkachru/Multi-Agent-AI-Researcher-FullStack.git
cd Multi-Agent-AI-Researcher-FullStack
```

Replace the URL with your actual repo (HTTPS or SSH). If the repo is private, use a personal access token or deploy key.

### Option B: Copy from your laptop with SCP

From your **laptop** (not the VM):

```bash
scp -i ~/.ssh/astraeus-key.pem -r /path/to/Astraeus-Multi-Agent-AI-Researcher ubuntu@<VM_PUBLIC_IP>:~/
```

Then on the VM:

```bash
cd ~/Astraeus-Multi-Agent-AI-Researcher
```

---

## Part 5: Add `.env` and data directory on the VM

- **`.env`**: The VM needs the same variables as locally (OpenRouter, Tavily, etc.). Either:
  - From laptop:  
    `scp -i ~/.ssh/astraeus-key.pem .env ubuntu@<VM_PUBLIC_IP>:~/Astraeus-Multi-Agent-AI-Researcher/.env`
  - Or on the VM: create the file with `nano .env` and paste your keys (no quotes needed around values).
- **Data directory** (for vector store):
  ```bash
  mkdir -p data/chroma_db
  ```

---

## Part 6: Build and run with Docker Compose on the VM

On the VM, in the project directory:

```bash
cd ~/Astraeus-Multi-Agent-AI-Researcher
sudo docker compose up -d --build
```

Check that containers are running:

```bash
sudo docker compose ps
sudo docker compose logs -f api
```

Press Ctrl+C to stop following logs.

---

## Part 7: Open the app in your browser

Use the VM’s **public IP** (or public DNS):

- **React frontend**: `http://<VM_PUBLIC_IP>:4173`
- **Streamlit** (if you started it): `http://<VM_PUBLIC_IP>:8502` (default `docker-compose.yml` mapping)
- **Backend health**: `http://<VM_PUBLIC_IP>:8765/api/health`

If you don’t see the app:

- Confirm the instance’s **security group** allows inbound traffic on 4173 (and 8765/8501 if you use them).
- Confirm containers are up: `sudo docker compose ps`.

---

## Part 8: Optional – use a domain and HTTPS

1. Point a domain’s **A record** to the VM’s public IP.
2. On the VM, install a reverse proxy (e.g. Nginx or Caddy) and obtain a certificate (e.g. Let’s Encrypt with Caddy or certbot). Route `/` to the frontend and `/api` to the backend. This is described in the main deployment plan (reverse proxy step).

---

## Quick reference

| Step            | Where    | Command / action |
|-----------------|----------|-------------------|
| Create VM       | AWS Console | EC2 → Launch instance (Ubuntu 22.04+, t3.small, **40 GB** gp3, key pair, security group with 22, 80, 443, 8765, 4173, 8501) |
| Elastic IP      | AWS Console | EC2 → Elastic IPs → Allocate → Associate to instance (stable public IP) |
| Connect         | Laptop   | `ssh -i ~/.ssh/astraeus-key.pem ubuntu@<VM_IP>` |
| Install Docker  | VM       | `curl -fsSL https://get.docker.com \| sudo sh` |
| Get code        | VM       | `git clone <repo> && cd Multi-Agent-AI-Researcher-FullStack` |
| Add .env        | Laptop or VM | Set `VITE_API_BASE` + `ALLOWED_ORIGINS` to Elastic IP; `scp .env` or `nano .env` |
| Run app         | VM       | `sudo docker compose up -d --build` |
| Open app        | Browser  | `http://<VM_IP>:4173` |

---

## Troubleshooting

- **SSH “Permission denied (publickey)”**: Check that you use `-i path/to/astraeus-key.pem` and `ubuntu@<IP>`. For Amazon Linux the user is often `ec2-user` instead of `ubuntu`.
- **Cannot reach app in browser**: Check security group inbound rules for 4173 (and 8765/8501). Ensure the VM has a **public IP** (or use an Elastic IP so it doesn’t change after restart).
- **Out of memory during build**: Use a larger instance type (e.g. t3.medium) or add swap: `sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`.
