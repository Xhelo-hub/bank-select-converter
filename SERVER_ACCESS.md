# 🚀 Your Server Access Information

## 🖥️ **Server Details**
- **Server IP**: `78.46.201.151`
- **HestiaCP Panel**: `http://78.46.201.151:8083` (⚠️ HTTP - needs SSL)
- **SSH Access**: `ssh root@78.46.201.151`

---

## 🔒 **HestiaCP Access (Current Status)**

### **Current URL** (Not Secure):
```
http://78.46.201.151:8083/login
```

### **🎯 Immediate Steps to Secure HestiaCP:**

#### **Step 1: Access HestiaCP (temporarily via HTTP)**
1. Go to: `http://78.46.201.151:8083/login`
2. **Accept security warning** in browser
3. **Login** with your credentials

#### **Step 2: Enable SSL Certificate**
Once logged in:
1. **Go to**: Server → Configure → SSL Certificate
2. **Enable SSL** for HestiaCP interface
3. **Save changes**

#### **Step 3: Alternative - SSH Method (Recommended)**
```bash
# SSH into your server
ssh root@78.46.201.151

# Enable SSL for HestiaCP
v-add-letsencrypt-host

# Restart HestiaCP service
systemctl restart hestia

# Check if SSL is working
curl -I https://78.46.201.151:8083
```

#### **Step 4: Access Securely**
After enabling SSL, use:
```
https://78.46.201.151:8083/login
```

---

## 🏦 **Bank Converter Deployment Ready**

### **Cloudflare DNS Configuration**
When ready to deploy your bank converter:

1. **Create A Record**:
   ```
   Type: A
   Name: converter (or bank-converter)
   IPv4: 78.46.201.151
   Proxy: 🟠 Proxied
   ```

2. **Your app will be available at**:
   ```
   https://converter.konsulence.al
   ```

### **Quick Deployment Commands**
```bash
# SSH to your server
ssh root@78.46.201.151

# Clone your project
git clone https://github.com/Xhelo-hub/bank-select-converter.git

# Follow deployment guide
cd bank-select-converter
chmod +x DEPLOYMENT_GUIDE.md
```

---

## 🛠️ **Quick Server Commands**

```bash
# Connect to server
ssh root@78.46.201.151

# Check HestiaCP status
systemctl status hestia

# Restart HestiaCP if needed
systemctl restart hestia

# Check SSL certificate
openssl s_client -connect 78.46.201.151:8083 -servername 78.46.201.151

# View HestiaCP logs
tail -f /usr/local/hestia/log/system.log
```

---

## ⚡ **Next Steps for Bank Converter**

1. **✅ Secure HestiaCP** (enable HTTPS)
2. **🌐 Add domain to Cloudflare** 
3. **📋 Create A record**: `converter.yourdomain.com` → `78.46.201.151`
4. **🚀 Deploy bank converter** using deployment guide
5. **🎯 Test**: Upload bank statement and convert

---

## 🆘 **Troubleshooting**

### **Can't Access HestiaCP?**
```bash
# Check if HestiaCP is running
ssh root@78.46.201.151
systemctl status hestia

# Check if port 8083 is open
netstat -tlnp | grep :8083

# Reset HestiaCP if needed
systemctl restart hestia
```

### **Forgot Admin Password?**
```bash
# Reset admin password
ssh root@78.46.201.151
v-change-user-password admin NEW_PASSWORD
```

### **Still Getting Security Warnings?**
This is normal for self-signed certificates. Options:
1. **Accept the warning** and proceed
2. **Enable Let's Encrypt** for HestiaCP (recommended)
3. **Use a custom domain** for HestiaCP

**Your server is ready for deployment! 🎉**