# PD Software Deployment Guide

## Prerequisites

### System Requirements
- **OS**: Windows 10+, macOS 10.14+, or Linux Ubuntu 18.04+
- **CPU**: Intel i5 or AMD Ryzen 5 (minimum)
- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: NVIDIA GTX 1060+ / AMD RX 580+ / Intel UHD 630+ (optional but recommended)
- **Network**: Gigabit ethernet recommended

### Software Dependencies
- **Python**: 3.8 or higher
- **FFmpeg**: 4.4 or higher with GPU support
- **MediaMTX**: Latest version
- **NDI SDK**: NewTek NDI SDK 5.0+

## Installation Steps

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
```
PyQt6>=6.4.0
psutil>=5.8.0
numpy>=1.21.0
pillow>=8.3.0
```

### 2. Install FFmpeg with GPU Support

#### Windows
```bash
# Download from https://ffmpeg.org/download.html
# Or use chocolatey
choco install ffmpeg
```

#### macOS
```bash
brew install ffmpeg
```

#### Linux
```bash
sudo apt update
sudo apt install ffmpeg
```

### 3. Setup MediaMTX Server

#### Download and Configure
```bash
# Download MediaMTX
wget https://github.com/bluenviron/mediamtx/releases/latest/download/mediamtx_linux_amd64.tar.gz
tar -xzf mediamtx_linux_amd64.tar.gz

# Copy optimized configuration
cp mediamtx-optimized.yml mediamtx.yml

# Start MediaMTX
./mediamtx
```

#### Configuration Verification
```bash
# Test SRT endpoint
ffmpeg -re -i test.mp4 -c copy -f mpegts srt://localhost:8890?streamid=test

# Test playback
ffplay srt://localhost:8890?streamid=test
```

### 4. Install NDI SDK

#### Download NDI SDK
1. Visit https://ndi.tv/sdk/
2. Download NDI SDK for your platform
3. Install according to platform instructions

#### Verify NDI Installation
```bash
# Check NDI tools work
NDI Studio Monitor
NDI Scan Converter
```

### 5. GPU Driver Setup

#### NVIDIA
```bash
# Install NVIDIA drivers
sudo apt install nvidia-driver-470
nvidia-smi  # Verify installation
```

#### AMD
```bash
# Install AMD drivers
sudo apt install amdgpu-pro
```

#### Intel
```bash
# Install Intel GPU drivers
sudo apt install intel-media-driver
```

## Configuration

### 1. MediaMTX Configuration

Edit `mediamtx.yml`:
```yaml
# SRT Configuration
srtMaxBandwidth: 15000000   # 15 Mbps
srtRecvBuf: 16777216        # 16 MB
srtLatency: 120             # 120ms base latency

# Authentication
authMethod: internal
authInternalUsers:
  - user: "pd_user"
    pass: "secure_password"
    ips: ["127.0.0.1", "192.168.1.0/24"]
```

### 2. Environment Variables

Create `.env` file:
```bash
# MediaMTX Configuration
MEDIAMTX_SERVER=localhost
MEDIAMTX_SRT_PORT=8890
MEDIAMTX_API_PORT=9997

# Authentication
PD_AUTH_USER=pd_user
PD_AUTH_PASS=secure_password

# GPU Configuration
PREFERRED_GPU_ENCODER=auto  # auto, nvenc, qsv, amf, cpu
```

### 3. Network Configuration

#### Firewall Rules
```bash
# Allow SRT port
sudo ufw allow 8890/udp

# Allow MediaMTX API
sudo ufw allow 9997/tcp
```

#### Network Optimization
```bash
# Increase UDP buffer sizes
echo 'net.core.rmem_max = 268435456' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 268435456' >> /etc/sysctl.conf
sysctl -p
```

## Running the Application

### 1. Start MediaMTX Server
```bash
./mediamtx &
```

### 2. Run PD Software
```bash
# Basic demo
python demo_complete_integration.py

# Resource optimization demo
python demo_resource_optimization.py

# Run tests
python test_integration.py
```

### 3. Verify Streaming

#### Check MediaMTX Status
```bash
curl http://localhost:9997/v3/config/global
```

#### Test SRT Stream
```bash
# Test with FFmpeg
ffmpeg -re -f lavfi -i testsrc=size=1920x1080:rate=30 \
    -c:v libx264 -preset ultrafast -tune zerolatency \
    -b:v 5M -f mpegts srt://localhost:8890?streamid=test
```

## Troubleshooting

### Common Issues

#### 1. GPU Not Detected
```bash
# Check GPU support
ffmpeg -encoders | grep nvenc
ffmpeg -encoders | grep qsv
ffmpeg -encoders | grep amf

# Verify drivers
nvidia-smi          # NVIDIA
intel_gpu_top       # Intel
radeontop           # AMD
```

#### 2. NDI Sources Not Found
```bash
# Check NDI network
ndi-directory-service --list

# Verify multicast
ping 239.255.255.250
```

#### 3. SRT Connection Failed
```bash
# Check MediaMTX logs
tail -f mediamtx.log

# Test SRT manually
srt-live-transmit file://test.ts srt://localhost:8890?streamid=test
```

#### 4. High CPU Usage
```bash
# Enable GPU acceleration
export CUDA_VISIBLE_DEVICES=0  # NVIDIA
export LIBVA_DRIVER_NAME=i965   # Intel
export AMDGPU_CIK_SUPPORT=1     # AMD

# Check resource usage
htop
nvidia-smi
```

### Performance Optimization

#### 1. GPU Acceleration
```bash
# NVIDIA optimization
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_VISIBLE_DEVICES=0

# Intel optimization
export LIBVA_DRIVER_NAME=i965
export INTEL_MEDIA_RUNTIME=1

# AMD optimization
export AMDGPU_CIK_SUPPORT=1
export AMDGPU_SI_SUPPORT=1
```

#### 2. Network Optimization
```bash
# Increase network buffers
echo 'net.core.netdev_max_backlog = 5000' >> /etc/sysctl.conf
echo 'net.core.rmem_default = 262144' >> /etc/sysctl.conf
echo 'net.core.wmem_default = 262144' >> /etc/sysctl.conf
```

#### 3. System Tuning
```bash
# Real-time scheduling
echo '@audio - rtprio 99' >> /etc/security/limits.conf
echo '@video - rtprio 99' >> /etc/security/limits.conf

# CPU governor
echo performance > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

## Monitoring and Maintenance

### 1. Log Files
```bash
# Application logs
tail -f pd_software.log

# MediaMTX logs
tail -f mediamtx.log

# System logs
journalctl -u pd-software -f
```

### 2. Performance Monitoring
```bash
# Resource usage
htop
iotop
nethogs

# GPU monitoring
nvidia-smi -l 1     # NVIDIA
intel_gpu_top       # Intel
radeontop           # AMD
```

### 3. Health Checks
```bash
# Check services
systemctl status pd-software
systemctl status mediamtx

# Check network
ss -tulpn | grep :8890
ss -tulpn | grep :9997

# Check GPU
nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader
```

## Production Deployment

### 1. Service Configuration

Create `pd-software.service`:
```ini
[Unit]
Description=PD Software Professional
After=network.target

[Service]
Type=simple
User=pd-software
WorkingDirectory=/opt/pd-software
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Auto-start Configuration
```bash
# Install service
sudo cp pd-software.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pd-software
sudo systemctl start pd-software
```

### 3. Backup and Recovery
```bash
# Backup configuration
tar -czf pd-software-backup.tar.gz \
    mediamtx.yml \
    .env \
    pd_app/

# Restore configuration
tar -xzf pd-software-backup.tar.gz
```

## Security Considerations

### 1. Authentication
- Use strong passwords for MediaMTX
- Enable TLS encryption for API
- Restrict IP access ranges

### 2. Network Security
- Use VPN for remote access
- Enable firewall rules
- Monitor network traffic

### 3. System Security
- Run with minimal privileges
- Regular security updates
- Monitor system logs

## Support and Maintenance

### 1. Regular Updates
```bash
# Update PD Software
git pull origin main
pip install -r requirements.txt

# Update MediaMTX
wget https://github.com/bluenviron/mediamtx/releases/latest/download/mediamtx_linux_amd64.tar.gz
```

### 2. Performance Monitoring
- Monitor CPU/GPU usage
- Check network latency
- Validate stream quality

### 3. Backup Strategy
- Daily configuration backup
- Weekly system backup
- Test restore procedures

---

**PD Software v1.0 Deployment Guide**  
*Professional Broadcasting Made Simple*  
© 2025 ReturnFeed. All rights reserved.