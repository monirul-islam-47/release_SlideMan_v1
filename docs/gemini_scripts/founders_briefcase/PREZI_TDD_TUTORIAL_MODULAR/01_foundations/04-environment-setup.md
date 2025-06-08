# 🛠️ Module 4: Development Environment Setup
## *Build Your Professional Developer Toolkit*

**Module:** 04 | **Phase:** Foundations  
**Duration:** 3 hours | **Prerequisites:** Module 03  
**Learning Track:** Professional Development Environment Configuration  

---

## 🎯 Module Objectives

By completing this module, you will:
- [ ] Set up a complete professional development environment
- [ ] Configure Python backend with FastAPI and testing tools
- [ ] Set up frontend development tools and build system
- [ ] Create your first CI/CD pipeline with GitHub Actions
- [ ] Verify everything works with initial tests
- [ ] Establish professional project structure

---

## 🛠️ Building Your Developer Toolkit

Think of this like setting up a professional workshop. A carpenter needs the right tools to build beautiful furniture - you need the right tools to build beautiful software!

The goal is to create an environment where:
- **TDD is natural**: Testing tools are fast and easy to use
- **Quality is automatic**: Code formatting and linting happen seamlessly
- **Deployment is smooth**: CI/CD pipelines handle the heavy lifting
- **Collaboration works**: Everything is consistent across team members

---

## 📋 Prerequisites Checklist

Before we start building PrezI, let's ensure you have everything you need:

### Essential Tools
- [ ] **Python 3.9+** (Our backend language)
- [ ] **Node.js 16+** (For Electron and build tools)
- [ ] **Git** (Version control)
- [ ] **GitHub Account** (Code hosting and CI/CD)
- [ ] **VS Code** (Recommended editor)
- [ ] **PowerPoint** (For COM integration - Windows required)

### VS Code Extensions (Highly Recommended)
- [ ] Python extension pack
- [ ] GitLens (Supercharge your Git experience)
- [ ] Live Share (Pair programming)
- [ ] pytest extension
- [ ] GitHub Actions extension
- [ ] Thunder Client (API testing)

---

## 🏗️ Project Structure Setup

Let's create the PrezI project structure following professional standards:

```bash
# Create the main project directory
mkdir prezi_app
cd prezi_app

# Initialize Git repository
git init
git branch -M main

# Create professional project structure
mkdir -p backend/{api/v1,core/{models,services,schemas},database/{migrations,repositories},tests/{unit,integration,e2e},utils}
mkdir -p frontend/{styles,scripts,assets}
mkdir -p docs/.github/workflows

# Create essential files
touch README.md .gitignore
touch backend/requirements.txt backend/main.py backend/pytest.ini
touch frontend/index.html frontend/package.json
touch .github/workflows/ci.yml .github/workflows/cd.yml
```

---

## 🐍 Backend Setup (Python + FastAPI)

### Step 1: Create Virtual Environment
```bash
cd backend

# Create isolated Python environment (like having a clean workshop for each project)
python -m venv venv

# Activate the environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Verify activation (you should see (venv) in your prompt)
which python  # Should point to your venv
```

### Step 2: Install Dependencies
Create `backend/requirements.txt`:
```txt
# Core backend dependencies for PrezI
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
alembic==1.13.0

# PowerPoint integration (Windows only)
pywin32==306; platform_system=="Windows"

# OpenAI integration for AI features
openai==1.3.0
python-dotenv==1.0.0

# Testing framework
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2  # For testing HTTP requests

# Development and code quality
black==23.11.0
flake8==6.1.0
mypy==1.7.1
isort==5.12.0

# CI/CD and security
pytest-html==4.1.1  # For HTML test reports
bandit==1.7.5        # Security linting
safety==2.3.4        # Dependency security checks
```

Install everything:
```bash
pip install -r requirements.txt
```

### Step 3: Configure Testing
Create `backend/pytest.ini`:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --cov=.
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    windows_only: Tests that require Windows
```

---

## 🌐 Frontend Setup (HTML/CSS/JavaScript + Electron)

**Note**: We're using vanilla HTML/CSS/JavaScript (not React) as specified in the PrezI requirements!

### Step 1: Initialize Node.js Project
```bash
cd ../frontend

# Initialize Node.js project
npm init -y
```

### Step 2: Install Electron and Development Tools
Update `frontend/package.json`:
```json
{
  "name": "prezi-frontend",
  "version": "1.0.0",
  "description": "PrezI Frontend - AI-Powered Presentation Management",
  "main": "main.js",
  "scripts": {
    "electron": "electron main.js",
    "electron-dev": "electron main.js --dev",
    "build": "npm run build:css && npm run build:js",
    "build:css": "echo 'CSS build placeholder'",
    "build:js": "echo 'JS build placeholder'",
    "test": "jest",
    "test:watch": "jest --watch",
    "lint": "eslint scripts/**/*.js",
    "format": "prettier --write ."
  },
  "devDependencies": {
    "electron": "^27.0.0",
    "electron-builder": "^24.0.0",
    "jest": "^29.0.0",
    "eslint": "^8.0.0",
    "prettier": "^3.0.0",
    "@jest/environment-jsdom": "^29.0.0"
  },
  "build": {
    "appId": "com.yourname.prezi",
    "productName": "PrezI",
    "directories": {
      "output": "dist"
    },
    "files": [
      "**/*",
      "!node_modules",
      "!dist"
    ]
  }
}
```

Install dependencies:
```bash
npm install
```

### Step 3: Create Electron Main Process
Create `frontend/main.js`:
```javascript
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        },
        show: false
    });

    // Load the HTML file
    mainWindow.loadFile('index.html');

    // Show window when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // Open DevTools in development
    if (process.argv.includes('--dev')) {
        mainWindow.webContents.openDevTools();
    }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    }
});
```

---

## 🔧 Configuration Files

### `.gitignore` (Professional ignore patterns)
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/
.venv/
venv/
*.egg-info/

# Node.js
node_modules/
dist/
build/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Electron
out/
app/
release/

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/settings.json
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Database
*.db
*.sqlite3

# Secrets and API keys
secrets/
api_keys.txt

# PowerPoint files (for testing)
*.pptx
test_presentations/

# Build artifacts
*.exe
*.dmg
*.AppImage
```

### Backend Code Quality Configuration
Create `backend/.flake8`:
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    .venv,
    venv,
    migrations
```

Create `backend/pyproject.toml`:
```toml
[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

---

## 🚀 Your First CI/CD Pipeline

Create `.github/workflows/ci.yml`:

```yaml
name: 🧪 Continuous Integration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-backend:
    name: 🐍 Backend Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, "3.10", "3.11"]
    
    steps:
    - name: 📥 Checkout code
      uses: actions/checkout@v4
      
    - name: 🐍 Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
        
    - name: 📦 Install dependencies
      run: |
        cd backend
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        
    - name: 🧹 Lint with flake8
      run: |
        cd backend
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        
    - name: 🔒 Security check with bandit
      run: |
        cd backend
        bandit -r . -f json || true
        
    - name: 🧪 Run tests with pytest
      run: |
        cd backend
        pytest --cov=. --cov-report=xml
        
    - name: 📊 Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  test-frontend:
    name: ⚛️ Frontend Tests  
    runs-on: ubuntu-latest
    
    steps:
    - name: 📥 Checkout code
      uses: actions/checkout@v4
      
    - name: 📦 Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
        
    - name: 📦 Install dependencies
      run: |
        cd frontend
        npm ci
        
    - name: 🧹 Lint code
      run: |
        cd frontend
        npm run lint
        
    - name: 🧪 Run tests
      run: |
        cd frontend
        npm run test
        
    - name: 🏗️ Build application
      run: |
        cd frontend
        npm run build
```

---

## 🎯 Verify Your Setup

Let's make sure everything is working with simple tests:

### Backend Test
Create `backend/tests/test_setup.py`:
```python
"""Test that our development environment is properly configured."""
import sys
import pytest


def test_python_version():
    """Verify we're using a supported Python version."""
    assert sys.version_info >= (3, 9)


def test_imports():
    """Verify all critical dependencies can be imported."""
    import fastapi
    import pytest
    import sqlalchemy
    import pydantic
    # If this runs without errors, our environment is good!


def test_basic_math():
    """A simple test to verify pytest is working."""
    assert 2 + 2 == 4
    assert "hello" + " world" == "hello world"


@pytest.mark.unit
def test_tdd_cycle():
    """Verify we can run TDD cycles."""
    # This test demonstrates the TDD cycle
    # RED: This would fail if our function didn't exist
    result = add_numbers(3, 5)
    assert result == 8


def add_numbers(a: int, b: int) -> int:
    """Simple function to test TDD setup."""
    return a + b
```

Run the backend test:
```bash
cd backend
pytest tests/test_setup.py -v
```

### Frontend Test  
Create `frontend/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PrezI - AI-Powered Presentation Management</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #0a0a0a;
            color: #ffffff;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            text-align: center;
        }
        .success {
            background: linear-gradient(135deg, #667eea, #764ba2);
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 PrezI Development Environment</h1>
        <div class="success">
            <h2>✅ Environment Setup Complete!</h2>
            <p>Your PrezI development environment is ready for TDD and CI/CD.</p>
        </div>
        <div id="status">Loading...</div>
    </div>

    <script>
        // Simple test to verify JavaScript is working
        document.addEventListener('DOMContentLoaded', function() {
            const statusElement = document.getElementById('status');
            statusElement.innerHTML = '🚀 Frontend is ready for development!';
            
            // Test basic functionality
            console.log('✅ JavaScript is working');
            console.log('✅ DOM manipulation is working');
            console.log('✅ PrezI frontend environment is ready');
        });
    </script>
</body>
</html>
```

Test the Electron app:
```bash
cd frontend
npm run electron-dev
```

---

## 🔄 Complete Environment Verification

### Run All Tests
```bash
# Backend tests
cd backend
pytest -v

# Frontend Electron app
cd ../frontend  
npm run electron-dev  # Should open PrezI window

# Check CI pipeline locally (if you have act installed)
# act pull_request
```

### Test Your Git Workflow
```bash
# Add all files to Git
git add .
git commit -m "feat(setup): complete development environment configuration

- Add Python backend with FastAPI and testing setup
- Add Electron frontend with professional structure  
- Configure CI/CD pipeline with GitHub Actions
- Add comprehensive code quality tools"

# Create GitHub repository and push
git remote add origin https://github.com/yourusername/prezi-capstone.git
git push -u origin main
```

---

## 🚨 Troubleshooting Common Issues

### Python Issues
```bash
# Virtual environment not activating
# Make sure you're in the backend directory
cd backend
python -m venv venv --clear  # Recreate if needed

# Permission errors on Windows
# Run terminal as administrator or use:
python -m venv venv --without-pip
python -m ensurepip --default-pip
```

### Node.js Issues
```bash
# Clear npm cache if installation fails
npm cache clean --force
rm -rf node_modules package-lock.json
npm install

# Electron won't start
# Check Node.js version (should be 16+)
node --version
npm --version
```

### PowerPoint COM Issues (Windows)
```bash
# Install pywin32 specifically
pip install pywin32==306

# Configure pywin32 (may require admin)
python Scripts/pywin32_postinstall.py -install
```

---

## 🎓 Environment Best Practices

### 1. Keep It Consistent
- Use the same Python and Node.js versions across team
- Pin dependency versions in requirements files
- Use virtual environments for isolation

### 2. Automate Quality Checks
- Set up pre-commit hooks for formatting
- Run tests before every commit
- Use CI/CD to catch issues early

### 3. Document Everything
- Keep README.md updated with setup instructions
- Document any special configuration needed
- Include troubleshooting tips for common issues

---

## 🚀 What's Next?

In the next module, **Project Models TDD**, you'll:
- Start building PrezI's core data models
- Apply TDD to domain-driven design
- Create your first complete TDD cycles
- Build the foundation for the entire application

### Preparation for Next Module
- [ ] Verify all tools are installed and working
- [ ] Complete environment verification tests
- [ ] Push initial setup to GitHub
- [ ] Confirm CI/CD pipeline runs successfully

---

## ✅ Module 4 Completion Checklist

Before proceeding to the next module, ensure you can:
- [ ] Start Python backend with virtual environment
- [ ] Run pytest with code coverage
- [ ] Launch Electron desktop application
- [ ] Execute CI/CD pipeline on GitHub
- [ ] Use all development tools (linting, formatting, testing)
- [ ] Navigate the professional project structure
- [ ] Commit and push code with proper Git workflow

**Module Status:** ⬜ Complete | **Next Module:** [05-project-models-tdd.md](../02_backend/05-project-models-tdd.md)

---

## 💡 Pro Tips for Environment Management

### 1. Use Environment Variables
Create `.env` file for local configuration:
```bash
# Backend environment
OPENAI_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///prezi.db
LOG_LEVEL=DEBUG
```

### 2. Script Common Tasks
Create `scripts/dev.py`:
```python
#!/usr/bin/env python3
"""Development helper scripts."""
import subprocess
import sys

def run_tests():
    """Run all tests."""
    subprocess.run([sys.executable, "-m", "pytest", "-v"])

def run_backend():
    """Start backend server."""
    subprocess.run(["uvicorn", "main:app", "--reload"])

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "test":
            run_tests()
        elif command == "backend":
            run_backend()
```

### 3. Document Your Choices
Keep a `DECISIONS.md` file documenting why you chose specific tools and configurations. This helps future developers (including yourself) understand the reasoning behind your setup.