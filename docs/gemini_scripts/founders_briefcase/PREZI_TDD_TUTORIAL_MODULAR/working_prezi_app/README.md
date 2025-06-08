# PrezI - AI-Powered Presentation Management System

## 🚀 **CAN THE APP RUN NOW? YES!** 

This PrezI application is **fully functional** and ready to run on Windows. Students can run it right now following the instructions below.

## 📋 Prerequisites for Windows Students

1. **Python 3.9+** - Download from https://www.python.org/downloads/
2. **Node.js 16.0+** - Download from https://nodejs.org/
3. **OpenAI API Key** - Get from https://platform.openai.com/api-keys
4. **Microsoft PowerPoint** (optional, for PowerPoint integration)

## 🚀 **3-Step Setup for Students**

### Step 1: Install Dependencies
```cmd
# Navigate to the project folder
cd working_prezi_app

# Install Python packages
pip install -r requirements.txt

# Install Node.js packages  
npm install
```

### Step 2: Configure Environment
```cmd
# Create environment file
echo OPENAI_API_KEY=your_api_key_here > .env
echo DATABASE_URL=sqlite:///prezi.db >> .env
echo ENVIRONMENT=development >> .env
```
**Replace `your_api_key_here` with your actual OpenAI API key**

### Step 3: Run the Application
```cmd
# Start the complete application (backend + desktop app)
npm run dev
```

**That's it!** The PrezI desktop application will launch automatically.

## ✅ **What Students Can Do Right Now**

Once running, students can immediately:

1. **✅ Create Projects** - Organize presentation files
2. **✅ Import PowerPoint Files** - Upload .pptx files (if PowerPoint installed)
3. **✅ Browse Slide Library** - View imported slides with thumbnails
4. **✅ Use AI Search** - Search slides with natural language
5. **✅ Manage Keywords** - Tag and categorize slides
6. **✅ Build Assemblies** - Drag-and-drop presentation building
7. **✅ Chat with PrezI** - AI assistant for help and suggestions
8. **✅ Export Presentations** - Save as PowerPoint or PDF
9. **✅ Real-time Updates** - Live progress tracking

## 🌐 **Alternative: Backend-Only Mode**

If you only want to test the API:

```cmd
# Run just the backend server
cd backend
python main.py
```

Then visit:
- **API Server**: http://127.0.0.1:8765
- **Interactive API Docs**: http://127.0.0.1:8765/docs  
- **Health Check**: http://127.0.0.1:8765/api/v1/health

## 📁 Project Structure

```
working_prezi_app/
├── backend/           # Python FastAPI backend
├── frontend/          # HTML/CSS/JS frontend  
├── electron/          # Electron desktop wrapper
├── docs/             # Documentation
├── tests/            # Test suites
└── scripts/          # Build and utility scripts
```

## 🏗️ Architecture

This application demonstrates:
- **FastAPI** REST API with SQLAlchemy ORM
- **SQLite** database with FTS5 search
- **PowerPoint COM** automation (Windows)
- **OpenAI API** integration for AI features
- **HTML/CSS/JavaScript** frontend with design system
- **Electron** desktop application wrapper

## 📚 Tutorial Reference

This working application serves as the **golden standard** for students following the TDD tutorial. Every feature built in the tutorial modules is demonstrated here in working form.

## 🔧 Development

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed development instructions.

## 📖 Documentation

- [API Documentation](docs/API.md)
- [Database Schema](docs/DATABASE.md)
- [Frontend Guide](docs/FRONTEND.md)
- [Deployment Guide](docs/DEPLOYMENT.md)