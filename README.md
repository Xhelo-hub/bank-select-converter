# 🏦 Bank Select Converter

A comprehensive web-based Albanian bank statement converter that transforms bank statements into QuickBooks-compatible formats. Features bank-specific converters for accurate processing and automatic file cleanup for privacy.

## ✨ Features

- **🎯 Bank-Specific Processing**: Individual converters for each Albanian bank
- **🌐 Web Interface**: Modern, responsive web application
- **🔒 Privacy-First**: Automatic file deletion after download
- **📁 Simple Structure**: Import/Export folders with flat file organization
- **🧹 Auto-Cleanup**: Periodic cleanup of temporary files
- **🚀 Production Ready**: HestiaCP deployment configuration included
- **📱 Mobile Friendly**: Responsive design works on all devices

## 🏛️ Supported Banks

- **BKT Bank** (PDF, CSV)
- **OTP Bank** (PDF, CSV) 
- **Raiffeisen Bank** (PDF, CSV)
- **TI Bank** (PDF, CSV)
- **Union Bank** (PDF, CSV)
- **E-Bills** (PDF)

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/bank-select-converter.git
   cd bank-select-converter
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the web interface**
   ```bash
   cd Bank_Specific_Converter
   python app.py
   ```

5. **Access the application**
   Open your browser and go to `http://127.0.0.1:5002`

## 🌐 Production Deployment

### HestiaCP Deployment

The project includes complete HestiaCP deployment configuration:

1. **Upload files** to your domain's public_html
2. **Follow the deployment guide** in `HESTIA_DEPLOYMENT.md`
3. **Use the deployment scripts** in `Bank_Specific_Converter/`

Quick deployment options:
- **Option 1**: HestiaCP Python App (Recommended)
- **Option 2**: Manual Gunicorn setup
- **Option 3**: Automated deployment script

## 📁 Project Structure

```
bank-select-converter/
├── Bank_Specific_Converter/     # Main web application
│   ├── app.py                   # Flask web interface
│   ├── wsgi.py                  # Production WSGI entry point
│   ├── config.py               # Configuration settings
│   ├── requirements.txt        # Dependencies
│   ├── deploy.sh              # Deployment script
│   ├── start.sh               # Production startup
│   ├── stop.sh                # Stop application
│   ├── restart.sh             # Restart application
│   └── HESTIA_DEPLOYMENT.md   # Deployment guide
├── Individual Converters/       # Bank-specific scripts
│   ├── BKT-2-QBO.py           # BKT Bank converter
│   ├── RAI-2-QBO.py           # Raiffeisen converter
│   ├── OTP-2-QBO.py           # OTP Bank converter
│   ├── TIBANK-2-QBO.py        # TI Bank converter
│   ├── UNION-2-QBO.py         # Union Bank converter
│   └── Withholding.py         # E-Bills converter
└── Legacy/                     # Previous versions
    └── Web_Based_Bank_Statement_Converter/
```

## 🔧 Configuration

### Environment Variables
```bash
FLASK_ENV=production              # Set to 'development' for debug mode
SECRET_KEY=your-secret-key       # Change for production
```

### File Structure
- **Import folder**: `import/` - Temporary uploaded files
- **Export folder**: `export/` - Temporary converted files
- **Auto-cleanup**: Files deleted after download + periodic cleanup

## 🛡️ Privacy & Security

- **🗑️ Auto-delete**: Files automatically deleted after download
- **⏰ Periodic cleanup**: Old files removed every 30 minutes  
- **🔒 No persistence**: No permanent file storage
- **🛡️ Secure headers**: Security headers configured
- **🔐 Environment-based config**: Secure configuration management

## 🔄 How It Works

1. **Upload**: User selects bank and uploads statement file
2. **Process**: Bank-specific converter processes the file
3. **Convert**: Statement converted to QuickBooks format
4. **Download**: User downloads converted file
5. **Cleanup**: Both original and converted files auto-deleted

## 📊 Monitoring

### Status Endpoints
- `/server-status` - Server storage and status info
- `/cleanup` - Manual cleanup trigger
- `/api/info` - Application information

### Features
- Real-time file count monitoring
- Background cleanup status
- Memory usage tracking
- Job processing statistics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 **Documentation**: Check the `HESTIA_DEPLOYMENT.md` for detailed setup
- 🐛 **Issues**: Report bugs via GitHub Issues
- 💬 **Questions**: Use GitHub Discussions

## 🚀 Roadmap

- [ ] Additional bank support
- [ ] PDF parsing improvements  
- [ ] Bulk file processing
- [ ] API endpoints for integration
- [ ] Docker deployment option
- [ ] Multi-language support

---

**Built with ❤️ for Albanian businesses to simplify their accounting workflows**