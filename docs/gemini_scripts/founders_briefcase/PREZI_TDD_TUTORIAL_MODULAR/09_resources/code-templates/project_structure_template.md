# 📁 PrezI Project Structure Template
## *Complete folder structure for your TDD capstone project*

```
prezi_app/
├── README.md                           # Project overview and setup instructions
├── requirements.txt                    # Python dependencies
├── package.json                        # Node.js dependencies (for Electron)
├── main.js                            # Electron entry point
├── pytest.ini                        # Pytest configuration
├── .gitignore                         # Git ignore patterns
├── .github/
│   └── workflows/
│       ├── ci.yml                     # Continuous Integration pipeline
│       └── cd.yml                     # Continuous Deployment pipeline
│
├── docs/                              # Project documentation
│   ├── api/                          # API documentation
│   ├── architecture/                 # Architecture diagrams and docs
│   └── user-guide/                   # User documentation
│
├── backend/                           # Python backend (FastAPI)
│   ├── main.py                       # FastAPI application entry point
│   ├── config.py                     # Configuration management
│   ├── requirements.txt              # Backend-specific dependencies
│   │
│   ├── api/                          # API layer
│   │   ├── __init__.py
│   │   ├── dependencies.py           # FastAPI dependencies
│   │   └── v1/                       # API version 1
│   │       ├── __init__.py
│   │       ├── projects.py           # Project endpoints
│   │       ├── slides.py             # Slide endpoints
│   │       ├── keywords.py           # Keyword endpoints
│   │       └── assemblies.py         # Assembly endpoints
│   │
│   ├── core/                         # Business logic and services
│   │   ├── __init__.py
│   │   ├── models/                   # Data models
│   │   │   ├── __init__.py
│   │   │   ├── project.py
│   │   │   ├── slide.py
│   │   │   ├── keyword.py
│   │   │   └── assembly.py
│   │   │
│   │   ├── services/                 # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── project_service.py
│   │   │   ├── slide_service.py
│   │   │   ├── powerpoint_service.py
│   │   │   ├── ai_service.py
│   │   │   └── export_service.py
│   │   │
│   │   └── schemas/                  # Pydantic schemas for API
│   │       ├── __init__.py
│   │       ├── project_schemas.py
│   │       ├── slide_schemas.py
│   │       └── assembly_schemas.py
│   │
│   ├── database/                     # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py             # Database connection management
│   │   ├── migrations/               # Database migration scripts
│   │   └── repositories/             # Repository pattern implementation
│   │       ├── __init__.py
│   │       ├── base_repository.py
│   │       ├── project_repository.py
│   │       └── slide_repository.py
│   │
│   └── utils/                        # Utility functions
│       ├── __init__.py
│       ├── logging.py                # Logging configuration
│       ├── security.py               # Security utilities
│       └── validators.py             # Data validation utilities
│
├── frontend/                         # Frontend (HTML/CSS/JavaScript)
│   ├── index.html                    # Main application page
│   ├── styles/                       # CSS stylesheets
│   │   ├── main.css                  # Main stylesheet
│   │   ├── components/               # Component-specific styles
│   │   └── themes/                   # Theme variations
│   │
│   ├── scripts/                      # JavaScript modules
│   │   ├── main.js                   # Main application script
│   │   ├── api/                      # API communication
│   │   ├── components/               # UI components
│   │   ├── services/                 # Frontend services
│   │   └── utils/                    # Frontend utilities
│   │
│   └── assets/                       # Static assets
│       ├── images/                   # Image files
│       ├── icons/                    # Icon files
│       └── fonts/                    # Font files
│
├── tests/                            # Test suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest configuration and fixtures
│   │
│   ├── unit/                         # Unit tests
│   │   ├── __init__.py
│   │   ├── models/                   # Model tests
│   │   ├── services/                 # Service tests
│   │   └── repositories/             # Repository tests
│   │
│   ├── integration/                  # Integration tests
│   │   ├── __init__.py
│   │   ├── api/                      # API integration tests
│   │   └── database/                 # Database integration tests
│   │
│   ├── e2e/                          # End-to-end tests
│   │   ├── __init__.py
│   │   ├── test_complete_workflow.py
│   │   └── test_user_journeys.py
│   │
│   └── fixtures/                     # Test data and fixtures
│       ├── sample_presentations/
│       └── test_data.json
│
├── scripts/                          # Development and deployment scripts
│   ├── setup.py                      # Environment setup
│   ├── build.py                      # Build automation
│   ├── deploy.py                     # Deployment automation
│   └── test.py                       # Test runner scripts
│
└── dist/                             # Distribution files (generated)
    ├── win/                          # Windows distributables
    ├── mac/                          # macOS distributables
    └── linux/                        # Linux distributables
```

## 📝 Key Files Explained

### Configuration Files
- **`requirements.txt`**: Python package dependencies
- **`package.json`**: Node.js dependencies for Electron
- **`pytest.ini`**: Test configuration and options
- **`.gitignore`**: Files and folders to exclude from version control

### Entry Points
- **`main.js`**: Electron application entry point
- **`backend/main.py`**: FastAPI server entry point
- **`frontend/index.html`**: Main web application page

### Core Architecture
- **`backend/core/models/`**: Data models defining the domain
- **`backend/core/services/`**: Business logic and operations
- **`backend/database/repositories/`**: Data access layer
- **`backend/api/v1/`**: REST API endpoints

### Testing Structure
- **`tests/unit/`**: Fast, isolated tests for individual components
- **`tests/integration/`**: Tests for component interactions
- **`tests/e2e/`**: Complete user workflow tests

### Development Tools
- **`.github/workflows/`**: CI/CD pipeline definitions
- **`scripts/`**: Automation scripts for development tasks
- **`docs/`**: Project documentation and guides

## 🚀 Getting Started

1. **Create the folder structure** using this template
2. **Initialize Git repository** in the root directory
3. **Set up virtual environment** for Python dependencies
4. **Install dependencies** from requirements files
5. **Run initial tests** to verify setup

## 📋 Folder Creation Commands

```bash
# Create the complete folder structure
mkdir -p prezi_app/{docs/{api,architecture,user-guide},backend/{api/v1,core/{models,services,schemas},database/{migrations,repositories},utils},frontend/{styles/{components,themes},scripts/{api,components,services,utils},assets/{images,icons,fonts}},tests/{unit/{models,services,repositories},integration/{api,database},e2e,fixtures/sample_presentations},scripts,dist/{win,mac,linux},.github/workflows}

# Navigate to project root
cd prezi_app

# Initialize Git repository
git init

# Create initial files
touch README.md requirements.txt package.json main.js pytest.ini .gitignore
touch backend/main.py backend/config.py
touch frontend/index.html
touch tests/conftest.py
```

This structure supports the complete PrezI application development with proper separation of concerns and professional organization.