# Container Tools Quick Start

## 🎯 You Have Container Tools Extension!

Microsoft has updated the Docker extension to **"Container Tools"** - a more comprehensive extension that includes:
- ✅ Docker support
- ✅ Docker Compose support  
- ✅ Kubernetes support
- ✅ Podman support
- ✅ Enhanced features

---

## 🔍 Finding the Containers Panel

### **Look for:**
- **Container icon** in the left sidebar (not whale icon)
- **"Containers"** section in the sidebar
- **"Docker"** section (legacy name, still works)

### **If Not Visible:**

**Method 1: Command Palette**
1. `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows)
2. Type: "View: Show Containers" or "View: Show Docker"
3. Select it

**Method 2: View Menu**
1. `View → Open View...`
2. Search: "Containers"
3. Select it

**Method 3: Activity Bar**
1. `View → Appearance → Activity Bar` (make sure checked)
2. Look for container icon in sidebar

---

## 🚀 Quick Access to Docker Features

### **Via Command Palette:**
1. `Cmd+Shift+P`
2. Type: "Docker" or "Container"
3. See all available commands:
   - `Docker: View Logs`
   - `Docker: Start Container`
   - `Docker: Stop Container`
   - `Docker: Restart Container`
   - `Docker: Execute in Container`
   - `Docker: Show Docker View`

### **Via Containers Panel:**
1. Open Containers panel (container icon)
2. Expand "Containers" or "Docker"
3. Right-click container → Actions

---

## 📋 Viewing Logs

### **Method 1: Right-Click (Easiest)**
1. Open Containers panel
2. Find your container (e.g., `forecaster-backend`)
3. Right-click → "View Logs"
4. Logs open in new tab with auto-refresh

### **Method 2: Command Palette**
1. `Cmd+Shift+P`
2. Type: "Docker: View Logs"
3. Select container

### **Method 3: Terminal (No Extension Needed)**
```bash
docker-compose logs -f backend
```

---

## 🎯 What Changed?

**Old:** Docker extension (whale icon)
**New:** Container Tools extension (container icon)

**Same functionality, better features:**
- ✅ All Docker features still work
- ✅ Enhanced Dockerfile support
- ✅ Better Docker Compose integration
- ✅ Kubernetes support added
- ✅ Improved UI

---

## ✅ Quick Checklist

- [ ] Container Tools extension installed? (`Cmd+Shift+X` → Search "Container Tools")
- [ ] Containers panel visible? (Look for container icon in sidebar)
- [ ] Can access via Command Palette? (`Cmd+Shift+P` → "Docker")
- [ ] Can view logs? (Right-click container → "View Logs")

---

## 🔧 If Still Having Issues

**Use Terminal (Always Works):**
```bash
# View logs
docker-compose logs -f backend

# List containers
docker ps

# Execute in container
docker-compose exec backend bash
```

**Use Tasks (Already Set Up):**
1. `Cmd+Shift+P`
2. "Tasks: Run Task"
3. Select Docker task

---

## 📝 Summary

**You have Container Tools!** It's the updated Docker extension with more features.

**To access:**
- Look for **container icon** in sidebar
- Or use **Command Palette** (`Cmd+Shift+P` → "Docker")
- Or use **terminal** (always works)

**All Docker functionality is available!** 🎉
