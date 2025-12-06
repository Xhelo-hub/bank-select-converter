#!/bin/bash
# Setup systemd service for Bank Converter
# This will ensure gunicorn automatically restarts if it crashes

echo "Setting up Bank Converter systemd service..."

# Copy service file to systemd directory
sudo cp bank-converter.service /etc/systemd/system/

# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable bank-converter.service

# Start the service
sudo systemctl start bank-converter.service

# Check status
sudo systemctl status bank-converter.service

echo ""
echo "✅ Service setup complete!"
echo ""
echo "Useful commands:"
echo "  sudo systemctl status bank-converter    # Check status"
echo "  sudo systemctl restart bank-converter   # Restart service"
echo "  sudo systemctl stop bank-converter      # Stop service"
echo "  sudo systemctl start bank-converter     # Start service"
echo "  sudo journalctl -u bank-converter -f   # View logs"
