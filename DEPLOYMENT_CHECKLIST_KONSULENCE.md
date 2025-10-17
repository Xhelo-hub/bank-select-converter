# ✅ converter.konsulence.al Deployment Checklist

## **Server Information**
- **Server IP**: `78.46.201.151`
- **Domain**: `converter.konsulence.al`  
- **HestiaCP**: `http://78.46.201.151:8083`
- **GitHub Repo**: `https://github.com/Xhelo-hub/bank-select-converter`

---

## **Phase 1: Cloudflare DNS (5 minutes)**

- [ ] **Login to Cloudflare Dashboard**
- [ ] **Select domain**: `konsulence.al`
- [ ] **Add A record**:
  ```
  Type: A
  Name: converter
  IPv4: 78.46.201.151
  Proxy: 🟠 Proxied
  ```
- [ ] **Verify DNS**: `nslookup converter.konsulence.al`

---

## **Phase 2: Server Access (Setup)**

### **Option A: SSH Key Setup (Recommended)**
- [ ] Generate SSH key if needed: `ssh-keygen -t rsa -b 4096`
- [ ] Copy key to server: `ssh-copy-id root@78.46.201.151`
- [ ] Test connection: `ssh root@78.46.201.151`

### **Option B: Password Access**
- [ ] Get root password from Hetzner console
- [ ] Connect: `ssh root@78.46.201.151` (enter password)

### **Option C: HestiaCP Method**
- [ ] Access: `http://78.46.201.151:8083`
- [ ] Use File Manager + Terminal

---

## **Phase 3: Deployment (15-20 minutes)**

### **Quick Auto-Deploy Method:**
- [ ] **SSH to server**: `ssh root@78.46.201.151`
- [ ] **Run deployment**:
  ```bash
  cd /tmp
  wget https://raw.githubusercontent.com/Xhelo-hub/bank-select-converter/main/deploy_to_server.sh
  chmod +x deploy_to_server.sh
  ./deploy_to_server.sh
  ```

### **Manual Method:**
- [ ] **Update system**: `apt update && apt upgrade -y`
- [ ] **Install dependencies**: `apt install -y python3 python3-pip python3-venv git nginx`
- [ ] **Add domain**: `v-add-web-domain admin converter.konsulence.al`
- [ ] **Enable SSL**: `v-add-letsencrypt-domain admin converter.konsulence.al`
- [ ] **Clone repo**:
  ```bash
  cd /tmp
  git clone https://github.com/Xhelo-hub/bank-select-converter.git
  ```
- [ ] **Deploy files**:
  ```bash
  WEB_DIR="/home/admin/web/converter.konsulence.al/public_html"
  mkdir -p $WEB_DIR
  cp -r /tmp/bank-select-converter/* $WEB_DIR/
  chown -R admin:admin $WEB_DIR
  ```
- [ ] **Setup Python**:
  ```bash
  cd $WEB_DIR/Bank_Specific_Converter
  sudo -u admin python3 -m venv venv
  sudo -u admin ./venv/bin/pip install flask gunicorn pandas openpyxl
  ```
- [ ] **Create systemd service** (see DEPLOY_FROM_GITHUB.md)
- [ ] **Start services**:
  ```bash
  systemctl enable bank-converter
  systemctl start bank-converter
  systemctl reload nginx
  ```

---

## **Phase 4: Verification (5 minutes)**

- [ ] **Check services**:
  ```bash
  systemctl status bank-converter
  systemctl status nginx
  ```
- [ ] **Test local**: `curl -I http://127.0.0.1:8000/server-status`
- [ ] **Test domain**: `curl -I https://converter.konsulence.al`
- [ ] **Visit website**: `https://converter.konsulence.al`
- [ ] **Test upload**: Upload a bank statement file
- [ ] **Test conversion**: Verify file converts correctly
- [ ] **Test auto-delete**: Confirm files are deleted after download

---

## **Management Commands**

### **Status Check**
```bash
# Service status
systemctl status bank-converter nginx

# Application logs
journalctl -u bank-converter -f

# Check files
ls -la /home/admin/web/converter.konsulence.al/public_html/Bank_Specific_Converter/
```

### **Update from GitHub**
```bash
cd /tmp
rm -rf bank-select-converter
git clone https://github.com/Xhelo-hub/bank-select-converter.git
cp -r bank-select-converter/* /home/admin/web/converter.konsulence.al/public_html/
chown -R admin:admin /home/admin/web/converter.konsulence.al/public_html/
systemctl restart bank-converter
```

### **Restart Services**
```bash
systemctl restart bank-converter
systemctl reload nginx
```

---

## **Success Criteria**

✅ **All Systems Go:**
- DNS resolves: `converter.konsulence.al` → `78.46.201.151`
- SSL works: Green padlock in browser
- Website loads: Bank converter interface visible
- Upload works: Can select bank and upload file
- Conversion works: QBO file downloads correctly
- Auto-delete works: No files remain on server
- Service stable: `systemctl status bank-converter` shows `active (running)`

---

## **Next Steps After Deployment**

1. **🔒 Security**: Change default passwords, setup firewall
2. **📊 Monitoring**: Setup log rotation, monitoring alerts  
3. **🔄 Backup**: Configure automated backups
4. **📈 Performance**: Monitor resource usage
5. **🛡️ Updates**: Regular system and app updates

---

**⏱️ Total Time**: 20-30 minutes  
**🎯 End Result**: `https://converter.konsulence.al` running your bank converter!

**Need help?** Check logs with: `journalctl -u bank-converter -f`