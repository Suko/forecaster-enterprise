# Cursor IDE Docker Extensions & Log Viewing

## 🎯 Best Extensions for Docker Development in Cursor

Since Cursor is based on VS Code, it supports VS Code extensions. Here are the best ones for Docker development:

---

## 🔧 Essential Docker Extensions

### **1. Container Tools (by Microsoft) - NEW**
**Extension ID:** `ms-azuretools.vscode-docker` (now part of Container Tools)

**Note:** Microsoft has updated the Docker extension to "Container Tools" which includes Docker support plus additional container features.

**Features:**
- ✅ View running containers
- ✅ View Docker images
- ✅ View Docker volumes
- ✅ View Docker networks
- ✅ **View container logs** (right-click container → View Logs)
- ✅ Execute commands in containers
- ✅ Build and run containers
- ✅ Docker Compose support
- ✅ Kubernetes support
- ✅ Container registry management

**Install:**
```
1. Open Cursor
2. Press Cmd+Shift+X (Extensions)
3. Search: "Container Tools" or "Docker"
4. Install "Container Tools" by Microsoft
```

**Usage:**
- Open Containers panel (container icon in sidebar)
- Right-click container → "View Logs"
- Right-click container → "Attach Shell" (terminal access)
- Right-click container → "Start/Stop/Restart"

---

### **2. Docker Compose Support**
**Note:** Docker Compose support is now included in Container Tools extension

**Features:**
- ✅ Manage docker-compose services
- ✅ View service logs
- ✅ Start/stop services
- ✅ View service status
- ✅ Compose file validation

---

### **3. Remote - Containers (by Microsoft)**
**Extension ID:** `ms-vscode-remote.remote-containers`

**Features:**
- ✅ Develop inside containers
- ✅ Attach to running containers
- ✅ Full IDE experience in container

**Use Case:** Advanced - for developing inside containers

---

## 📋 Built-in Terminal Options

### **Option 1: Integrated Terminal**
Cursor has built-in terminal support:

```bash
# View logs in terminal
docker-compose logs -f backend

# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f db
```

**Access:** `View → Terminal` or `` Ctrl+` ``

---

### **Option 2: Docker Extension Log Viewer**

**Steps:**
1. Install Docker extension
2. Open Docker panel (whale icon)
3. Expand "Containers"
4. Right-click container → "View Logs"
5. Logs open in new tab with:
   - Auto-refresh
   - Search/filter
   - Color coding

---

## 🎨 Recommended Extension Setup

### **Quick Install Script:**

```bash
# Install via command line (if you have code CLI)
code --install-extension ms-azuretools.vscode-docker
# Container Tools includes Docker support
```

### **Or Manual Install:**

1. **Open Extensions:**
   - `Cmd+Shift+X` (Mac) or `Ctrl+Shift+X` (Windows/Linux)

2. **Search and Install:**
   - Search: `Container Tools` or `Docker`
   - Install: "Container Tools" by Microsoft
   - (Includes Docker, Docker Compose, and Kubernetes support)

3. **Verify:**
   - Look for container icon in sidebar (or whale icon if legacy)
   - Should see Containers panel

---

## 🚀 Using Docker Extension

### **View Logs:**

**Method 1: Right-Click Menu**
1. Open Containers panel (container icon in sidebar)
2. Expand "Containers" or "Docker"
3. Find your container (e.g., `forecaster-backend`)
4. Right-click → "View Logs"
5. Logs open in new tab

**Method 2: Command Palette**
1. `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows)
2. Type: "Docker: View Logs" or "Container: View Logs"
3. Select container

### **Execute Commands:**

1. Right-click container → "Attach Shell"
2. Opens terminal inside container
3. Run commands directly:
   ```bash
   # Inside container
   alembic upgrade head
   pytest tests/
   ```

### **Manage Containers:**

- **Start:** Right-click → "Start"
- **Stop:** Right-click → "Stop"
- **Restart:** Right-click → "Restart"
- **Remove:** Right-click → "Remove"

---

## 📊 Log Viewing Features

### **In Container Tools Log Viewer:**

- ✅ **Auto-refresh** - Logs update automatically
- ✅ **Search** - `Cmd+F` to search logs
- ✅ **Filter** - Filter by service/container
- ✅ **Color coding** - Errors in red, etc.
- ✅ **Timestamps** - See when events occurred
- ✅ **Follow mode** - Auto-scroll to latest

### **In Terminal:**

```bash
# Follow logs (live updates)
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Since specific time
docker-compose logs --since 10m backend

# Multiple services
docker-compose logs -f backend db

# With timestamps
docker-compose logs -f -t backend
```

---

## 🛠️ Advanced: Custom Tasks

### **Create Tasks for Common Commands:**

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Docker: View Backend Logs",
      "type": "shell",
      "command": "docker-compose logs -f backend",
      "problemMatcher": []
    },
    {
      "label": "Docker: View All Logs",
      "type": "shell",
      "command": "docker-compose logs -f",
      "problemMatcher": []
    },
    {
      "label": "Docker: Restart Backend",
      "type": "shell",
      "command": "docker-compose restart backend",
      "problemMatcher": []
    }
  ]
}
```

**Usage:**
- `Cmd+Shift+P` → "Tasks: Run Task"
- Select task

---

## 🎯 Quick Reference

### **View Logs:**
```bash
# Terminal
docker-compose logs -f backend

# Docker Extension
Right-click container → View Logs
```

### **Execute in Container:**
```bash
# Terminal
docker-compose exec backend bash

# Docker Extension
Right-click container → Attach Shell
```

### **Restart Service:**
```bash
# Terminal
docker-compose restart backend

# Docker Extension
Right-click container → Restart
```

### **View Status:**
```bash
# Terminal
docker-compose ps

# Container Tools Extension
View in Containers panel sidebar
```

---

## 📝 Recommended Workflow

### **For Development:**

1. **Install Container Tools Extension**
   - `Cmd+Shift+X` → Search "Container Tools" → Install

2. **Open Containers Panel**
   - Click container icon in sidebar (or look for Containers/Docker section)
   - See all containers

3. **View Logs**
   - Right-click `forecaster-backend` → "View Logs"
   - Keep tab open for live updates

4. **Quick Actions**
   - Right-click to start/stop/restart
   - Right-click → "Attach Shell" for terminal access

### **For Debugging:**

1. **View Logs** (Docker extension or terminal)
2. **Search logs** (`Cmd+F` in log viewer)
3. **Filter by service** (if multiple)
4. **Execute commands** (Attach Shell)

---

## 🔍 Alternative: Terminal-Based Workflow

If you prefer terminal (no extensions needed):

```bash
# Terminal 1: Backend logs
docker-compose logs -f backend

# Terminal 2: Database logs
docker-compose logs -f db

# Terminal 3: All logs
docker-compose logs -f

# Terminal 4: Execute commands
docker-compose exec backend bash
```

**Cursor Terminal:**
- Split terminals: `` Ctrl+` ``
- Multiple terminals: `+` button
- Each terminal can run different command

---

## 📚 Summary

**Best Extension:**
- ✅ **Container Tools by Microsoft** - Full Docker management + log viewing (includes Docker extension)

**Quick Setup:**
1. Install Container Tools extension (`Cmd+Shift+X` → "Container Tools")
2. Open Containers panel (container icon in sidebar)
3. Right-click containers → View Logs

**Alternative:**
- Use built-in terminal: `docker-compose logs -f backend`

**Both methods work great!** Choose based on preference:
- **Extension:** Visual, integrated, easy clicks
- **Terminal:** Fast, flexible, scriptable

---

## 🎉 Pro Tips

1. **Keep log viewer open** - Pin tab for easy access
2. **Use search** - `Cmd+F` to find errors quickly
3. **Multiple terminals** - One for logs, one for commands
4. **Docker extension** - Great for container management
5. **Terminal** - Great for automation/scripts
