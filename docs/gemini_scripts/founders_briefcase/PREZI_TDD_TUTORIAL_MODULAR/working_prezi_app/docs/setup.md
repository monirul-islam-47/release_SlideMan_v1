# PrezI Setup Guide

Complete step-by-step setup instructions for the PrezI application.

## System Requirements

### Minimum Requirements
- **Operating System:** Windows 10, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python:** 3.9 or higher
- **Node.js:** 16.0 or higher
- **RAM:** 4GB minimum, 8GB recommended
- **Storage:** 2GB free space

### Recommended for Full Features
- **Windows 10/11** (for PowerPoint COM automation)
- **Microsoft PowerPoint** (2016 or later)
- **OpenAI API Key** (for AI features)
- **8GB+ RAM** (for processing large presentations)

## Installation Steps

### 1. Clone Repository
```bash
git clone <repository-url>
cd working_prezi_app
```

### 2. Python Environment Setup

#### Windows
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

#### macOS/Linux
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 3. Node.js Setup
```bash
# Install Node.js dependencies
npm install

# Verify installation
npm list
```

### 4. Environment Configuration

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file with your settings:**
   ```bash
   # Required: OpenAI API Key for AI features
   OPENAI_API_KEY=sk-your-api-key-here
   
   # Optional: Customize other settings
   DEBUG=true
   PORT=8000
   ```

3. **Get OpenAI API Key:**
   - Go to [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create account or sign in
   - Generate new API key
   - Add billing information (required for API usage)

### 5. Database Setup

The application uses SQLite (no additional setup required):
```bash
# Database will be created automatically on first run
# Location: ./prezi_app.db
```

## Running the Application

### Development Mode
```bash
# Start both backend and frontend with hot reload
npm run dev
```

### Production Mode
```bash
# Start as Electron desktop application
npm run electron
```

### Manual Startup
```bash
# Terminal 1: Start backend
python backend/main.py

# Terminal 2: Start frontend (in another terminal)
cd frontend
python -m http.server 3000

# Terminal 3: Start Electron (in another terminal)
npm run electron
```

## Verification & Testing

### 1. Health Check
Visit `http://localhost:8000/api/v1/health` to verify backend is running.

### 2. Frontend Check
Visit `http://localhost:3000` to verify frontend is accessible.

### 3. Feature Testing
1. **Create Project** - Test project creation
2. **Import Slides** - Upload a PowerPoint file
3. **AI Features** - Try search with OpenAI API key
4. **Export** - Test presentation export

### 4. Run Test Suite
```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
npm test

# End-to-end tests
npm run test:e2e
```

## Troubleshooting

### Common Issues

#### 1. Python Virtual Environment Issues
```bash
# If venv activation fails
python -m pip install --user virtualenv
python -m virtualenv venv

# If Python not found
which python3
# Use full path if needed
```

#### 2. Node.js Dependency Issues
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules
npm install

# Use specific Node.js version
nvm use 16  # if using nvm
```

#### 3. PowerPoint COM Issues (Windows)
```bash
# Run as administrator
# Right-click command prompt -> "Run as administrator"

# Verify PowerPoint installation
powershell "Get-WmiObject -Class Win32_Product | Where-Object Name -like '*PowerPoint*'"

# Register PowerPoint COM objects
regsvr32 "C:\Program Files\Microsoft Office\root\Office16\PPTVIEW.DLL"
```

#### 4. OpenAI API Issues
- **Invalid API Key:** Check key format (starts with `sk-`)
- **Quota Exceeded:** Check billing in OpenAI dashboard
- **Rate Limits:** Wait a few minutes and retry
- **Network Issues:** Check firewall/proxy settings

#### 5. Database Issues
```bash
# Reset database
rm prezi_app.db

# Check permissions
ls -la prezi_app.db

# Manual database creation
python -c "from backend.database.database import init_app_database; init_app_database()"
```

#### 6. Port Conflicts
```bash
# Check what's using port 8000
netstat -tulpn | grep 8000  # Linux/macOS
netstat -ano | findstr 8000  # Windows

# Use different port
PORT=8001 python backend/main.py
```

### Log Analysis

#### Backend Logs
```bash
# Enable debug logging
export DEBUG=true  # Linux/macOS
set DEBUG=true     # Windows

# View logs
python backend/main.py
```

#### Frontend Logs
- Open browser Developer Tools (F12)
- Check Console tab for JavaScript errors
- Check Network tab for API request failures

## Platform-Specific Notes

### Windows
- **PowerPoint COM:** Full slide processing available
- **File Paths:** Use backslashes in paths
- **Admin Rights:** May be required for COM registration

### macOS
- **PowerPoint COM:** Not available, uses python-pptx fallback
- **Permissions:** May need to allow app in Security & Privacy
- **Python:** Use `python3` explicitly

### Linux
- **PowerPoint COM:** Not available, uses python-pptx fallback
- **Dependencies:** May need additional system packages:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install python3-venv python3-pip nodejs npm
  
  # CentOS/RHEL
  sudo yum install python3-venv python3-pip nodejs npm
  ```

## Performance Optimization

### System Optimization
```bash
# Increase file upload limits
MAX_FILE_SIZE=209715200  # 200MB

# Optimize worker threads
WORKER_THREADS=8  # Set to CPU core count

# Increase cache sizes
CACHE_SIZE=2000
THUMBNAIL_CACHE_SIZE=1000
```

### Database Optimization
```bash
# Enable WAL mode (default)
# Increase cache size in production
DATABASE_POOL_SIZE=10
```

### Memory Management
- Close unused browser tabs
- Restart application if memory usage high
- Use task manager to monitor resource usage

## Security Considerations

### API Key Security
- Never commit `.env` files to version control
- Use environment variables in production
- Rotate API keys regularly

### Network Security
- Use HTTPS in production
- Configure CORS origins properly
- Implement rate limiting

### File Security
- Validate uploaded file types
- Scan files for malware in production
- Limit file sizes appropriately

## Production Deployment

### Environment Variables
```bash
# Production settings
DEBUG=false
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:pass@host:port/db  # if using PostgreSQL
```

### Process Management
```bash
# Use process manager like PM2
npm install -g pm2
pm2 start ecosystem.config.js
```

### Monitoring
- Set up health check endpoints
- Monitor API response times
- Track error rates and user metrics

## Getting Help

### Documentation
- **API Docs:** Available at `/docs` in development mode
- **Architecture:** See `docs/architecture.md`
- **Features:** See `docs/features.md`

### Support Channels
- **GitHub Issues:** For bug reports and feature requests
- **Documentation:** Check existing docs first
- **Logs:** Always include relevant log output

### Debugging Steps
1. Check all services are running
2. Verify environment variables
3. Test API endpoints manually
4. Check browser console for errors
5. Review application logs
6. Test with minimal configuration

## Next Steps

After successful setup:
1. **Explore Features** - Try all major functionality
2. **Import Data** - Upload your PowerPoint files
3. **Configure AI** - Set up OpenAI integration
4. **Customize Settings** - Adjust preferences
5. **Learn Shortcuts** - Master keyboard shortcuts
6. **Read Documentation** - Understand advanced features

---

*For additional help, see the troubleshooting section or contact support.*