# 🧭 Module 3: Professional Git Workflow - Your Development Compass
## *Master the collaboration and version control skills used by top tech companies*

**Module:** 03 | **Phase:** Foundations  
**Duration:** 3 hours | **Prerequisites:** Module 02  
**Learning Track:** Professional Version Control and Collaboration  

---

## 🎯 Module Objectives

By completing this module, you will:
- [ ] Master modern Git workflows (GitHub Flow vs GitFlow)
- [ ] Implement professional branching strategies
- [ ] Write industry-standard commit messages
- [ ] Understand how Git integrates with CI/CD
- [ ] Establish your professional development rhythm
- [ ] Set up collaborative development practices

---

## 🧭 Git is Your Time Machine and Collaboration Superpower

Imagine if you could:
- Save your game at any point and return to it later
- See exactly what changed between save points
- Collaborate with friends on the same game without overwriting each other's work
- Automatically merge everyone's contributions

**That's Git!** And in professional development, knowing Git isn't optional - it's like knowing how to use email in a business setting.

---

## 🌊 Modern Git Workflows: From Complex to Simple

The industry has evolved from complex workflows to simpler, more agile approaches:

### 🏭 **GitFlow** (The Old Way - Complex but Structured)
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

**Branches**:
- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/***: Individual feature development
- **release/***: Preparing releases
- **hotfix/***: Emergency production fixes

### 🚀 **GitHub Flow** (The Modern Way - Simple and Fast)
Like a nimble startup:
```
main ────●───●───●───●───●───●─────
          │   │   │   │   │   │
feature   ●───●   ●───●   ●───●
```

**When to use**: Small to medium teams, continuous deployment, frequent releases *(this is what we'll use for PrezI!)*

**Branches**:
- **main**: Always production-ready
- **feature/***: All development work

**Why simpler is better**:
- Faster feedback cycles
- Less merge conflicts
- Easier to understand
- Better for continuous deployment

---

## 🎮 Your Git Workflow for PrezI

We'll use a **modified GitHub Flow** that includes professional CI/CD practices:

### Step 1: Feature Branch Creation
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

### Step 2: TDD Development Cycle
```bash
# Work in TDD cycles: Red → Green → Refactor
git add test_user_authentication.py
git commit -m "RED: Add failing test for user login validation"

git add user_authentication.py
git commit -m "GREEN: Implement basic user login validation"

git add user_authentication.py
git commit -m "REFACTOR: Improve error handling and add type hints"
```

### Step 3: Continuous Integration (CI) Magic ✨
When you push your branch:
```bash
git push origin feature/user-authentication-tdd
```

**GitHub Actions automatically**:
1. Runs ALL your tests
2. Checks code quality (linting)
3. Verifies security (dependency scanning)
4. Reports results back to you

### Step 4: Professional Code Review
```bash
# Create a Pull Request (PR) through GitHub UI
# Your PR triggers:
# - Automated tests
# - Code review from teammates
# - Continuous integration checks
```

### Step 5: Automated Deployment (CD) 🚀
When your PR is approved and merged:
```bash
# GitHub Actions automatically:
# 1. Runs final test suite
# 2. Builds the application
# 3. Deploys to staging environment
# 4. (Eventually) deploys to production
```

---

## 🎯 Professional Commit Message Format

Your commit messages should tell a story. Use this format:

```
type(scope): brief description

Longer explanation if needed.

- Additional bullet points
- Can provide more context
```

### Commit Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **test**: Adding or modifying tests
- **refactor**: Code refactoring
- **ci**: CI/CD changes
- **chore**: Maintenance tasks

### Examples for PrezI
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

---

## 🔄 The Professional Development Rhythm

Here's your daily workflow rhythm as a professional developer:

### **Morning Sync**:
```bash
git checkout main
git pull origin main  # Get latest changes
git checkout feature/my-current-work
git rebase main      # Integrate latest changes into your work
```

### **Development Cycle** (repeat throughout the day):
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

### **End of Day**:
```bash
git push origin feature/my-current-work  # Backup your work
# Create PR when feature is complete
```

---

## 🏆 Why This Workflow Rocks

### 1. **Safety Net** 🛡️
Your tests prevent you from breaking existing code. Every change is verified automatically.

### 2. **Collaboration** 🤝
Multiple developers can work simultaneously without conflicts. Git handles the complexity.

### 3. **Quality** ✨
Automated checks catch issues before they reach production. Code review ensures best practices.

### 4. **Documentation** 📚
Git history tells the story of how your code evolved. Future developers can understand decisions.

### 5. **Professional** 💼
This is exactly how top companies like Google, Microsoft, and Netflix manage code.

---

## 🛠️ Hands-On: Set Up Your PrezI Git Workflow

### Step 1: Create Your Repository
```bash
# Create new repository on GitHub (through web interface)
# Then clone it locally
git clone https://github.com/yourusername/prezi-capstone.git
cd prezi-capstone

# Set up initial structure
touch README.md
git add README.md
git commit -m "feat: initial project setup

- Add README with project description
- Establish repository for PrezI capstone project"

git push origin main
```

### Step 2: Configure Git for Professional Use
```bash
# Set your identity (use your real name and email)
git config user.name "Your Full Name"
git config user.email "your.email@example.com"

# Enable useful settings
git config pull.rebase true  # Use rebase instead of merge for pulls
git config branch.autosetupmerge always
git config branch.autosetuprebase always

# Set up default branch name
git config init.defaultBranch main
```

### Step 3: Create Your First Feature Branch
```bash
# Start your first TDD cycle
git checkout -b feature/project-model-tdd

# Create initial test file
mkdir -p tests/unit/models
touch tests/unit/models/test_project.py

# Add your first failing test
git add tests/
git commit -m "RED: add failing test for Project model creation"

# Push to create remote branch
git push -u origin feature/project-model-tdd
```

### Step 4: Practice the TDD + Git Rhythm
Complete the Project model from Module 2 using proper Git workflow:

1. **Red Phase**: Write failing test, commit with "RED:" prefix
2. **Green Phase**: Implement minimal code, commit with "GREEN:" prefix  
3. **Refactor Phase**: Improve code, commit with "REFACTOR:" prefix
4. **Push**: Share your work and trigger CI

---

## 🔧 Essential Git Commands for PrezI Development

### Daily Commands
```bash
# Check status
git status

# See what changed
git diff

# Add files to staging
git add filename
git add .  # Add all changes

# Commit changes
git commit -m "type(scope): description"

# Push changes
git push origin branch-name

# Pull latest changes
git pull origin main
```

### Branch Management
```bash
# List branches
git branch -a

# Create and switch to new branch
git checkout -b feature/new-feature

# Switch branches
git checkout branch-name

# Delete branch (locally)
git branch -d feature/completed-feature

# Delete branch (remotely)
git push origin --delete feature/completed-feature
```

### Emergency Commands
```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Stash uncommitted changes
git stash
git stash pop  # Restore stashed changes

# See commit history
git log --oneline --graph
```

---

## 🚨 Common Git Pitfalls (And How to Avoid Them)

### 1. **Committing to main branch directly**
```bash
# Wrong
git checkout main
git add .
git commit -m "made some changes"

# Right
git checkout -b feature/my-changes
git add .
git commit -m "feat(component): add new functionality"
```

### 2. **Vague commit messages**
```bash
# Wrong
git commit -m "fixed stuff"
git commit -m "updates"

# Right
git commit -m "fix(auth): resolve login validation bug
- Handle empty email addresses correctly
- Add appropriate error messages"
```

### 3. **Not pulling before starting work**
```bash
# Wrong
git checkout -b feature/new-work  # Might be outdated

# Right
git checkout main
git pull origin main
git checkout -b feature/new-work
```

### 4. **Committing too much at once**
```bash
# Wrong
git add .  # 50 files changed
git commit -m "implemented entire user system"

# Right
# Make small, focused commits
git add user_model.py
git commit -m "feat(models): add User model with validation"
git add test_user_model.py
git commit -m "test(models): add comprehensive User model tests"
```

---

## 🎯 Integration with TDD and CI/CD

### How Git + TDD + CI/CD Work Together

1. **TDD drives code quality**: Tests ensure your code works
2. **Git tracks your progress**: Every TDD cycle is documented
3. **CI validates your work**: Automated testing on every push
4. **CD deploys when ready**: Automatic deployment when tests pass

### The Professional Development Loop
```
Write failing test (RED) → Commit → Push
         ↓
Implement code (GREEN) → Commit → Push → CI runs tests
         ↓
Refactor code (BLUE) → Commit → Push → CI validates
         ↓
Create PR → Code review → Merge → CD deploys
```

---

## 🚀 What's Next?

In the next module, **Environment Setup**, you'll:
- Configure your complete development environment
- Set up testing frameworks and CI/CD tools
- Install PrezI-specific dependencies
- Verify everything works together

### Preparation for Next Module
- [ ] Set up GitHub repository for PrezI
- [ ] Configure Git with professional settings
- [ ] Practice basic Git commands
- [ ] Complete first feature branch workflow

---

## 💡 Pro Tips for Git Mastery

### 1. Commit Early and Often
Small, frequent commits are better than large, infrequent ones:
```bash
# Good
git commit -m "feat(auth): add password validation"
git commit -m "test(auth): add password validation tests"
git commit -m "refactor(auth): improve error messages"

# Less ideal
git commit -m "complete authentication system"  # Too big
```

### 2. Use .gitignore Properly
Create a `.gitignore` file to exclude unnecessary files:
```gitignore
# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/
.coverage

# Virtual environments
venv/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# PrezI specific
*.pptx
dist/
build/
```

### 3. Write Commit Messages for Your Future Self
Imagine reading your commit message in 6 months. Will you understand what you did and why?

### 4. Use Branches Liberally
Don't be afraid to create branches for experiments:
```bash
git checkout -b experiment/new-idea
# Try something out
# If it works, merge it
# If not, delete the branch
```

---

## ✅ Module 3 Completion Checklist

Before proceeding to the next module, ensure you can:
- [ ] Explain the difference between GitFlow and GitHub Flow
- [ ] Create feature branches with proper naming
- [ ] Write professional commit messages
- [ ] Follow the TDD + Git development rhythm
- [ ] Set up a GitHub repository for PrezI
- [ ] Understand how Git integrates with CI/CD
- [ ] Use essential Git commands confidently

**Module Status:** ⬜ Complete | **Next Module:** [04-environment-setup.md](04-environment-setup.md)

---

## 📚 Additional Resources

- **Book**: "Pro Git" by Scott Chacon (free online)
- **Interactive Tutorial**: Learn Git Branching (learngitbranching.js.org)
- **GitHub Docs**: GitHub Flow guide
- **Practice**: Contribute to open source projects to practice workflow