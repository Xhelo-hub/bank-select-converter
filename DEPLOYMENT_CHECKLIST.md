# ✅ Quick Deployment Checklist

## Pre-Deployment Requirements

- [ ] **Hetzner Server Ready**
  - [ ] HestiaCP installed and accessible
  - [ ] SSH access working
  - [ ] Server IP address noted: `_________________`

- [ ] **Cloudflare Configuration**  
  - [ ] Domain added to Cloudflare
  - [ ] A record created: `converter.yourdomain.com` → `SERVER_IP`
  - [ ] SSL/TLS set to "Full (strict)"
  - [ ] "Always Use HTTPS" enabled

- [ ] **Access Credentials**
  - [ ] HestiaCP Username: `admin` (or your username)
  - [ ] HestiaCP Password: `_________________`
  - [ ] SSH Root Access: `ssh root@SERVER_IP`

---

## Deployment Steps (30-45 minutes)

### **Phase 1: DNS Setup (5 minutes)**
- [ ] Cloudflare A record created
- [ ] DNS propagation verified: `nslookup converter.yourdomain.com`

### **Phase 2: Server Preparation (10 minutes)**
- [ ] SSH connected to server
- [ ] System updated: `apt update && apt upgrade -y`
- [ ] Dependencies installed: `apt install -y python3 python3-pip python3-venv git nginx`

### **Phase 3: HestiaCP Domain (5 minutes)**
- [ ] Domain added via HestiaCP web interface OR command line
- [ ] SSL certificate generated with Let's Encrypt
- [ ] Domain accessible via HTTPS (may show default page)

### **Phase 4: Application Setup (15 minutes)**
- [ ] Repository cloned to `/home/admin/bank-select-converter`
- [ ] Python virtual environment created
- [ ] Dependencies installed from requirements.txt
- [ ] Files copied to web directory
- [ ] Permissions set correctly (import/export folders writable)

### **Phase 5: Service Configuration (10 minutes)**
- [ ] Systemd service file created (`/etc/systemd/system/bank-converter.service`)
- [ ] Nginx configuration updated in HestiaCP
- [ ] Services enabled and started
- [ ] Local connection test successful: `curl http://127.0.0.1:8000/server-status`

### **Phase 6: Final Verification (5 minutes)**
- [ ] Website accessible: `https://converter.yourdomain.com`
- [ ] File upload test successful
- [ ] Conversion test successful  
- [ ] Auto-deletion working (no files saved permanently)

---

## Quick Commands Reference

```bash
# Connect to server
ssh root@YOUR_SERVER_IP

# Check service status
systemctl status bank-converter
systemctl status nginx

# View logs
journalctl -u bank-converter -f

# Restart if needed
systemctl restart bank-converter
systemctl reload nginx

# Check disk usage
df -h /home/admin/web/converter.yourdomain.com/public_html/Bank_Specific_Converter/

# Manual cleanup (if needed)
rm -rf /home/admin/web/converter.yourdomain.com/public_html/Bank_Specific_Converter/import/*
rm -rf /home/admin/web/converter.yourdomain.com/public_html/Bank_Specific_Converter/export/*
```

---

## Troubleshooting Quick Fixes

| Problem | Solution |
|---------|----------|
| 502 Bad Gateway | `systemctl restart bank-converter` |
| Permission Denied | `chown -R admin:admin /home/admin/web/converter.yourdomain.com/` |
| Import folder not writable | `chmod 777 /home/admin/web/.../import` |
| SSL Certificate Error | Re-run: `v-add-letsencrypt-domain admin converter.yourdomain.com` |
| Cloudflare 522 Error | Check if services are running: `systemctl status bank-converter nginx` |

---

## Success Indicators

✅ **All Green Lights:**
- Service status: `active (running)`
- Nginx status: `active (running)`  
- Website loads without errors
- File upload works
- Conversion produces correct QBO files
- Files are automatically deleted after download
- HTTPS certificate is valid (green padlock)

## Contact & Support

- **GitHub Repository**: https://github.com/Xhelo-hub/bank-select-converter
- **Server Status Check**: `https://converter.yourdomain.com/server-status`
- **Log Location**: `/var/log/nginx/domains/converter.yourdomain.com.error.log`

---

**Estimated Total Time**: 30-45 minutes  
**Difficulty Level**: Intermediate  
**Prerequisites**: Basic Linux command line knowledge