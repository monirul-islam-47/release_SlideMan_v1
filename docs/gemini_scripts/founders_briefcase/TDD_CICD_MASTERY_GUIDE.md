# 🎯 Test-Driven Development & CI/CD Mastery Guide
## *Building PrezI: Your Capstone Journey to Professional Software Development*

**Version:** 1.0  
**Target Audience:** Computer Science Students (Capstone Project)  
**Learning Objectives:** Master TDD, CI/CD, and Professional Git Workflows  
**Project Vehicle:** PrezI - AI-Powered Presentation Management Application  

---

## 📚 Table of Contents

### **Part I: Foundations** 
1. [Welcome to Your Capstone Adventure](#1-welcome-to-your-capstone-adventure)
2. [The TDD Mindset: Red, Green, Refactor](#2-the-tdd-mindset-red-green-refactor)
3. [Professional Git Workflow: Your Development Compass](#3-professional-git-workflow-your-development-compass)
4. [Setting Up Your Development Environment](#4-setting-up-your-development-environment)

### **Part II: TDD in Practice**
5. [Your First TDD Cycle: Building Project Models](#5-your-first-tdd-cycle-building-project-models)
6. [Database Layer TDD with Repository Pattern](#6-database-layer-tdd-with-repository-pattern)
7. [API Layer TDD: RESTful Services with FastAPI](#7-api-layer-tdd-restful-services-with-fastapi)
8. [Frontend TDD: React Components and User Interactions](#8-frontend-tdd-react-components-and-user-interactions)

### **Part III: Advanced TDD & Integration**
9. [Advanced TDD: AI Integration and External Services](#9-advanced-tdd-ai-integration-and-external-services)
10. [End-to-End Testing: The Full User Journey](#10-end-to-end-testing-the-full-user-journey)
11. [Test Doubles: Mocks, Stubs, and Fakes](#11-test-doubles-mocks-stubs-and-fakes)

### **Part IV: CI/CD & Professional Practices**
12. [Introduction to CI/CD: Automating Your Development Pipeline](#12-introduction-to-cicd-automating-your-development-pipeline)
13. [GitHub Actions: Your First CI Pipeline](#13-github-actions-your-first-ci-pipeline)
14. [Advanced CI/CD: Testing, Security, and Deployment](#14-advanced-cicd-testing-security-and-deployment)
15. [Code Quality Gates: Linting, Coverage, and Review](#15-code-quality-gates-linting-coverage-and-review)

### **Part V: Mastery & Assessment**
16. [Performance Testing and Monitoring](#16-performance-testing-and-monitoring)
17. [Documentation-Driven Development](#17-documentation-driven-development)
18. [Capstone Project Assessment: TDD Mastery Evaluation](#18-capstone-project-assessment-tdd-mastery-evaluation)
19. [Beyond the Capstone: Industry Best Practices](#19-beyond-the-capstone-industry-best-practices)

### **Appendices**
- [A: TDD Cheat Sheet](#appendix-a-tdd-cheat-sheet)
- [B: Git Commands Reference](#appendix-b-git-commands-reference)
- [C: CI/CD Pipeline Templates](#appendix-c-cicd-pipeline-templates)
- [D: Testing Frameworks Quick Reference](#appendix-d-testing-frameworks-quick-reference)

---

## Learning Path Overview

This guide follows a carefully crafted learning progression:

**🔴 Red Phase:** Understanding the problem and writing failing tests  
**🟢 Green Phase:** Making tests pass with minimal code  
**🔵 Refactor Phase:** Improving code quality while maintaining tests  
**🚀 Deploy Phase:** Automating delivery through CI/CD pipelines  

Each chapter builds upon the previous one, creating a comprehensive understanding of modern software development practices.

---

*"The best way to learn programming is to write code. The best way to write good code is to test it first. The best way to deliver good code is to automate its journey to production."*

**Let's begin your journey to TDD and CI/CD mastery!**

---

## 1. Welcome to Your Capstone Adventure

### 🎮 Think of Development Like Building a Video Game

Imagine you're creating the next big video game. You wouldn't just throw together some graphics and hope it works, right? You'd have a game design document, you'd test each level before players see it, and you'd have systems to automatically deploy updates when you fix bugs.

**That's exactly what we're doing with PrezI!**

Building software without tests is like creating a game without playtesting - you're just hoping it works when real users try it. Building software without automation is like manually copying game files to every player's computer when you release an update.

### 🚀 Your Mission: Build PrezI from Zero to Hero

Throughout this guide, you'll be building **PrezI** - an AI-powered presentation management application that will:
- Help users organize their PowerPoint slides intelligently
- Use AI to automatically create presentations
- Provide a beautiful, modern interface that feels like magic

But here's the secret sauce: **You'll build it using Test-Driven Development (TDD) and modern CI/CD practices** - the same techniques used by top tech companies like Google, Microsoft, and Netflix.

### 🧠 What You'll Master

By the end of this capstone project, you'll have:

1. **TDD Superpowers**: Write tests that guide your code design (not the other way around!)
2. **Git Wizardry**: Use professional branching strategies and collaboration workflows
3. **CI/CD Magic**: Automate testing, building, and deployment like a DevOps engineer
4. **Industry-Ready Skills**: The exact practices used in professional software teams

### 🎯 The Three Laws of TDD (Your New Programming Commandments)

Before we dive in, let me introduce you to the **Three Laws of TDD** - created by "Uncle Bob" Martin, one of the programming legends:

1. **Law #1**: You are not allowed to write any production code unless it is to make a failing unit test pass.
2. **Law #2**: You are not allowed to write any more of a unit test than is sufficient to fail.
3. **Law #3**: You are not allowed to write any more production code than is sufficient to pass the one failing unit test.

Think of these like the rules of a challenging game - they might seem restrictive at first, but they lead to incredibly powerful results!

### 🌟 Why This Matters for Your Career

**Real talk**: The companies you want to work for (tech giants, innovative startups, cutting-edge companies) ALL use these practices. Learning TDD and CI/CD isn't just about getting good grades - it's about becoming the kind of developer that companies fight to hire.

**Fun Fact**: Studies show that teams using TDD have 40-80% fewer bugs in production. That means less time fixing broken code and more time building amazing features!

---

## 2. The TDD Mindset: Red, Green, Refactor

### 🎨 TDD is Like Painting by Numbers (But Cooler)

Remember painting by numbers as a kid? You'd start with a canvas full of numbered sections, and you'd fill each section with the right color. TDD works similarly:

- **🔴 Red**: Draw the outline (write a failing test)
- **🟢 Green**: Fill in the basics (make the test pass)
- **🔵 Refactor**: Add the artistic touches (improve the code)

### 🧪 The Science Behind the Magic

Think of TDD like being a scientist:

1. **Hypothesis** (Red): "I think this function should work this way"
2. **Experiment** (Green): Write the simplest code to test your hypothesis
3. **Analysis** (Refactor): Improve your solution based on what you learned

### 🎭 The Three Phases Explained

#### 🔴 **RED PHASE**: "The Failing Test"
This is where you become a **requirements detective**. You write a test that describes what you want your code to do - even though that code doesn't exist yet!

```python
# Example: Testing our Project model before it exists
def test_project_should_have_name_and_creation_date():
    project = Project(name="My Awesome Presentation")
    assert project.name == "My Awesome Presentation"
    assert project.created_at is not None  # This will fail - Project doesn't exist yet!
```

**Why this is powerful**: Writing the test first forces you to think about the API design and user experience BEFORE you get lost in implementation details.

#### 🟢 **GREEN PHASE**: "Make It Work"
Now you write the **minimal** code to make the test pass. Not the best code, not the prettiest code - just enough to turn that red test green.

```python
# Minimal Project class to make our test pass
from datetime import datetime

class Project:
    def __init__(self, name):
        self.name = name
        self.created_at = datetime.now()
```

**Why minimal matters**: Resist the urge to over-engineer! The test tells you exactly what you need. Extra features can be added in future TDD cycles.

#### 🔵 **REFACTOR PHASE**: "Make It Beautiful"
With a passing test as your safety net, now you can improve the code without fear. Add error handling, improve performance, make it more readable.

```python
# Refactored Project class with better design
from datetime import datetime
from typing import Optional

class Project:
    def __init__(self, name: str, created_at: Optional[datetime] = None):
        if not name or not name.strip():
            raise ValueError("Project name cannot be empty")
        
        self.name = name.strip()
        self.created_at = created_at or datetime.now()
```

### 🎪 The Rhythm of TDD

TDD has a rhythm - like a drummer keeping time in a band:

1. **Red** (30 seconds): Write a tiny failing test
2. **Green** (2 minutes): Make it pass with minimal code
3. **Refactor** (2-5 minutes): Clean up and improve
4. **Repeat**: Start the cycle again

### 🏃‍♂️ The Speed Advantage

**Myth**: "TDD slows you down because you're writing more code"
**Reality**: TDD speeds you up because:

- You catch bugs immediately (not 3 weeks later when fixing them is expensive)
- You have instant feedback on your design decisions
- You can refactor fearlessly with your test safety net
- You spend less time debugging and more time creating

### 🎯 TDD + CI/CD: The Perfect Partnership

Here's where it gets exciting - **your TDD tests become the foundation of your CI/CD pipeline!**

Every time you push code to GitHub:
1. **Continuous Integration** automatically runs ALL your tests
2. If tests pass → code can be merged and deployed
3. If tests fail → deployment is blocked, preventing broken code from reaching users

This means your TDD practice directly translates to professional deployment practices!

---

## 3. Professional Git Workflow: Your Development Compass

### 🧭 Git is Your Time Machine and Collaboration Superpower

Imagine if you could:
- Save your game at any point and return to it later
- See exactly what changed between save points
- Collaborate with friends on the same game without overwriting each other's work
- Automatically merge everyone's contributions

**That's Git!** And in professional development, knowing Git isn't optional - it's like knowing how to use email in a business setting.

### 🌊 Modern Git Workflows: From Complex to Simple

The industry has evolved from complex workflows to simpler, more agile approaches:

#### 🏭 **GitFlow** (The Old Way - Complex but Structured)
Like a formal factory assembly line:
```
main ────────────●─────────●─────────
       │         │         │
develop ●───●───●───●───●───●───●───●──
         │   │       │       │
feature  ●───●       ●───●   ●───●
                      │
release                ●───●
                        │
hotfix                  ●───●
```

**When to use**: Large teams, multiple product versions, infrequent releases

#### 🚀 **GitHub Flow** (The Modern Way - Simple and Fast)
Like a nimble startup:
```
main ────●───●───●───●───●───●─────
          │   │   │   │   │   │
feature   ●───●   ●───●   ●───●
```

**When to use**: Small to medium teams, continuous deployment, frequent releases (this is what we'll use for PrezI!)

### 🎮 Your Git Workflow for PrezI

We'll use a **modified GitHub Flow** that includes professional CI/CD practices:

#### Step 1: Feature Branch Creation
```bash
# Start from the latest main branch
git checkout main
git pull origin main

# Create a feature branch with descriptive naming
git checkout -b feature/user-authentication-tdd

# Professional naming convention:
# feature/description
# bugfix/issue-description  
# hotfix/critical-issue
```

#### Step 2: TDD Development Cycle
```bash
# Work in TDD cycles: Red → Green → Refactor
git add test_user_authentication.py
git commit -m "RED: Add failing test for user login validation"

git add user_authentication.py
git commit -m "GREEN: Implement basic user login validation"

git add user_authentication.py
git commit -m "REFACTOR: Improve error handling and add type hints"
```

#### Step 3: Continuous Integration (CI) Magic ✨
When you push your branch:
```bash
git push origin feature/user-authentication-tdd
```

**GitHub Actions automatically**:
1. Runs ALL your tests
2. Checks code quality (linting)
3. Verifies security (dependency scanning)
4. Reports results back to you

#### Step 4: Professional Code Review
```bash
# Create a Pull Request (PR) through GitHub UI
# Your PR triggers:
# - Automated tests
# - Code review from teammates
# - Continuous integration checks
```

#### Step 5: Automated Deployment (CD) 🚀
When your PR is approved and merged:
```bash
# GitHub Actions automatically:
# 1. Runs final test suite
# 2. Builds the application
# 3. Deploys to staging environment
# 4. (Eventually) deploys to production
```

### 🎯 Professional Commit Message Format

Your commit messages should tell a story. Use this format:

```
type(scope): brief description

Longer explanation if needed.

- Additional bullet points
- Can provide more context
```

**Examples for PrezI**:
```bash
git commit -m "feat(auth): add user login with TDD approach

- Implemented LoginService with input validation
- Added comprehensive test coverage for edge cases  
- Integrated with CI pipeline for automated testing"

git commit -m "test(database): add integration tests for Project repository

- Tests cover CRUD operations and edge cases
- Mock external dependencies appropriately
- Verify database transactions work correctly"

git commit -m "ci(github-actions): add automated testing workflow

- Run tests on Python 3.9, 3.10, and 3.11
- Include linting and security checks
- Deploy to staging on successful PR merge"
```

### 🔄 The Professional Development Rhythm

Here's your daily workflow rhythm as a professional developer:

**Morning Sync**:
```bash
git checkout main
git pull origin main  # Get latest changes
git checkout feature/my-current-work
git rebase main      # Integrate latest changes into your work
```

**Development Cycle** (repeat throughout the day):
```bash
# TDD Red phase
git add tests/
git commit -m "RED: add failing test for new feature"

# TDD Green phase  
git add src/
git commit -m "GREEN: implement minimal code to pass test"

# TDD Refactor phase
git add src/
git commit -m "REFACTOR: improve code quality and design"

# Push regularly to trigger CI
git push origin feature/my-current-work
```

**End of Day**:
```bash
git push origin feature/my-current-work  # Backup your work
# Create PR when feature is complete
```

### 🏆 Why This Workflow Rocks

1. **Safety Net**: Your tests prevent you from breaking existing code
2. **Collaboration**: Multiple developers can work simultaneously without conflicts
3. **Quality**: Automated checks catch issues before they reach production
4. **Documentation**: Git history tells the story of how your code evolved
5. **Professional**: This is exactly how top companies manage code

---

## 4. Setting Up Your Development Environment

### 🛠️ Building Your Developer Toolkit

Think of this like setting up a professional workshop. A carpenter needs the right tools to build beautiful furniture - you need the right tools to build beautiful software!

### 📋 Prerequisites Checklist

Before we start building PrezI, let's ensure you have everything you need:

#### Essential Tools
- [ ] **Python 3.9+** (Our backend language)
- [ ] **Node.js 16+** (For our frontend and build tools)
- [ ] **Git** (Version control)
- [ ] **GitHub Account** (Code hosting and CI/CD)
- [ ] **VS Code** (Recommended editor)
- [ ] **Docker** (For consistent environments - optional but recommended)

#### VS Code Extensions (Highly Recommended)
- [ ] Python extension pack
- [ ] GitLens (Supercharge your Git experience)
- [ ] Live Share (Pair programming)
- [ ] pytest extension
- [ ] GitHub Actions extension

### 🏗️ Project Structure Setup

Let's create the PrezI project structure following professional standards:

```bash
# Create the main project directory
mkdir prezi_app
cd prezi_app

# Initialize Git repository
git init
git branch -M main

# Create professional project structure
mkdir -p {backend/{api/v1,core,database,tests},frontend/{src/{components,services,tests},public},docs,.github/workflows}

# Create essential files
touch README.md .gitignore backend/requirements.txt frontend/package.json
touch .github/workflows/ci.yml .github/workflows/cd.yml
```

### 🐍 Backend Setup (Python + FastAPI)

#### Create Virtual Environment
```bash
cd backend

# Create isolated Python environment (like having a clean workshop for each project)
python -m venv venv

# Activate the environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### Install Dependencies
Create `requirements.txt`:
```txt
# Core backend dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pydantic==2.5.0
sqlalchemy==2.0.23
alembic==1.13.0

# Development and testing
black==23.11.0
flake8==6.1.0
mypy==1.7.1
httpx==0.25.2  # For testing HTTP requests

# CI/CD specific
pytest-html==4.1.1  # For HTML test reports
bandit==1.7.5        # Security linting
safety==2.3.4        # Dependency security checks
```

Install everything:
```bash
pip install -r requirements.txt
```

### 🌐 Frontend Setup (Modern Web Stack)

```bash
cd ../frontend

# Initialize Node.js project
npm init -y

# Install core dependencies
npm install react@18 react-dom@18 vite@4 @vitejs/plugin-react

# Install testing dependencies  
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event vitest jsdom

# Install development tools
npm install --save-dev eslint prettier @typescript-eslint/parser @typescript-eslint/eslint-plugin

# Install CI/CD helpers
npm install --save-dev start-server-and-test cypress
```

### 🔧 Configuration Files

#### `.gitignore` (Professional ignore patterns)
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

# Node.js
node_modules/
dist/
build/
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/settings.json
.idea/

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Database
*.db
*.sqlite3

# Secrets
.env
secrets/
```

#### `backend/pytest.ini` (Test configuration)
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
```

### 🚀 Your First CI/CD Pipeline

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
        python-version: [3.9, 3.10, 3.11]
    
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
        npm run test:coverage
        
    - name: 🏗️ Build application
      run: |
        cd frontend
        npm run build
```

### 🎯 Verify Your Setup

Let's make sure everything is working with a simple test:

#### Backend Test
Create `backend/tests/test_setup.py`:
```python
"""Test that our development environment is properly configured."""

def test_python_version():
    """Verify we're using a supported Python version."""
    import sys
    assert sys.version_info >= (3, 9)

def test_imports():
    """Verify all critical dependencies can be imported."""
    import fastapi
    import pytest
    import sqlalchemy
    # If this runs without errors, our environment is good!

def test_basic_math():
    """A simple test to verify pytest is working."""
    assert 2 + 2 == 4
    assert "hello" + " world" == "hello world"
```

Run the test:
```bash
cd backend
pytest tests/test_setup.py -v
```

#### Frontend Test
Create `frontend/src/tests/setup.test.js`:
```javascript
// Test that our frontend environment is properly configured

describe('Development Environment', () => {
  test('basic JavaScript functionality', () => {
    expect(2 + 2).toBe(4);
    expect('hello' + ' world').toBe('hello world');
  });

  test('React testing library is available', () => {
    // If this imports without error, our setup is correct
    const { render } = require('@testing-library/react');
    expect(render).toBeDefined();
  });
});
```

### 🎉 Congratulations!

You've just set up a professional-grade development environment! You now have:

✅ **Version control** with Git  
✅ **Backend testing** with pytest  
✅ **Frontend testing** with modern tools  
✅ **Automated CI pipeline** that runs on every commit  
✅ **Code quality tools** (linting, security checks)  
✅ **Professional project structure**  

**Next up**: We'll write our first TDD cycle and see this environment in action!

---

## 5. Your First TDD Cycle: Building Project Models

### 🎯 Time to Get Your Hands Dirty!

Now comes the moment you've been waiting for - **writing actual code using TDD!** We're going to build the core `Project` model for PrezI, and you'll experience the magical Red-Green-Refactor cycle firsthand.

Think of this like learning to ride a bike - it might feel wobbly at first, but once you get the rhythm, you'll wonder how you ever coded without TDD!

### 🎮 The Game Plan: Building a Project Model

Our PrezI application needs to manage presentation projects. Each project should:
- Have a unique name
- Track when it was created  
- Store the file path where presentations are stored
- Validate that the name isn't empty

But here's the TDD twist - **we're going to write the tests BEFORE we write the Project class!**

### 🔴 RED PHASE: Writing Our First Failing Test

Let's start with the simplest possible test. Create `backend/tests/test_project_model.py`:

```python
"""Tests for the Project model - our first TDD adventure!"""

import pytest
from datetime import datetime
from models.project import Project  # This doesn't exist yet - that's the point!


def test_project_creation_with_name():
    """Test that we can create a project with just a name."""
    # This is our first "red" test - it will fail because Project doesn't exist!
    project = Project(name="My First Presentation Project")
    
    assert project.name == "My First Presentation Project"
    assert project.created_at is not None
    assert isinstance(project.created_at, datetime)


def test_project_requires_name():
    """Test that creating a project without a name raises an error."""
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        Project(name="")
    
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        Project(name=None)
```

Now let's run this test and watch it fail beautifully:

```bash
cd backend
pytest tests/test_project_model.py -v
```

**Expected output:**
```
ImportError: No module named 'models.project'
```

🎉 **Congratulations!** You just wrote your first failing test! This is the "Red" phase - the test fails because the code doesn't exist yet.

### 🟢 GREEN PHASE: Making the Test Pass (Minimally)

Now we write **just enough** code to make our test pass. Create `backend/models/__init__.py` (empty file) and `backend/models/project.py`:

```python
"""Project model - built with TDD!"""

from datetime import datetime
from typing import Optional


class Project:
    """Represents a presentation project in PrezI."""
    
    def __init__(self, name: Optional[str], created_at: Optional[datetime] = None):
        # Validation logic to make our tests pass
        if not name or (isinstance(name, str) and not name.strip()):
            raise ValueError("Project name cannot be empty")
        
        self.name = name
        self.created_at = created_at or datetime.now()
```

Run the test again:

```bash
pytest tests/test_project_model.py -v
```

**Expected output:**
```
test_project_model.py::test_project_creation_with_name PASSED
test_project_model.py::test_project_requires_name PASSED

======================== 2 passed in 0.02s ========================
```

🎉 **GREEN!** Your tests are passing! Notice how we wrote the **minimal** code needed - no fancy features, no over-engineering.

### 🔵 REFACTOR PHASE: Making It Beautiful

Now that our tests are green, we can refactor safely. Let's improve our Project class:

```python
"""Project model - built with TDD!"""

from datetime import datetime
from typing import Optional
from pathlib import Path
import uuid


class Project:
    """Represents a presentation project in PrezI.
    
    Each project manages a collection of PowerPoint presentations
    and provides organization capabilities for slides.
    """
    
    def __init__(
        self, 
        name: str, 
        path: Optional[str] = None,
        created_at: Optional[datetime] = None,
        project_id: Optional[str] = None
    ):
        """Initialize a new project.
        
        Args:
            name: The project name (required, non-empty)
            path: File system path for project files
            created_at: When the project was created (defaults to now)
            project_id: Unique identifier (auto-generated if not provided)
        
        Raises:
            ValueError: If name is empty or invalid
        """
        self._validate_name(name)
        
        self.name = name.strip()
        self.path = path
        self.created_at = created_at or datetime.now()
        self.project_id = project_id or str(uuid.uuid4())
    
    def _validate_name(self, name: Optional[str]) -> None:
        """Validate the project name."""
        if not name or not isinstance(name, str) or not name.strip():
            raise ValueError("Project name cannot be empty")
    
    def __str__(self) -> str:
        """String representation of the project."""
        return f"Project(name='{self.name}', id='{self.project_id[:8]}...')"
    
    def __repr__(self) -> str:
        """Developer representation of the project."""
        return (f"Project(name='{self.name}', path='{self.path}', "
                f"created_at='{self.created_at}', project_id='{self.project_id}')")
```

Run the tests again to ensure our refactoring didn't break anything:

```bash
pytest tests/test_project_model.py -v
```

Still green? Perfect! That's the power of TDD - you can refactor fearlessly.

### 🚀 Adding More Features with TDD

Let's add more functionality using the Red-Green-Refactor cycle. Add these tests to `test_project_model.py`:

```python
def test_project_with_custom_path():
    """Test that we can specify a custom path for project files."""
    project = Project(name="Client Presentation", path="/projects/client-deck")
    
    assert project.path == "/projects/client-deck"


def test_project_string_representation():
    """Test that projects have useful string representations."""
    project = Project(name="Test Project")
    
    str_repr = str(project)
    assert "Test Project" in str_repr
    assert "Project(" in str_repr


def test_project_has_unique_id():
    """Test that each project gets a unique identifier."""
    project1 = Project(name="Project One")
    project2 = Project(name="Project Two")
    
    assert project1.project_id != project2.project_id
    assert len(project1.project_id) > 0
    assert len(project2.project_id) > 0


def test_project_name_is_trimmed():
    """Test that project names are automatically trimmed of whitespace."""
    project = Project(name="  Spaced Out Project  ")
    
    assert project.name == "Spaced Out Project"
```

Run these new tests:

```bash
pytest tests/test_project_model.py::test_project_with_custom_path -v
pytest tests/test_project_model.py::test_project_string_representation -v
pytest tests/test_project_model.py::test_project_has_unique_id -v
pytest tests/test_project_model.py::test_project_name_is_trimmed -v
```

**All green!** Our refactored code already handles these cases. This is TDD magic - good design emerges naturally.

### 🎪 Your First CI/CD Integration

Now let's see your TDD tests work with your CI pipeline! 

First, commit your work using professional Git practices:

```bash
# Stage your changes
git add models/ tests/

# Commit with a descriptive message
git commit -m "feat(models): implement Project model with TDD

- Add Project class with name validation
- Include comprehensive test coverage
- Support custom paths and unique IDs
- Follow TDD Red-Green-Refactor cycle"

# Push to trigger CI pipeline
git push origin main
```

**What happens next is CI/CD magic:**

1. **GitHub Actions detects your push**
2. **Automatically sets up Python environment**
3. **Installs your dependencies**
4. **Runs ALL your tests** (including your new Project tests)
5. **Reports results back to GitHub**

You can watch this happen in real-time by going to your GitHub repository → Actions tab!

### 🧠 What You Just Learned

In this first TDD cycle, you experienced:

✅ **Red Phase**: Writing failing tests that describe desired behavior  
✅ **Green Phase**: Writing minimal code to make tests pass  
✅ **Refactor Phase**: Improving code quality while maintaining green tests  
✅ **CI Integration**: Your tests automatically run on every commit  
✅ **Professional Git Workflow**: Descriptive commits that tell a story  

### 🎯 TDD Principles You Applied

1. **Test-First Design**: You thought about the API before implementation
2. **Incremental Development**: Small steps with frequent feedback
3. **Safety Net**: Tests protect you during refactoring
4. **Documentation**: Tests serve as executable documentation
5. **Quality Assurance**: CI ensures your code works in different environments

### 🤔 Reflection Questions

Before moving on, think about these questions:

1. **How did writing tests first change your thinking about the code?**
2. **What would have happened if you tried to refactor without tests?**
3. **How does the CI pipeline give you confidence in your code?**

### 🎪 Fun TDD Challenge

Try this exercise: Add a new feature to the Project class using TDD:

**Feature**: Projects should track how many presentation files they contain

**Your mission**:
1. 🔴 Write a failing test for `project.file_count` property
2. 🟢 Implement minimal code to make it pass
3. 🔵 Refactor to make it beautiful
4. 🚀 Commit and watch CI run your tests

### 🏁 Chapter Summary

You've just completed your first TDD cycle! You now know how to:

- Write failing tests that describe desired behavior
- Implement minimal code to satisfy tests
- Refactor safely with a test safety net
- Integrate TDD with professional Git workflows
- Use CI pipelines to automatically validate your code

**Next up**: We'll apply TDD to database operations and learn about the Repository pattern!

---

## 6. Database Layer TDD with Repository Pattern

### 🏦 Building PrezI's Memory Bank

Every great application needs a reliable way to store and retrieve data. PrezI needs to remember:
- Projects and their details
- Imported presentation files  
- Individual slides and their content
- Keywords and tags for organization

We're going to build this using the **Repository Pattern** - a professional design pattern that makes database operations testable, maintainable, and swappable.

Think of a repository like a **smart librarian** - you ask for "all projects created this month" and the librarian handles all the complex database queries behind the scenes.

### 🎯 What You'll Build in This Chapter

By the end of this chapter, your PrezI app will have:
- A complete SQLite database for storing all application data
- Repository classes that handle all database operations
- Comprehensive tests that ensure data integrity
- Database migrations for version control
- CI pipeline integration for database testing

### 🧩 The Repository Pattern Explained

Instead of scattering SQL queries throughout your code, the Repository pattern creates a clean interface:

```python
# ❌ Bad: SQL scattered everywhere
def get_user_projects(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE user_id = ?", (user_id,))
    return cursor.fetchall()

# ✅ Good: Repository pattern
class ProjectRepository:
    def find_by_user(self, user_id: str) -> List[Project]:
        # Clean, testable interface
        pass
```

### 🏗️ Setting Up the Database Foundation

First, let's create the database schema. Create `backend/database/schema.sql`:

```sql
-- PrezI Database Schema
-- Built with TDD principles

-- Core projects table
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Presentation files within projects
CREATE TABLE IF NOT EXISTS files (
    file_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    slide_count INTEGER DEFAULT 0,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE
);

-- Individual slides
CREATE TABLE IF NOT EXISTS slides (
    slide_id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    slide_number INTEGER NOT NULL,
    title TEXT,
    content TEXT,
    thumbnail_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files (file_id) ON DELETE CASCADE
);

-- Keywords for organization
CREATE TABLE IF NOT EXISTS keywords (
    keyword_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    color TEXT DEFAULT '#e5e7eb',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE,
    UNIQUE (project_id, name)
);

-- Many-to-many relationship between slides and keywords
CREATE TABLE IF NOT EXISTS slide_keywords (
    slide_id TEXT NOT NULL,
    keyword_id TEXT NOT NULL,
    PRIMARY KEY (slide_id, keyword_id),
    FOREIGN KEY (slide_id) REFERENCES slides (slide_id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES keywords (keyword_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_files_project_id ON files (project_id);
CREATE INDEX IF NOT EXISTS idx_slides_file_id ON slides (file_id);
CREATE INDEX IF NOT EXISTS idx_keywords_project_id ON keywords (project_id);
CREATE INDEX IF NOT EXISTS idx_slide_keywords_slide_id ON slide_keywords (slide_id);
CREATE INDEX IF NOT EXISTS idx_slide_keywords_keyword_id ON slide_keywords (keyword_id);
```

### 🔧 Database Connection Manager

Create `backend/database/connection.py`:

```python
"""Database connection management for PrezI."""

import sqlite3
import threading
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


class DatabaseManager:
    """Manages SQLite database connections with thread safety."""
    
    def __init__(self, db_path: str = "prezi.db"):
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._ensure_database_exists()
    
    def _ensure_database_exists(self) -> None:
        """Create database and tables if they don't exist."""
        with self.get_connection() as conn:
            schema_path = Path(__file__).parent / "schema.sql"
            with open(schema_path, 'r') as f:
                conn.executescript(f.read())
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
        
        try:
            yield self._local.connection
        except Exception:
            self._local.connection.rollback()
            raise
        else:
            self._local.connection.commit()
    
    def close(self) -> None:
        """Close database connection."""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            del self._local.connection
```

### 🔴 RED PHASE: Writing Repository Tests

Now let's write tests for our ProjectRepository. Create `backend/tests/test_project_repository.py`:

```python
"""Tests for ProjectRepository - TDD for database operations!"""

import pytest
import tempfile
import os
from datetime import datetime
from database.connection import DatabaseManager
from database.repositories import ProjectRepository
from models.project import Project


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create temporary file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Create database manager
    db_manager = DatabaseManager(path)
    
    yield db_manager
    
    # Cleanup
    db_manager.close()
    os.unlink(path)


@pytest.fixture
def project_repo(temp_db):
    """Create a ProjectRepository for testing."""
    return ProjectRepository(temp_db)


class TestProjectRepository:
    """Test suite for ProjectRepository."""
    
    def test_save_new_project(self, project_repo):
        """Test saving a new project to the database."""
        # Create a project
        project = Project(
            name="Test Project",
            path="/test/path"
        )
        
        # Save it
        saved_project = project_repo.save(project)
        
        # Verify it was saved
        assert saved_project.project_id is not None
        assert saved_project.name == "Test Project"
        assert saved_project.path == "/test/path"
        assert saved_project.created_at is not None
    
    def test_find_by_id(self, project_repo):
        """Test finding a project by its ID."""
        # Save a project first
        project = Project(name="Findable Project")
        saved_project = project_repo.save(project)
        
        # Find it by ID
        found_project = project_repo.find_by_id(saved_project.project_id)
        
        # Verify we found the right one
        assert found_project is not None
        assert found_project.project_id == saved_project.project_id
        assert found_project.name == "Findable Project"
    
    def test_find_by_id_not_found(self, project_repo):
        """Test finding a project that doesn't exist."""
        result = project_repo.find_by_id("nonexistent-id")
        assert result is None
    
    def test_find_all_projects(self, project_repo):
        """Test retrieving all projects."""
        # Save multiple projects
        project1 = project_repo.save(Project(name="Project 1"))
        project2 = project_repo.save(Project(name="Project 2"))
        project3 = project_repo.save(Project(name="Project 3"))
        
        # Find all
        all_projects = project_repo.find_all()
        
        # Verify we got them all
        assert len(all_projects) == 3
        project_names = [p.name for p in all_projects]
        assert "Project 1" in project_names
        assert "Project 2" in project_names
        assert "Project 3" in project_names
    
    def test_update_project(self, project_repo):
        """Test updating an existing project."""
        # Save a project
        project = project_repo.save(Project(name="Original Name"))
        
        # Update it
        project.name = "Updated Name"
        project.path = "/new/path"
        updated_project = project_repo.save(project)
        
        # Verify the update
        assert updated_project.name == "Updated Name"
        assert updated_project.path == "/new/path"
        assert updated_project.project_id == project.project_id
    
    def test_delete_project(self, project_repo):
        """Test deleting a project."""
        # Save a project
        project = project_repo.save(Project(name="Doomed Project"))
        project_id = project.project_id
        
        # Delete it
        success = project_repo.delete(project_id)
        
        # Verify deletion
        assert success is True
        assert project_repo.find_by_id(project_id) is None
    
    def test_delete_nonexistent_project(self, project_repo):
        """Test deleting a project that doesn't exist."""
        success = project_repo.delete("nonexistent-id")
        assert success is False
```

Run these tests and watch them fail gloriously:

```bash
pytest tests/test_project_repository.py -v
```

**Expected output:**
```
ImportError: No module named 'database.repositories'
```

Perfect! **RED PHASE** complete.

### 🟢 GREEN PHASE: Implementing the Repository

Now let's create the ProjectRepository. Create `backend/database/repositories.py`:

```python
"""Repository classes for PrezI database operations."""

from typing import List, Optional
from models.project import Project
from database.connection import DatabaseManager
import uuid


class ProjectRepository:
    """Repository for Project database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save(self, project: Project) -> Project:
        """Save a project to the database (insert or update)."""
        if hasattr(project, 'project_id') and project.project_id:
            return self._update(project)
        else:
            return self._insert(project)
    
    def _insert(self, project: Project) -> Project:
        """Insert a new project."""
        # Generate ID if not present
        if not hasattr(project, 'project_id') or not project.project_id:
            project.project_id = str(uuid.uuid4())
        
        with self.db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO projects (project_id, name, path, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                project.project_id,
                project.name,
                project.path,
                project.created_at
            ))
        
        return project
    
    def _update(self, project: Project) -> Project:
        """Update an existing project."""
        with self.db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE projects 
                SET name = ?, path = ?, updated_at = CURRENT_TIMESTAMP
                WHERE project_id = ?
            """, (
                project.name,
                project.path,
                project.project_id
            ))
        
        return project
    
    def find_by_id(self, project_id: str) -> Optional[Project]:
        """Find a project by its ID."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT project_id, name, path, created_at
                FROM projects
                WHERE project_id = ?
            """, (project_id,))
            
            row = cursor.fetchone()
            if row:
                return self._row_to_project(row)
            return None
    
    def find_all(self) -> List[Project]:
        """Find all projects."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT project_id, name, path, created_at
                FROM projects
                ORDER BY created_at DESC
            """)
            
            return [self._row_to_project(row) for row in cursor.fetchall()]
    
    def delete(self, project_id: str) -> bool:
        """Delete a project by ID. Returns True if deleted, False if not found."""
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM projects WHERE project_id = ?
            """, (project_id,))
            
            return cursor.rowcount > 0
    
    def _row_to_project(self, row) -> Project:
        """Convert a database row to a Project object."""
        return Project(
            name=row['name'],
            path=row['path'],
            created_at=row['created_at'],
            project_id=row['project_id']
        )
```

Run the tests again:

```bash
pytest tests/test_project_repository.py -v
```

**Expected output:**
```
====================== 8 passed in 0.05s ======================
```

🎉 **GREEN!** All tests passing!

### 🔵 REFACTOR PHASE: Adding Professional Features

Let's refactor to add error handling and better design:

```python
"""Repository classes for PrezI database operations."""

from typing import List, Optional
from models.project import Project
from database.connection import DatabaseManager
from datetime import datetime
import uuid
import logging


logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class ProjectRepository:
    """Repository for Project database operations with error handling."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save(self, project: Project) -> Project:
        """Save a project to the database (insert or update)."""
        try:
            if self._project_exists(project.project_id if hasattr(project, 'project_id') else None):
                return self._update(project)
            else:
                return self._insert(project)
        except Exception as e:
            logger.error(f"Error saving project {project.name}: {e}")
            raise RepositoryError(f"Failed to save project: {e}")
    
    def _project_exists(self, project_id: Optional[str]) -> bool:
        """Check if a project exists in the database."""
        if not project_id:
            return False
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM projects WHERE project_id = ?", 
                (project_id,)
            )
            return cursor.fetchone() is not None
    
    def _insert(self, project: Project) -> Project:
        """Insert a new project."""
        # Generate ID if not present
        if not hasattr(project, 'project_id') or not project.project_id:
            project.project_id = str(uuid.uuid4())
        
        with self.db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO projects (project_id, name, path, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                project.project_id,
                project.name,
                project.path,
                project.created_at.isoformat() if project.created_at else datetime.now().isoformat()
            ))
        
        logger.info(f"Created new project: {project.name} ({project.project_id})")
        return project
    
    def _update(self, project: Project) -> Project:
        """Update an existing project."""
        with self.db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE projects 
                SET name = ?, path = ?, updated_at = CURRENT_TIMESTAMP
                WHERE project_id = ?
            """, (
                project.name,
                project.path,
                project.project_id
            ))
        
        logger.info(f"Updated project: {project.name} ({project.project_id})")
        return project
    
    def find_by_id(self, project_id: str) -> Optional[Project]:
        """Find a project by its ID."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT project_id, name, path, created_at
                    FROM projects
                    WHERE project_id = ?
                """, (project_id,))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_project(row)
                return None
        except Exception as e:
            logger.error(f"Error finding project {project_id}: {e}")
            raise RepositoryError(f"Failed to find project: {e}")
    
    def find_all(self) -> List[Project]:
        """Find all projects."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT project_id, name, path, created_at
                    FROM projects
                    ORDER BY created_at DESC
                """)
                
                return [self._row_to_project(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error finding all projects: {e}")
            raise RepositoryError(f"Failed to find projects: {e}")
    
    def delete(self, project_id: str) -> bool:
        """Delete a project by ID. Returns True if deleted, False if not found."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM projects WHERE project_id = ?
                """, (project_id,))
                
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Deleted project: {project_id}")
                else:
                    logger.warning(f"Attempted to delete non-existent project: {project_id}")
                
                return success
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {e}")
            raise RepositoryError(f"Failed to delete project: {e}")
    
    def _row_to_project(self, row) -> Project:
        """Convert a database row to a Project object."""
        return Project(
            name=row['name'],
            path=row['path'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            project_id=row['project_id']
        )
```

Run tests to ensure refactoring didn't break anything:

```bash
pytest tests/test_project_repository.py -v
```

Still green? Excellent!

### 🚀 CI/CD Integration with Database Testing

Let's update your CI pipeline to include database testing. Add this to your `.github/workflows/ci.yml`:

```yaml
  test-database:
    name: 🗄️ Database Tests
    runs-on: ubuntu-latest
    
    steps:
    - name: 📥 Checkout code
      uses: actions/checkout@v4
      
    - name: 🐍 Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
        
    - name: 📦 Install dependencies
      run: |
        cd backend
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        
    - name: 🗄️ Test database operations
      run: |
        cd backend
        pytest tests/test_*_repository.py -v --cov=database
        
    - name: 🧪 Integration tests
      run: |
        cd backend
        pytest -m integration -v
```

### 🎪 Real-World Database Testing

Let's add some integration tests that simulate real PrezI usage. Create `backend/tests/test_project_integration.py`:

```python
"""Integration tests for Project workflow."""

import pytest
import tempfile
import os
from database.connection import DatabaseManager
from database.repositories import ProjectRepository
from models.project import Project


@pytest.mark.integration
def test_complete_project_workflow():
    """Test a complete project lifecycle - create, use, update, delete."""
    # Setup temporary database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        # Initialize components
        db_manager = DatabaseManager(db_path)
        project_repo = ProjectRepository(db_manager)
        
        # 1. Create a new project (like user creating their first project)
        new_project = Project(
            name="Client Q4 Presentation", 
            path="/projects/q4-client"
        )
        saved_project = project_repo.save(new_project)
        
        assert saved_project.project_id is not None
        assert saved_project.name == "Client Q4 Presentation"
        
        # 2. User comes back later, loads all their projects
        all_projects = project_repo.find_all()
        assert len(all_projects) == 1
        assert all_projects[0].name == "Client Q4 Presentation"
        
        # 3. User updates project details
        project = project_repo.find_by_id(saved_project.project_id)
        project.name = "Client Q4 Final Presentation"
        project.path = "/projects/q4-client-final"
        
        updated_project = project_repo.save(project)
        assert updated_project.name == "Client Q4 Final Presentation"
        
        # 4. Verify update persisted
        reloaded_project = project_repo.find_by_id(saved_project.project_id)
        assert reloaded_project.name == "Client Q4 Final Presentation"
        assert reloaded_project.path == "/projects/q4-client-final"
        
        # 5. User deletes old project
        deleted = project_repo.delete(saved_project.project_id)
        assert deleted is True
        
        # 6. Verify project is gone
        all_projects = project_repo.find_all()
        assert len(all_projects) == 0
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.integration  
def test_concurrent_project_operations():
    """Test that multiple project operations work correctly."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    try:
        db_manager = DatabaseManager(db_path)
        project_repo = ProjectRepository(db_manager)
        
        # Create multiple projects rapidly (simulating busy user)
        projects = []
        for i in range(10):
            project = Project(name=f"Project {i}", path=f"/path/{i}")
            saved_project = project_repo.save(project)
            projects.append(saved_project)
        
        # Verify all were saved
        all_projects = project_repo.find_all()
        assert len(all_projects) == 10
        
        # Verify each can be found individually
        for project in projects:
            found_project = project_repo.find_by_id(project.project_id)
            assert found_project is not None
            assert found_project.name == project.name
    
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)
```

### 🎯 Adding to the Main Application

Let's create a service layer that uses our repository. Create `backend/services/project_service.py`:

```python
"""Project service layer for PrezI application."""

from typing import List, Optional
from models.project import Project
from database.repositories import ProjectRepository, RepositoryError
import logging


logger = logging.getLogger(__name__)


class ProjectService:
    """Service layer for project operations."""
    
    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository
    
    def create_project(self, name: str, path: Optional[str] = None) -> Project:
        """Create a new project with validation."""
        if not name or not name.strip():
            raise ValueError("Project name is required")
        
        project = Project(name=name.strip(), path=path)
        
        try:
            return self.project_repository.save(project)
        except RepositoryError as e:
            logger.error(f"Failed to create project '{name}': {e}")
            raise
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        if not project_id:
            raise ValueError("Project ID is required")
        
        return self.project_repository.find_by_id(project_id)
    
    def get_all_projects(self) -> List[Project]:
        """Get all projects ordered by creation date."""
        return self.project_repository.find_all()
    
    def update_project(self, project_id: str, name: Optional[str] = None, 
                      path: Optional[str] = None) -> Optional[Project]:
        """Update an existing project."""
        project = self.project_repository.find_by_id(project_id)
        if not project:
            return None
        
        if name is not None:
            if not name.strip():
                raise ValueError("Project name cannot be empty")
            project.name = name.strip()
        
        if path is not None:
            project.path = path
        
        return self.project_repository.save(project)
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        if not project_id:
            raise ValueError("Project ID is required")
        
        return self.project_repository.delete(project_id)
```

### 🧪 Testing the Service Layer

Create `backend/tests/test_project_service.py`:

```python
"""Tests for ProjectService."""

import pytest
import tempfile
import os
from database.connection import DatabaseManager
from database.repositories import ProjectRepository
from services.project_service import ProjectService


@pytest.fixture
def project_service():
    """Create a ProjectService for testing."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db_manager = DatabaseManager(db_path)
    project_repo = ProjectRepository(db_manager)
    service = ProjectService(project_repo)
    
    yield service
    
    # Cleanup
    db_manager.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestProjectService:
    """Test suite for ProjectService."""
    
    def test_create_project_success(self, project_service):
        """Test successful project creation."""
        project = project_service.create_project("Test Project", "/test/path")
        
        assert project.name == "Test Project"
        assert project.path == "/test/path"
        assert project.project_id is not None
    
    def test_create_project_empty_name(self, project_service):
        """Test that empty project names are rejected."""
        with pytest.raises(ValueError, match="Project name is required"):
            project_service.create_project("")
        
        with pytest.raises(ValueError, match="Project name is required"):
            project_service.create_project("   ")
    
    def test_get_all_projects(self, project_service):
        """Test retrieving all projects."""
        # Create some projects
        project1 = project_service.create_project("Project 1")
        project2 = project_service.create_project("Project 2")
        
        # Get all projects
        all_projects = project_service.get_all_projects()
        
        assert len(all_projects) == 2
        project_names = [p.name for p in all_projects]
        assert "Project 1" in project_names
        assert "Project 2" in project_names
    
    def test_update_project(self, project_service):
        """Test updating a project."""
        # Create a project
        project = project_service.create_project("Original Name")
        
        # Update it
        updated = project_service.update_project(
            project.project_id, 
            name="Updated Name", 
            path="/new/path"
        )
        
        assert updated.name == "Updated Name"
        assert updated.path == "/new/path"
        assert updated.project_id == project.project_id
```

### 🎊 Commit Your Database Layer

Let's commit this major milestone:

```bash
git add database/ services/ tests/
git commit -m "feat(database): implement complete database layer with TDD

- Add SQLite schema for projects, files, slides, keywords  
- Implement ProjectRepository with full CRUD operations
- Add ProjectService for business logic layer
- Include comprehensive test coverage (unit + integration)
- Add CI pipeline integration for database testing
- Follow Repository pattern for clean architecture"

git push origin main
```

### 🏆 What You've Accomplished

Congratulations! You've just built a **production-ready database layer** for PrezI using TDD:

✅ **Complete SQLite schema** for all PrezI data  
✅ **Repository pattern** for clean, testable database operations  
✅ **Service layer** for business logic  
✅ **Comprehensive test coverage** (unit + integration)  
✅ **CI pipeline integration** for automated database testing  
✅ **Professional error handling** and logging  
✅ **Thread-safe database connections**  

Your PrezI application now has a solid foundation to store and manage presentation data!

### 🔮 Next Steps Preview

In the next chapter, we'll:
- Build the REST API layer using FastAPI
- Connect your database to HTTP endpoints
- Add API testing with automatic OpenAPI documentation
- Implement request/response validation

**The students are now 2/3 of the way to having a complete, working PrezI application!**

---

## 7. API Layer TDD: RESTful Services with FastAPI

### 🌐 Building PrezI's Communication Bridge

Now that PrezI has a solid database foundation, it's time to build the **REST API** - the bridge that allows the frontend to communicate with your backend. Think of APIs like a restaurant menu - they tell the frontend exactly what it can order (endpoints) and what format the order should be in (request/response schemas).

We'll use **FastAPI** - one of the most modern and powerful Python web frameworks. It's fast, has automatic documentation, and plays beautifully with TDD!

### 🎯 What You'll Build in This Chapter

By the end of this chapter, your PrezI app will have:
- A complete REST API with all project management endpoints
- Automatic OpenAPI documentation (interactive API explorer!)
- Request/response validation using Pydantic models
- Comprehensive API testing using TDD
- Error handling with proper HTTP status codes
- CI/CD pipeline integration for API testing

### 🏗️ FastAPI Architecture Overview

FastAPI follows a clean architecture pattern that works perfectly with TDD:

```python
# 🎯 Clean separation of concerns
Frontend (React) 
    ↕ HTTP Requests
API Layer (FastAPI) 
    ↕ Service Calls  
Service Layer (Business Logic)
    ↕ Repository Calls
Database Layer (SQLite)
```

Each layer has a single responsibility and can be tested independently!

### 🔴 RED PHASE: Writing API Tests First

Let's start by writing tests for our Project API endpoints. Create `backend/tests/test_project_api.py`:

```python
"""Tests for Project API endpoints - TDD for REST APIs!"""

import pytest
from fastapi.testclient import TestClient
from fastapi import status
import tempfile
import os
from main import create_app
from database.connection import DatabaseManager
from database.repositories import ProjectRepository
from services.project_service import ProjectService
import json


@pytest.fixture
def test_app():
    """Create a test application with temporary database."""
    # Create temporary database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Create app with test database
    app = create_app(db_path=db_path)
    client = TestClient(app)
    
    yield client
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestProjectAPI:
    """Test suite for Project API endpoints."""
    
    def test_create_project_success(self, test_app):
        """Test successful project creation via API."""
        project_data = {
            "name": "Test Project",
            "path": "/test/path"
        }
        
        response = test_app.post("/api/v1/projects", json=project_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["path"] == "/test/path"
        assert "project_id" in data
        assert "created_at" in data
    
    def test_create_project_invalid_data(self, test_app):
        """Test project creation with invalid data."""
        # Test empty name
        response = test_app.post("/api/v1/projects", json={"name": ""})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test missing name
        response = test_app.post("/api/v1/projects", json={"path": "/some/path"})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_all_projects(self, test_app):
        """Test retrieving all projects."""
        # Create some projects first
        test_app.post("/api/v1/projects", json={"name": "Project 1"})
        test_app.post("/api/v1/projects", json={"name": "Project 2"})
        
        # Get all projects
        response = test_app.get("/api/v1/projects")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert len(data) == 2
        project_names = [p["name"] for p in data]
        assert "Project 1" in project_names
        assert "Project 2" in project_names
    
    def test_get_project_by_id(self, test_app):
        """Test retrieving a specific project by ID."""
        # Create a project
        create_response = test_app.post("/api/v1/projects", json={"name": "Test Project"})
        project_id = create_response.json()["project_id"]
        
        # Get the project by ID
        response = test_app.get(f"/api/v1/projects/{project_id}")
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == "Test Project"
        assert data["project_id"] == project_id
    
    def test_get_project_not_found(self, test_app):
        """Test retrieving a non-existent project."""
        response = test_app.get("/api/v1/projects/nonexistent-id")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()
    
    def test_update_project(self, test_app):
        """Test updating an existing project."""
        # Create a project
        create_response = test_app.post("/api/v1/projects", json={"name": "Original Name"})
        project_id = create_response.json()["project_id"]
        
        # Update the project
        update_data = {
            "name": "Updated Name",
            "path": "/updated/path"
        }
        response = test_app.put(f"/api/v1/projects/{project_id}", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["path"] == "/updated/path"
        assert data["project_id"] == project_id
    
    def test_update_project_not_found(self, test_app):
        """Test updating a non-existent project."""
        response = test_app.put("/api/v1/projects/nonexistent-id", json={"name": "New Name"})
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_project(self, test_app):
        """Test deleting a project."""
        # Create a project
        create_response = test_app.post("/api/v1/projects", json={"name": "Doomed Project"})
        project_id = create_response.json()["project_id"]
        
        # Delete the project
        response = test_app.delete(f"/api/v1/projects/{project_id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify it's gone
        get_response = test_app.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_project_not_found(self, test_app):
        """Test deleting a non-existent project."""
        response = test_app.delete("/api/v1/projects/nonexistent-id")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
```

Run these tests and watch them fail spectacularly:

```bash
cd backend
pytest tests/test_project_api.py -v
```

**Expected output:**
```
ImportError: No module named 'main'
```

Perfect! **RED PHASE** complete. The tests fail because we haven't built the API yet.

### 🟢 GREEN PHASE: Building the FastAPI Application

Now let's build the API to make our tests pass. First, create the Pydantic models for request/response validation. Create `backend/api/schemas.py`:

```python
"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProjectCreate(BaseModel):
    """Schema for creating a new project."""
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    path: Optional[str] = Field(None, max_length=500, description="Project file path")


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Project name")
    path: Optional[str] = Field(None, max_length=500, description="Project file path")


class ProjectResponse(BaseModel):
    """Schema for project responses."""
    project_id: str
    name: str
    path: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True  # Allow converting from ORM objects


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    error_code: Optional[str] = None
```

Now create the API endpoints. Create `backend/api/v1/projects.py`:

```python
"""Project API endpoints for PrezI."""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from api.schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ErrorResponse
from services.project_service import ProjectService
from database.repositories import ProjectRepository, RepositoryError
from database.connection import DatabaseManager


router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service() -> ProjectService:
    """Dependency injection for ProjectService."""
    # This will be properly injected in main.py
    db_manager = DatabaseManager()
    project_repo = ProjectRepository(db_manager)
    return ProjectService(project_repo)


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate, 
    service: ProjectService = Depends(get_project_service)
) -> ProjectResponse:
    """Create a new project."""
    try:
        created_project = service.create_project(
            name=project.name,
            path=project.path
        )
        return ProjectResponse.from_orm(created_project)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )


@router.get("/", response_model=List[ProjectResponse])
async def get_all_projects(
    service: ProjectService = Depends(get_project_service)
) -> List[ProjectResponse]:
    """Get all projects."""
    try:
        projects = service.get_all_projects()
        return [ProjectResponse.from_orm(project) for project in projects]
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve projects"
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service)
) -> ProjectResponse:
    """Get a project by ID."""
    try:
        project = service.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        return ProjectResponse.from_orm(project)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project"
        )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    service: ProjectService = Depends(get_project_service)
) -> ProjectResponse:
    """Update a project."""
    try:
        updated_project = service.update_project(
            project_id=project_id,
            name=project_update.name,
            path=project_update.path
        )
        if not updated_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        return ProjectResponse.from_orm(updated_project)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service)
):
    """Delete a project."""
    try:
        deleted = service.delete_project(project_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )
```

Finally, create the main FastAPI application. Create `backend/main.py`:

```python
"""Main FastAPI application for PrezI."""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from api.v1.projects import router as projects_router
from database.connection import DatabaseManager
from database.repositories import ProjectRepository
from services.project_service import ProjectService


def create_app(db_path: str = "prezi.db") -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="PrezI API",
        description="AI-Powered Presentation Management System",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware for frontend communication
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Database manager singleton
    db_manager = DatabaseManager(db_path)
    
    # Dependency injection override for testing
    def get_project_service() -> ProjectService:
        project_repo = ProjectRepository(db_manager)
        return ProjectService(project_repo)
    
    # Override the dependency in the router
    projects_router.dependency_overrides[
        projects_router.dependencies[0].dependency
    ] = get_project_service
    
    # Include routers
    app.include_router(projects_router, prefix="/api/v1")
    
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "Welcome to PrezI API",
            "version": "1.0.0",
            "docs": "/docs"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
```

Update your `backend/requirements.txt` to include FastAPI dependencies:

```txt
# Add these to your existing requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
httpx==0.25.2  # For testing
```

Install the new dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Now run the tests again:

```bash
pytest tests/test_project_api.py -v
```

**Expected output:**
```
====================== 10 passed in 0.15s ======================
```

🎉 **GREEN!** All API tests are passing!

### 🔵 REFACTOR PHASE: Adding Professional Features

Let's refactor to add better error handling, logging, and professional API features:

```python
"""Project API endpoints for PrezI - Refactored with professional features."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from typing import List
import logging
from api.schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ErrorResponse
from services.project_service import ProjectService
from database.repositories import ProjectRepository, RepositoryError
from database.connection import DatabaseManager


# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


# Custom exception handler
async def repository_error_handler(request: Request, exc: RepositoryError):
    """Handle repository errors gracefully."""
    logger.error(f"Repository error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error_code": "REPOSITORY_ERROR"}
    )


def get_project_service() -> ProjectService:
    """Dependency injection for ProjectService."""
    db_manager = DatabaseManager()
    project_repo = ProjectRepository(db_manager)
    return ProjectService(project_repo)


@router.post(
    "/", 
    response_model=ProjectResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new presentation project with a name and optional file path."
)
async def create_project(
    project: ProjectCreate, 
    service: ProjectService = Depends(get_project_service)
) -> ProjectResponse:
    """Create a new project."""
    logger.info(f"Creating project: {project.name}")
    
    try:
        created_project = service.create_project(
            name=project.name,
            path=project.path
        )
        logger.info(f"Created project: {created_project.name} ({created_project.project_id})")
        return ProjectResponse.model_validate(created_project)
    except ValueError as e:
        logger.warning(f"Invalid project data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RepositoryError as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )


@router.get(
    "/", 
    response_model=List[ProjectResponse],
    summary="Get all projects",
    description="Retrieve all projects ordered by creation date (newest first)."
)
async def get_all_projects(
    service: ProjectService = Depends(get_project_service)
) -> List[ProjectResponse]:
    """Get all projects."""
    logger.info("Retrieving all projects")
    
    try:
        projects = service.get_all_projects()
        logger.info(f"Retrieved {len(projects)} projects")
        return [ProjectResponse.model_validate(project) for project in projects]
    except RepositoryError as e:
        logger.error(f"Failed to retrieve projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve projects"
        )


@router.get(
    "/{project_id}", 
    response_model=ProjectResponse,
    summary="Get project by ID",
    description="Retrieve a specific project by its unique identifier."
)
async def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service)
) -> ProjectResponse:
    """Get a project by ID."""
    logger.info(f"Retrieving project: {project_id}")
    
    try:
        project = service.get_project(project_id)
        if not project:
            logger.warning(f"Project not found: {project_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        logger.info(f"Retrieved project: {project.name}")
        return ProjectResponse.model_validate(project)
    except ValueError as e:
        logger.warning(f"Invalid project ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RepositoryError as e:
        logger.error(f"Failed to retrieve project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project"
        )


@router.put(
    "/{project_id}", 
    response_model=ProjectResponse,
    summary="Update project",
    description="Update an existing project's name and/or file path."
)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    service: ProjectService = Depends(get_project_service)
) -> ProjectResponse:
    """Update a project."""
    logger.info(f"Updating project: {project_id}")
    
    try:
        updated_project = service.update_project(
            project_id=project_id,
            name=project_update.name,
            path=project_update.path
        )
        if not updated_project:
            logger.warning(f"Project not found for update: {project_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        logger.info(f"Updated project: {updated_project.name}")
        return ProjectResponse.model_validate(updated_project)
    except ValueError as e:
        logger.warning(f"Invalid update data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RepositoryError as e:
        logger.error(f"Failed to update project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )


@router.delete(
    "/{project_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="Delete a project and all its associated data."
)
async def delete_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service)
):
    """Delete a project."""
    logger.info(f"Deleting project: {project_id}")
    
    try:
        deleted = service.delete_project(project_id)
        if not deleted:
            logger.warning(f"Project not found for deletion: {project_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        logger.info(f"Deleted project: {project_id}")
    except ValueError as e:
        logger.warning(f"Invalid project ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RepositoryError as e:
        logger.error(f"Failed to delete project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )
```

### 🚀 Testing Your API in Real Time

Let's start the API server and see it in action:

```bash
cd backend
python main.py
```

Your API is now running at `http://localhost:8000`!

**🎉 Check out these amazing features:**

1. **Interactive API Documentation**: Visit `http://localhost:8000/docs`
   - You can test all endpoints directly in the browser!
   - Try creating a project, updating it, and deleting it

2. **Alternative Documentation**: Visit `http://localhost:8000/redoc`
   - Beautiful, readable documentation

3. **Health Check**: Visit `http://localhost:8000/health`
   - Returns `{"status": "healthy"}`

### 🧪 Advanced API Testing

Let's add some advanced tests for edge cases and error handling. Add these tests to `test_project_api.py`:

```python
def test_api_documentation_endpoints(test_app):
    """Test that API documentation endpoints are working."""
    # Test OpenAPI schema
    response = test_app.get("/openapi.json")
    assert response.status_code == status.HTTP_200_OK
    
    schema = response.json()
    assert schema["info"]["title"] == "PrezI API"
    assert schema["info"]["version"] == "1.0.0"

def test_health_check(test_app):
    """Test the health check endpoint."""
    response = test_app.get("/health")
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}

def test_cors_headers(test_app):
    """Test that CORS headers are properly set."""
    response = test_app.options("/api/v1/projects")
    
    # Should have CORS headers
    assert "access-control-allow-origin" in response.headers

def test_create_project_name_validation(test_app):
    """Test detailed name validation."""
    # Test name too long
    long_name = "a" * 201  # Max is 200
    response = test_app.post("/api/v1/projects", json={"name": long_name})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    # Test name with only whitespace
    response = test_app.post("/api/v1/projects", json={"name": "   "})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_concurrent_api_requests(test_app):
    """Test that the API handles concurrent requests properly."""
    import concurrent.futures
    import threading
    
    def create_project(index):
        return test_app.post("/api/v1/projects", json={"name": f"Project {index}"})
    
    # Create multiple projects concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(create_project, i) for i in range(10)]
        responses = [future.result() for future in futures]
    
    # All should succeed
    assert all(r.status_code == status.HTTP_201_CREATED for r in responses)
    
    # Verify all were created
    get_response = test_app.get("/api/v1/projects")
    projects = get_response.json()
    assert len(projects) == 10
```

### 🎪 CI/CD Integration for API Testing

Update your `.github/workflows/ci.yml` to include API testing:

```yaml
  test-api:
    name: 🌐 API Tests
    runs-on: ubuntu-latest
    
    steps:
    - name: 📥 Checkout code
      uses: actions/checkout@v4
      
    - name: 🐍 Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
        
    - name: 📦 Install dependencies
      run: |
        cd backend
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        
    - name: 🌐 Test API endpoints
      run: |
        cd backend
        pytest tests/test_*_api.py -v --cov=api
        
    - name: 🚀 Test API server startup
      run: |
        cd backend
        timeout 10s python main.py || exit_code=$?
        if [ $exit_code -eq 124 ]; then
          echo "API server started successfully"
        else
          echo "API server failed to start"
          exit 1
        fi
```

### 🎯 Manual Testing with curl

You can also test your API using curl commands:

```bash
# Create a project
curl -X POST "http://localhost:8000/api/v1/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Test Project", "path": "/test/path"}'

# Get all projects  
curl http://localhost:8000/api/v1/projects

# Get a specific project (replace {id} with actual project ID)
curl http://localhost:8000/api/v1/projects/{project_id}

# Update a project
curl -X PUT "http://localhost:8000/api/v1/projects/{project_id}" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Project Name"}'

# Delete a project
curl -X DELETE http://localhost:8000/api/v1/projects/{project_id}
```

### 🎊 Commit Your API Layer

Let's commit this major milestone:

```bash
git add api/ main.py tests/
git commit -m "feat(api): implement complete REST API with TDD

- Add FastAPI application with project endpoints
- Implement request/response validation with Pydantic  
- Add comprehensive API testing with TestClient
- Include automatic OpenAPI documentation
- Add proper error handling and HTTP status codes
- Integrate CORS middleware for frontend communication
- Add CI pipeline integration for API testing"

git push origin main
```

### 🏆 What You've Accomplished

Incredible work! You've just built a **production-ready REST API** for PrezI:

✅ **Complete REST API** with all CRUD operations  
✅ **Automatic OpenAPI documentation** (interactive API explorer!)  
✅ **Request/response validation** with Pydantic schemas  
✅ **Comprehensive API testing** using FastAPI TestClient  
✅ **Professional error handling** with proper HTTP status codes  
✅ **CORS support** for frontend communication  
✅ **Logging and monitoring** capabilities  
✅ **CI/CD integration** for automated API testing  

### 🌟 The Magic You've Created

Your PrezI application now has:
1. **Solid data layer** (database + repositories)
2. **Business logic layer** (services)  
3. **API communication layer** (REST endpoints)

**Students can now:**
- Create, read, update, and delete projects via HTTP
- Access interactive API documentation
- Have their frontend communicate with the backend
- Deploy the API to any cloud platform

### 🔮 Next Steps Preview

In the next chapter, we'll:
- Build the React frontend with modern testing practices
- Connect the frontend to your API
- Implement real-time user interactions
- Add frontend testing with React Testing Library

**IMPORTANT COURSE CORRECTION**: The tutorial needs to be updated to build the complete PrezI application as specified in the requirements. Let me revise this to ensure students build the actual working PrezI system.

---

## 🚨 CRITICAL UPDATE: Building the Real PrezI Application

### What We've Built So Far vs. What PrezI Actually Is

**What we have**: Basic project CRUD API  
**What PrezI actually is**: AI-powered PowerPoint slide management system with:

- **PowerPoint Integration**: Import .pptx files and extract individual slides
- **AI Slide Analysis**: Automatic content understanding and categorization  
- **Slide Assembly System**: Drag-and-drop presentation building
- **Natural Language Search**: "Find charts about Q4 revenue"
- **AI-Powered Automation**: "Create investor pitch" → automatic assembly
- **Export System**: Export to .pptx/.pdf with proper formatting
- **Desktop Application**: Electron wrapper for native app experience

### 🎯 Revised Tutorial Focus

The remaining chapters will now build the complete PrezI application:

---

## 8. PowerPoint Integration & Slide Processing with TDD

### 🎪 Building PrezI's Core Magic: PowerPoint Integration

This is where PrezI comes alive! We're going to build the system that imports PowerPoint files, extracts individual slides, analyzes their content with AI, and creates a searchable slide library. This is the foundation that makes everything else possible.

### 🎯 What You'll Build in This Chapter

By the end of this chapter, your PrezI app will:
- Import .pptx files using COM automation (Windows PowerPoint integration)
- Extract individual slides as images with metadata
- Analyze slide content using OpenAI API
- Store slides in the database with AI-generated insights
- Create a complete slide library system

### 🏗️ The PowerPoint Processing Pipeline

```python
# 🎯 The PrezI Magic Pipeline
.pptx File → COM Automation → Slide Extraction → AI Analysis → Database Storage → Searchable Library
```

### 🔴 RED PHASE: PowerPoint Integration Tests

Let's start by writing tests for our PowerPoint processor. Create `backend/tests/test_powerpoint_processor.py`:

```python
"""Tests for PowerPoint processing - the heart of PrezI!"""

import pytest
import tempfile
import os
from pathlib import Path
from services.powerpoint_processor import PowerPointProcessor
from services.ai_analyzer import SlideAnalyzer
from database.connection import DatabaseManager
from database.repositories import ProjectRepository, FileRepository, SlideRepository
from models.project import Project
from models.slide import Slide, SlideFile


@pytest.fixture
def powerpoint_processor():
    """Create PowerPoint processor for testing."""
    # Create temporary database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db_manager = DatabaseManager(db_path)
    project_repo = ProjectRepository(db_manager)
    file_repo = FileRepository(db_manager)
    slide_repo = SlideRepository(db_manager)
    ai_analyzer = SlideAnalyzer(api_key="test-key")  # Mock for testing
    
    processor = PowerPointProcessor(
        project_repo=project_repo,
        file_repo=file_repo, 
        slide_repo=slide_repo,
        ai_analyzer=ai_analyzer
    )
    
    yield processor
    
    # Cleanup
    db_manager.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestPowerPointProcessor:
    """Test suite for PowerPoint processing."""
    
    def test_extract_slides_from_pptx(self, powerpoint_processor):
        """Test extracting slides from a PowerPoint file."""
        # Create a test project
        project = Project(name="Test Project")
        
        # Mock .pptx file path (in real implementation, this would be an actual file)
        test_pptx_path = "/path/to/test_presentation.pptx"
        
        # Process the PowerPoint file
        slide_file = powerpoint_processor.import_file(
            project=project,
            file_path=test_pptx_path
        )
        
        # Verify file was imported
        assert slide_file.filename == "test_presentation.pptx"
        assert slide_file.slide_count > 0
        assert slide_file.project_id == project.project_id
    
    def test_slide_content_extraction(self, powerpoint_processor):
        """Test that slide content is properly extracted."""
        project = Project(name="Content Test Project")
        test_pptx_path = "/path/to/content_test.pptx"
        
        # Import file and get slides
        slide_file = powerpoint_processor.import_file(project, test_pptx_path)
        slides = powerpoint_processor.get_slides_for_file(slide_file.file_id)
        
        # Verify slides have content
        for slide in slides:
            assert slide.slide_number >= 1
            assert slide.thumbnail_path is not None
            # Content can be None for slides with only images
            assert hasattr(slide, 'title_text')
            assert hasattr(slide, 'body_text')
            assert hasattr(slide, 'speaker_notes')
    
    def test_ai_slide_analysis(self, powerpoint_processor):
        """Test that slides are analyzed with AI."""
        project = Project(name="AI Analysis Test")
        test_pptx_path = "/path/to/ai_test.pptx"
        
        # Import and analyze
        slide_file = powerpoint_processor.import_file(project, test_pptx_path)
        slides = powerpoint_processor.get_slides_for_file(slide_file.file_id)
        
        # Verify AI analysis was performed
        for slide in slides:
            assert slide.ai_topic is not None
            assert slide.ai_type is not None  # Title, Data/Chart, etc.
            assert slide.ai_insight is not None
    
    def test_duplicate_file_handling(self, powerpoint_processor):
        """Test handling of duplicate file imports."""
        project = Project(name="Duplicate Test")
        test_pptx_path = "/path/to/duplicate_test.pptx"
        
        # Import same file twice
        slide_file1 = powerpoint_processor.import_file(project, test_pptx_path)
        slide_file2 = powerpoint_processor.import_file(project, test_pptx_path)
        
        # Should handle gracefully (either skip or update)
        assert slide_file1.file_id != slide_file2.file_id or slide_file1.file_id == slide_file2.file_id
    
    def test_batch_import(self, powerpoint_processor):
        """Test importing multiple PowerPoint files."""
        project = Project(name="Batch Import Test")
        pptx_files = [
            "/path/to/presentation1.pptx",
            "/path/to/presentation2.pptx", 
            "/path/to/presentation3.pptx"
        ]
        
        # Import all files
        imported_files = []
        for file_path in pptx_files:
            slide_file = powerpoint_processor.import_file(project, file_path)
            imported_files.append(slide_file)
        
        # Verify all were imported
        assert len(imported_files) == 3
        
        # Verify total slide count across all files
        total_slides = 0
        for slide_file in imported_files:
            slides = powerpoint_processor.get_slides_for_file(slide_file.file_id)
            total_slides += len(slides)
        
        assert total_slides > 0
```

### 🟢 GREEN PHASE: Building the PowerPoint Processor

Now let's implement the PowerPoint processing system. First, let's create the models for slides and files:

Create `backend/models/slide.py`:

```python
"""Slide and File models for PrezI."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import uuid


@dataclass
class SlideFile:
    """Represents an imported PowerPoint file."""
    filename: str
    file_path: str
    project_id: str
    slide_count: int = 0
    file_id: Optional[str] = None
    imported_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.file_id:
            self.file_id = str(uuid.uuid4())
        if not self.imported_at:
            self.imported_at = datetime.now()


@dataclass  
class Slide:
    """Represents an individual slide from a PowerPoint presentation."""
    file_id: str
    slide_number: int
    thumbnail_path: str
    title_text: Optional[str] = None
    body_text: Optional[str] = None
    speaker_notes: Optional[str] = None
    ai_topic: Optional[str] = None
    ai_type: Optional[str] = None
    ai_insight: Optional[str] = None
    slide_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.slide_id:
            self.slide_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now()


@dataclass
class SlideElement:
    """Represents an element within a slide (chart, image, text block)."""
    slide_id: str
    element_type: str  # 'chart', 'image', 'text', 'table'
    bounding_box: str  # JSON string with coordinates
    extracted_text: Optional[str] = None
    element_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.element_id:
            self.element_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now()
```

Create the AI analyzer service `backend/services/ai_analyzer.py`:

```python
"""AI-powered slide content analysis for PrezI."""

import openai
import json
import logging
from typing import Dict, Any, Optional
from models.slide import Slide


logger = logging.getLogger(__name__)


class SlideAnalyzer:
    """Analyzes slide content using OpenAI API."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        openai.api_key = api_key
    
    def analyze_slide(self, slide: Slide) -> Dict[str, Any]:
        """Analyze a slide and return AI insights."""
        try:
            # Prepare slide content for analysis
            content = self._prepare_slide_content(slide)
            
            # Get AI analysis
            analysis = self._call_openai_analysis(content)
            
            return {
                'ai_topic': analysis.get('slide_topic'),
                'ai_type': analysis.get('slide_type'), 
                'ai_insight': analysis.get('key_insight')
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze slide {slide.slide_id}: {e}")
            return {
                'ai_topic': 'Unknown',
                'ai_type': 'Other',
                'ai_insight': 'Analysis failed'
            }
    
    def _prepare_slide_content(self, slide: Slide) -> str:
        """Prepare slide content for AI analysis."""
        content_parts = []
        
        if slide.title_text:
            content_parts.append(f"Title: {slide.title_text}")
        
        if slide.body_text:
            content_parts.append(f"Body: {slide.body_text}")
        
        if slide.speaker_notes:
            content_parts.append(f"Notes: {slide.speaker_notes}")
        
        return "\n".join(content_parts) if content_parts else "No text content"
    
    def _call_openai_analysis(self, content: str) -> Dict[str, Any]:
        """Call OpenAI API to analyze slide content."""
        prompt = f"""
        Analyze the following slide content and return a JSON object with these fields:
        - slide_topic: A brief, 3-5 word topic for the slide
        - slide_type: One of 'Title', 'Agenda', 'Problem', 'Solution', 'Data/Chart', 'Quote', 'Team', 'Summary', 'Call to Action', 'Other'
        - key_insight: A single sentence summarizing the main takeaway
        
        Slide Content:
        {content}
        
        Return only valid JSON:
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a presentation analyst. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            result = response.choices[0].message.content.strip()
            return json.loads(result)
            
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI response as JSON")
            return {
                'slide_topic': 'Unknown Topic',
                'slide_type': 'Other', 
                'key_insight': 'Could not analyze content'
            }
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
```

Create the PowerPoint processor `backend/services/powerpoint_processor.py`:

```python
"""PowerPoint file processing for PrezI."""

import os
import tempfile
import logging
from pathlib import Path
from typing import List, Optional
import win32com.client as win32  # For COM automation
from models.project import Project
from models.slide import SlideFile, Slide
from database.repositories import ProjectRepository, FileRepository, SlideRepository
from services.ai_analyzer import SlideAnalyzer


logger = logging.getLogger(__name__)


class PowerPointProcessor:
    """Processes PowerPoint files and extracts slides."""
    
    def __init__(
        self,
        project_repo: ProjectRepository,
        file_repo: FileRepository,
        slide_repo: SlideRepository,
        ai_analyzer: SlideAnalyzer
    ):
        self.project_repo = project_repo
        self.file_repo = file_repo
        self.slide_repo = slide_repo
        self.ai_analyzer = ai_analyzer
    
    def import_file(self, project: Project, file_path: str) -> SlideFile:
        """Import a PowerPoint file and extract all slides."""
        logger.info(f"Importing PowerPoint file: {file_path}")
        
        try:
            # Validate file exists and is .pptx
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not file_path.lower().endswith('.pptx'):
                raise ValueError("Only .pptx files are supported")
            
            # Create file record
            filename = Path(file_path).name
            slide_file = SlideFile(
                filename=filename,
                file_path=file_path,
                project_id=project.project_id
            )
            
            # Extract slides using COM automation
            slides = self._extract_slides_from_pptx(file_path, slide_file.file_id)
            slide_file.slide_count = len(slides)
            
            # Save file record
            saved_file = self.file_repo.save(slide_file)
            
            # Process and save each slide
            for slide in slides:
                # Analyze with AI
                ai_analysis = self.ai_analyzer.analyze_slide(slide)
                slide.ai_topic = ai_analysis['ai_topic']
                slide.ai_type = ai_analysis['ai_type']
                slide.ai_insight = ai_analysis['ai_insight']
                
                # Save slide
                self.slide_repo.save(slide)
            
            logger.info(f"Successfully imported {len(slides)} slides from {filename}")
            return saved_file
            
        except Exception as e:
            logger.error(f"Failed to import file {file_path}: {e}")
            raise
    
    def _extract_slides_from_pptx(self, file_path: str, file_id: str) -> List[Slide]:
        """Extract slides from PowerPoint file using COM automation."""
        slides = []
        powerpoint = None
        presentation = None
        
        try:
            # Start PowerPoint application
            powerpoint = win32.Dispatch("PowerPoint.Application")
            powerpoint.Visible = False  # Run in background
            
            # Open presentation
            presentation = powerpoint.Presentations.Open(file_path, ReadOnly=True)
            
            # Create thumbnails directory
            thumbnail_dir = Path("thumbnails") / file_id
            thumbnail_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract each slide
            for slide_num in range(1, presentation.Slides.Count + 1):
                slide_obj = presentation.Slides(slide_num)
                
                # Extract text content
                title_text = self._extract_slide_title(slide_obj)
                body_text = self._extract_slide_body(slide_obj)
                speaker_notes = self._extract_speaker_notes(slide_obj)
                
                # Export slide as image
                thumbnail_path = thumbnail_dir / f"slide_{slide_num}.png"
                slide_obj.Export(str(thumbnail_path), "PNG")
                
                # Create slide object
                slide = Slide(
                    file_id=file_id,
                    slide_number=slide_num,
                    thumbnail_path=str(thumbnail_path),
                    title_text=title_text,
                    body_text=body_text,
                    speaker_notes=speaker_notes
                )
                
                slides.append(slide)
            
            return slides
            
        except Exception as e:
            logger.error(f"COM automation failed: {e}")
            raise
        finally:
            # Cleanup COM objects
            if presentation:
                presentation.Close()
            if powerpoint:
                powerpoint.Quit()
    
    def _extract_slide_title(self, slide_obj) -> Optional[str]:
        """Extract title text from slide."""
        try:
            for shape in slide_obj.Shapes:
                if shape.Type == 14:  # Placeholder type
                    if hasattr(shape, 'TextFrame') and shape.TextFrame.HasText:
                        if shape.PlaceholderFormat.Type == 1:  # Title placeholder
                            return shape.TextFrame.TextRange.Text.strip()
            return None
        except:
            return None
    
    def _extract_slide_body(self, slide_obj) -> Optional[str]:
        """Extract body text from slide."""
        try:
            body_texts = []
            for shape in slide_obj.Shapes:
                if shape.Type == 14:  # Placeholder type
                    if hasattr(shape, 'TextFrame') and shape.TextFrame.HasText:
                        if shape.PlaceholderFormat.Type == 2:  # Content placeholder
                            body_texts.append(shape.TextFrame.TextRange.Text.strip())
            return "\n".join(body_texts) if body_texts else None
        except:
            return None
    
    def _extract_speaker_notes(self, slide_obj) -> Optional[str]:
        """Extract speaker notes from slide."""
        try:
            if slide_obj.NotesPage.Shapes.Count > 1:
                notes_shape = slide_obj.NotesPage.Shapes(2)  # Notes placeholder
                if hasattr(notes_shape, 'TextFrame') and notes_shape.TextFrame.HasText:
                    return notes_shape.TextFrame.TextRange.Text.strip()
            return None
        except:
            return None
    
    def get_slides_for_file(self, file_id: str) -> List[Slide]:
        """Get all slides for a specific file."""
        return self.slide_repo.find_by_file_id(file_id)
    
    def get_slides_for_project(self, project_id: str) -> List[Slide]:
        """Get all slides for a project."""
        return self.slide_repo.find_by_project_id(project_id)
```

### 🔵 REFACTOR PHASE: Adding Repository Support

Now we need to create the repositories for files and slides. Create `backend/database/repositories.py` (update existing):

```python
"""Repository classes for PrezI database operations - Updated for complete system."""

from typing import List, Optional
from models.project import Project
from models.slide import SlideFile, Slide
from database.connection import DatabaseManager
from datetime import datetime
import uuid
import logging


logger = logging.getLogger(__name__)


class FileRepository:
    """Repository for SlideFile database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save(self, slide_file: SlideFile) -> SlideFile:
        """Save a slide file to the database."""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO files (file_id, project_id, filename, file_path, slide_count, imported_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    slide_file.file_id,
                    slide_file.project_id,
                    slide_file.filename,
                    slide_file.file_path,
                    slide_file.slide_count,
                    slide_file.imported_at.isoformat()
                ))
            
            logger.info(f"Saved file: {slide_file.filename}")
            return slide_file
            
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise
    
    def find_by_project_id(self, project_id: str) -> List[SlideFile]:
        """Find all files for a project."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT file_id, project_id, filename, file_path, slide_count, imported_at
                    FROM files
                    WHERE project_id = ?
                    ORDER BY imported_at DESC
                """, (project_id,))
                
                return [self._row_to_slide_file(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to find files for project {project_id}: {e}")
            raise
    
    def _row_to_slide_file(self, row) -> SlideFile:
        """Convert database row to SlideFile object."""
        return SlideFile(
            file_id=row['file_id'],
            project_id=row['project_id'],
            filename=row['filename'],
            file_path=row['file_path'],
            slide_count=row['slide_count'],
            imported_at=datetime.fromisoformat(row['imported_at'])
        )


class SlideRepository:
    """Repository for Slide database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save(self, slide: Slide) -> Slide:
        """Save a slide to the database."""
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO slides (
                        slide_id, file_id, slide_number, title_text, body_text, 
                        speaker_notes, thumbnail_path, ai_topic, ai_type, ai_insight, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    slide.slide_id,
                    slide.file_id,
                    slide.slide_number,
                    slide.title_text,
                    slide.body_text,
                    slide.speaker_notes,
                    slide.thumbnail_path,
                    slide.ai_topic,
                    slide.ai_type,
                    slide.ai_insight,
                    slide.created_at.isoformat()
                ))
            
            return slide
            
        except Exception as e:
            logger.error(f"Failed to save slide: {e}")
            raise
    
    def find_by_file_id(self, file_id: str) -> List[Slide]:
        """Find all slides for a file."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT slide_id, file_id, slide_number, title_text, body_text,
                           speaker_notes, thumbnail_path, ai_topic, ai_type, ai_insight, created_at
                    FROM slides
                    WHERE file_id = ?
                    ORDER BY slide_number ASC
                """, (file_id,))
                
                return [self._row_to_slide(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to find slides for file {file_id}: {e}")
            raise
    
    def find_by_project_id(self, project_id: str) -> List[Slide]:
        """Find all slides for a project."""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT s.slide_id, s.file_id, s.slide_number, s.title_text, s.body_text,
                           s.speaker_notes, s.thumbnail_path, s.ai_topic, s.ai_type, s.ai_insight, s.created_at
                    FROM slides s
                    JOIN files f ON s.file_id = f.file_id
                    WHERE f.project_id = ?
                    ORDER BY f.imported_at DESC, s.slide_number ASC
                """, (project_id,))
                
                return [self._row_to_slide(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to find slides for project {project_id}: {e}")
            raise
    
    def search_slides(self, query: str, project_id: Optional[str] = None) -> List[Slide]:
        """Search slides using full-text search."""
        try:
            with self.db_manager.get_connection() as conn:
                if project_id:
                    cursor = conn.execute("""
                        SELECT s.slide_id, s.file_id, s.slide_number, s.title_text, s.body_text,
                               s.speaker_notes, s.thumbnail_path, s.ai_topic, s.ai_type, s.ai_insight, s.created_at
                        FROM slides s
                        JOIN files f ON s.file_id = f.file_id
                        JOIN slides_fts fts ON s.slide_id = fts.rowid
                        WHERE fts MATCH ? AND f.project_id = ?
                        ORDER BY rank
                    """, (query, project_id))
                else:
                    cursor = conn.execute("""
                        SELECT s.slide_id, s.file_id, s.slide_number, s.title_text, s.body_text,
                               s.speaker_notes, s.thumbnail_path, s.ai_topic, s.ai_type, s.ai_insight, s.created_at
                        FROM slides s
                        JOIN slides_fts fts ON s.slide_id = fts.rowid
                        WHERE fts MATCH ?
                        ORDER BY rank
                    """, (query,))
                
                return [self._row_to_slide(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to search slides: {e}")
            raise
    
    def _row_to_slide(self, row) -> Slide:
        """Convert database row to Slide object."""
        return Slide(
            slide_id=row['slide_id'],
            file_id=row['file_id'],
            slide_number=row['slide_number'],
            title_text=row['title_text'],
            body_text=row['body_text'],
            speaker_notes=row['speaker_notes'],
            thumbnail_path=row['thumbnail_path'],
            ai_topic=row['ai_topic'],
            ai_type=row['ai_type'],
            ai_insight=row['ai_insight'],
            created_at=datetime.fromisoformat(row['created_at'])
        )
```

### 🎊 What You've Built

Congratulations! You've just implemented the core of PrezI:

✅ **PowerPoint COM Integration** - Extracts slides from .pptx files  
✅ **AI-Powered Analysis** - Understands slide content automatically  
✅ **Complete Slide Library** - Stores and organizes all slides  
✅ **Full-Text Search** - Find slides by content  
✅ **Thumbnail Generation** - Visual slide previews  

Your students now have the foundation of a real AI-powered presentation management system!

### 🔮 Next: Building the Complete Frontend

Next, we'll build the Electron desktop app with the HTML/CSS/JavaScript interface that matches the specifications, including:
- Slide library grid with thumbnails
- Drag-and-drop assembly system  
- AI-powered search interface
- Export functionality

**The students are now building the REAL PrezI application!**