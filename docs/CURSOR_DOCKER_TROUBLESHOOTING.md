# Cursor Docker Extension Troubleshooting

## 🐋 Can't Find Containers Panel/Container Icon?

**Note:** Microsoft has updated the Docker extension to "Container Tools" - look for container icon instead of whale icon.

### **Step 1: Check if Extension is Installed**

**Method 1: Via Extensions Panel**
1. Press `Cmd+Shift+X` (or `Ctrl+Shift+X` on Windows/Linux)
2. Search for "Container Tools" or "Docker"
3. Check if "Container Tools" by Microsoft is installed
4. If not installed, click "Install"

**Method 2: Via Command Palette**
1. Press `Cmd+Shift+P` (or `Ctrl+Shift+P`)
2. Type: "Extensions: Show Installed Extensions"
3. Search for "Container Tools" or "Docker"
4. Check installation status

---

### **Step 2: Enable Docker Panel**

**If Extension is Installed but Panel Not Visible:**

**Method 1: Show Activity Bar**
1. `View → Appearance → Activity Bar` (make sure it's checked)
2. Look for whale icon in left sidebar

**Method 2: Command Palette**
1. `Cmd+Shift+P`
2. Type: "View: Show Containers" or "View: Show Docker"
3. Or: "Docker: Focus on Docker View" or "Container: Focus on Containers View"

**Method 3: Manual Panel Access**
1. `View → Open View...`
2. Search: "Containers" or "Docker"
3. Select "Containers" or "Docker" view

---

### **Step 3: Alternative - Use Command Palette**

Even without the panel, you can use Docker commands:

1. Press `Cmd+Shift+P`
2. Type "Docker" to see all Docker commands:
   - `Docker: View Logs`
   - `Docker: Start Container`
   - `Docker: Stop Container`
   - `Docker: Restart Container`
   - `Docker: Execute in Container`

---

### **Step 4: Check Extension Status**

**Verify Extension is Active:**
1. `Cmd+Shift+P`
2. Type: "Developer: Show Running Extensions"
3. Look for `ms-azuretools.vscode-docker`
4. Check if it's enabled

**If Disabled:**
1. Go to Extensions (`Cmd+Shift+X`)
2. Find Docker extension
3. Click "Enable"

---

## 🔧 Alternative Solutions

### **Option 1: Use Terminal (No Extension Needed)**

**View Logs:**
```bash
# In Cursor terminal (Ctrl+` or View → Terminal)
docker-compose logs -f backend
```

**Manage Containers:**
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart backend

# Execute in container
docker-compose exec backend bash
```

### **Option 2: Use Tasks (Already Created)**

I've created `.vscode/tasks.json` with Docker tasks:

1. `Cmd+Shift+P`
2. Type: "Tasks: Run Task"
3. Select:
   - "Docker: View Backend Logs"
   - "Docker: View All Logs"
   - "Docker: Restart Backend"
   - etc.

### **Option 3: Install Extension Manually**

**If Extension Search Doesn't Work:**

1. Open Extensions panel (`Cmd+Shift+X`)
2. Click "..." (three dots) in top right
3. Select "Install from VSIX..." (if available)
4. Or download from: https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker

---

## 🎯 Quick Fix Checklist

- [ ] Extension installed? (`Cmd+Shift+X` → Search "Docker")
- [ ] Extension enabled? (Check in Extensions panel)
- [ ] Activity bar visible? (`View → Appearance → Activity Bar`)
- [ ] Tried Command Palette? (`Cmd+Shift+P` → "Docker")
- [ ] Tried "View: Show Docker"? (`Cmd+Shift+P` → "View: Show Docker")

---

## 📋 Manual Installation Steps

**Step-by-Step:**

1. **Open Extensions:**
   - `Cmd+Shift+X` (Mac) or `Ctrl+Shift+X` (Windows/Linux)

2. **Search:**
   - Type: "Container Tools" or "Docker"
   - Look for: "Container Tools" by Microsoft
   - Publisher: Microsoft

3. **Install:**
   - Click "Install" button
   - Wait for installation

4. **Reload:**
   - May need to reload Cursor
   - `Cmd+Shift+P` → "Developer: Reload Window"

5. **Verify:**
   - Check sidebar for container icon (or whale icon if legacy)
   - Or `Cmd+Shift+P` → "Docker" or "Container" (should see commands)

---

## 🔍 If Still Not Working

### **Check Cursor Version:**
- Docker extension requires Cursor based on VS Code 1.60+
- Update Cursor if needed

### **Check Docker is Running:**
```bash
# In terminal
docker ps

# Should show running containers
# If error, Docker Desktop might not be running
```

### **Use Terminal Instead:**
If extension doesn't work, terminal is fully functional:

```bash
# View logs
docker-compose logs -f backend

# List containers
docker ps

# Container details
docker inspect forecaster-backend
```

---

## ✅ Recommended: Use Terminal + Tasks

Since the panel might not be visible, use:

1. **Terminal** for logs:
   ```bash
   docker-compose logs -f backend
   ```

2. **Tasks** for quick commands:
   - `Cmd+Shift+P` → "Tasks: Run Task" → "Docker: View Backend Logs"

3. **Command Palette** for Docker commands:
   - `Cmd+Shift+P` → Type "Docker" → Select command

---

## 📝 Summary

**If whale icon not visible:**
1. ✅ Check extension is installed (`Cmd+Shift+X`)
2. ✅ Try Command Palette (`Cmd+Shift+P` → "Docker")
3. ✅ Use terminal (works without extension)
4. ✅ Use tasks (already set up in `.vscode/tasks.json`)

**All Docker functionality works via terminal/tasks even without the panel!**
