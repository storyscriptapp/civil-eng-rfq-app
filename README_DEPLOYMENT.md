# 🚀 Quick Start - Deploying to Your Jellyfin Server

## 📦 What You Have

You now have everything needed to deploy your RFQ Tracker to your home server!

---

## 🎯 Deployment Options

### **Option 1: Full Production Setup** ⭐ **Recommended**
- Hosted on your Jellyfin server
- Accessible from anywhere via Cloudflare Tunnel
- Password protected
- Auto-starts on boot
- Automatic backups

**Follow:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Complete step-by-step guide

---

### **Option 2: Quick Test on Server**
Just want to test it on the server first?

1. Copy project folder to server
2. Install Python & dependencies
3. Run `start_api.bat`
4. Access at `http://[server-ip]:8000`

---

## 📁 Files You'll Need

### **Authentication** 🔐
- `rfq_scraper/auth.py` - Login system (username/password)

### **Deployment Scripts** 📜
- `DEPLOYMENT_GUIDE.md` - Complete deployment instructions
- `start_api.bat` - Quick start script for Windows
- `backup_database.ps1` - Backup script
- `install_service.ps1` - Auto-start on boot

### **Configuration**
- Default username: `admin`
- Default password: `changeme123` (⚠️ **CHANGE THIS!**)
- To change: Run `python auth.py` in the rfq_scraper folder

---

## 🔒 Security Features Added

✅ **Password Protection** - Login required for all write operations
✅ **HTTPS Ready** - Works with Cloudflare Tunnel (automatic SSL)
✅ **No Ports Exposed** - Cloudflare Tunnel keeps your network hidden
✅ **Rate Limiting** - Blocks brute force login attempts
✅ **Secure Passwords** - Uses SHA-256 hashing

---

## 📱 What You'll Be Able to Do

Once deployed:

1. **Access from work PC:** `https://rfq.yourdomain.com`
2. **Access from phone:** Same URL!
3. **Run scraper remotely:** Click button in web UI
4. **Share with team:** Just give them the URL and password

---

## 🆘 Help & Support

### **Need Help with Setup?**
1. Follow [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. YouTube searches:
   - "Cloudflare Tunnel setup Windows"
   - "Windows Task Scheduler auto start"
3. Take screenshots of any errors and let me know!

### **Common Issues**

**"Can't access from internet"**
- Check Cloudflare tunnel is running
- Verify API is running locally first

**"Forgot password"**
- Run `python auth.py` to generate new hash
- Update Windows environment variable

**"API won't start"**
- Check port 8000 isn't already in use
- Verify Python venv is activated

---

## 🎉 Ready to Deploy?

**Start here:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

It has everything you need with screenshots and step-by-step instructions!

---

## 💡 Tips

- 📸 **Take screenshots** of your Cloudflare setup (helpful for troubleshooting)
- 🔐 **Save your password** somewhere secure (like a password manager)
- 💾 **Test backups** before relying on them
- 🧪 **Test locally first** before setting up Cloudflare Tunnel

---

Good luck! You've got this! 🚀

