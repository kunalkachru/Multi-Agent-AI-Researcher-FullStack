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
| Custom TCP | 8501        | Anywhere  | Streamlit (optional) |

- **Source “My IP”**: use it for SSH so only your current IP can connect. For “Anywhere” AWS will show `0.0.0.0/0` (any internet IP). You can restrict 8765/4173/8501 to “My IP” later for security.
5. Leave **Outbound** as default (all traffic allowed).

### 1.7 Storage

- **Configure storage**: 20–30 GB **gp3** is enough to start. You can increase later.

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

---

## Part 4: Put your app on the VM

### Option A: Clone from Git (recommended)

On the VM:

```bash
sudo apt install -y git
git clone https://github.com/YOUR_USERNAME/Astraeus-Multi-Agent-AI-Researcher.git
cd Astraeus-Multi-Agent-AI-Researcher
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
- **Streamlit** (if you started it): `http://<VM_PUBLIC_IP>:8501`
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
| Create VM       | AWS Console | EC2 → Launch instance (Ubuntu 22.04, t3.small, key pair, security group with 22, 80, 443, 8765, 4173, 8501) |
| Connect         | Laptop   | `ssh -i ~/.ssh/astraeus-key.pem ubuntu@<VM_IP>` |
| Install Docker  | VM       | `curl -fsSL https://get.docker.com \| sudo sh` |
| Get code        | VM       | `git clone <repo> && cd Astraeus-Multi-Agent-AI-Researcher` |
| Add .env        | Laptop or VM | `scp .env ubuntu@<VM_IP>:~/.../` or create on VM |
| Run app         | VM       | `sudo docker compose up -d --build` |
| Open app        | Browser  | `http://<VM_IP>:4173` |

---

## Troubleshooting

- **SSH “Permission denied (publickey)”**: Check that you use `-i path/to/astraeus-key.pem` and `ubuntu@<IP>`. For Amazon Linux the user is often `ec2-user` instead of `ubuntu`.
- **Cannot reach app in browser**: Check security group inbound rules for 4173 (and 8765/8501). Ensure the VM has a **public IP** (or use an Elastic IP so it doesn’t change after restart).
- **Out of memory during build**: Use a larger instance type (e.g. t3.medium) or add swap: `sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`.
