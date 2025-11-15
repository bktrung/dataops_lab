# 🚀 Jenkins CI/CD Setup with Docker & PostgreSQL (GCP)

This guide walks you through setting up a **Jenkins CI/CD pipeline** on **Google Cloud Compute Engine**, complete with **Dockerized PostgreSQL** and a **remote agent node**.

---

## 🧱 1. Create Jenkins Server (GCP)

### 1.1. Provision a VM

1. Go to **Google Cloud Console → Compute Engine → VM Instances → Create Instance**
2. **Name:** `jenkins-server`
3. **OS:** Ubuntu 24.04 LTS x86/64
4. **Disk Size:** 20 GB
5. **Networking:** Check both **Allow HTTP** and **Allow HTTPS**
6. Click **Save** and **Create**

### 1.2. Assign a Static IP

- Go to **VPC Network → IP Addresses → Reserve Static Address**
- Match the **region** with your VM
- Assign the reserved IP to `jenkins-server`

### 1.3. SSH into the Server

```bash
ssh -i /path/to/private_key username@<EXTERNAL_IP>
```

Update base packages:

```bash
sudo apt update && sudo apt install -y curl wget gnupg2 ca-certificates lsb-release apt-transport-https software-properties-common
```

---

## ⚙️ 2. Install Jenkins

```bash
mkdir -p /tools/jenkins
cd /tools/jenkins
vi jenkins-install.sh
```

Paste:

```bash
apt install -y openjdk-17-jdk openjdk-17-jre
java --version
wget -p -O - https://pkg.jenkins.io/debian/jenkins.io.key | apt-key add -
sh -c 'echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 5BA31D57EF5975CA
apt-get update
apt install -y jenkins
systemctl start jenkins
ufw allow 8080
```

Run the script:

```bash
chmod +x jenkins-install.sh
sudo sh jenkins-install.sh
systemctl status jenkins
```

> ✅ Create a **firewall rule** to allow inbound TCP **port 8080**

Retrieve the initial admin password:

```bash
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

Open `http://<EXTERNAL_IP>:8080`, log in, create an admin, and install **Suggested Plugins**.

---

## 🐘 3. Setup PostgreSQL via Docker

### 3.1. Install Docker

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 3.2. Create a Database Container

```bash
mkdir -p /tools/db
cd /tools/db
vi docker-compose.yml
```

Add:

```yaml
services:
  db:
    image: pgvector/pgvector:0.8.1-pg17-bookworm
    container_name: ytchat-db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: postgres
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    ports:
      - "5432:5432"

volumes:
  pg_data:
```

Start the database:

```bash
sudo docker compose up -d
```

> 🔥 Add a firewall rule to **allow port 5432**

Test connection:

```bash
psql -U postgres -d postgres -h <DB_HOST> -p 5432
```

---

## 🧩 4. Setup Jenkins Agent Node (lab-server)

1. Create another VM (`lab-server`)
2. Assign static IP + allow HTTP/HTTPS
3. SSH into it and install prerequisites:

```bash
sudo -i
apt install -y openjdk-17-jdk
adduser jenkins
mkdir -p /opt/jenkins-agent
chown -R jenkins:jenkins /opt/jenkins-agent
su jenkins
```

4. On **Jenkins Dashboard → Manage Jenkins → Nodes → New Node**,  
   create a node named **lab-server**, set **Remote root dir:** `/opt/jenkins-agent`, and save.

5. From the node page, copy the “Run from agent command line” command and execute it inside `/opt/jenkins-agent`.

---

## 🔁 5. Create Jenkins Agent Service

```bash
sudo tee /etc/systemd/system/jenkins-agent.service <<'EOF'
[Unit]
Description=Jenkins Agent
After=network.target

[Service]
User=jenkins
WorkingDirectory=/opt/jenkins-agent
ExecStart=/usr/bin/java -jar agent.jar -url http://<JENKINS_IP>:8080/   -secret @secret-file -name "lab-server" -webSocket -workDir "/opt/jenkins-agent"
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable jenkins-agent
sudo systemctl start jenkins-agent
systemctl status jenkins-agent
```

Now `sudo systemctl start jenkins-agent` connects the node automatically.

---

## 🐳 6. Docker Access for Jenkins User

```bash
sudo usermod -aG docker jenkins
su jenkins
docker ps   # should work without sudo
sudo systemctl restart jenkins
```

---

## 🟩 7. Install Node.js (for migrations)

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## 🧰 8. Configure Jenkins Pipeline

### 8.1. Add Required Plugins
- **Blue Ocean**
- **Active Choices**

### 8.2. Pipeline Parameters

In project configuration:
- **Discard Old Builds:** Keep 10
- **Parameters:**
  - **Active Choice:** `server` → `return ["lab-server"]`
  - **String:** `hash` → commit hash
  - **Active Choice:** `action` → `return ["start", "stop", "upcode", "rollback", "migrate"]`

---

## 🧾 9. Jenkins Pipeline Script

```groovy
<-- Groovy script here (omitted for brevity) -->
```

---

## 🔑 10. Environment Variables (lab-server)

```bash
mkdir -p /opt/envs
cd /opt/envs
vi ytchat-backend.env
```

Add:

```bash
GEMINI_API_KEY=YOUR-KEY
EMBEDDING_DIMENSION=768
GEMINI_EMBEDDING_MODEL='text-embedding-004'
DATABASE_URL=postgresql://postgres:postgres@<DB_IP>:5432/postgres
GEMINI_CHAT_MODEL=gemini-2.0-flash-exp
PORT=3000
NODE_ENV=production
CORS_ORIGIN=http://localhost
LOG_LEVEL=info
```

---

## 🔁 11. Jenkins Actions

| Action | Description |
|--------|--------------|
| **start** | Start project containers |
| **stop** | Stop containers |
| **upcode** | Checkout code by hash → build + push images → restart with new version |
| **rollback** | Rollback to previous image tags |
| **migrate** | Run database migrations via drizzle-kit |

---

## ⚠️ Troubleshooting

- **Permission denied on Docker socket:**
  ```bash
  ERROR: permission denied while trying to connect to the Docker daemon socket
  ```
  → Reboot and ensure `jenkins` user is in `docker` group.

---

## ✅ Result

You now have:
- A **Jenkins master server** on GCP
- A **PostgreSQL test database** via Docker
- A **remote Jenkins agent** node for project builds
- A fully parameterized **CI/CD pipeline** with build, deploy, rollback, and migration steps.
