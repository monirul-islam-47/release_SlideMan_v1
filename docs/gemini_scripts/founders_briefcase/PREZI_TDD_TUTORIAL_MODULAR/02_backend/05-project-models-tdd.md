# 🎯 Module 5: Your First TDD Cycle - Building Project Models
## *Experience the Red-Green-Refactor Magic with Real Code*

**Module:** 05 | **Phase:** Core Backend  
**Duration:** 4 hours | **Prerequisites:** Module 04 (Environment Setup)  
**Learning Track:** Domain Models with Test-Driven Development  

---

## 🎯 Module Objectives

By completing this module, you will:
- [ ] Execute your first complete TDD cycle in PrezI
- [ ] Build the core Project model with comprehensive tests
- [ ] Experience the Red-Green-Refactor rhythm firsthand
- [ ] Integrate TDD with your CI/CD pipeline
- [ ] Apply professional Git workflow with TDD commits
- [ ] Master test-first domain design

---

## 🎮 Time to Get Your Hands Dirty!

Now comes the moment you've been waiting for - **writing actual code using TDD!** We're going to build the core `Project` model for PrezI, and you'll experience the magical Red-Green-Refactor cycle firsthand.

Think of this like learning to ride a bike - it might feel wobbly at first, but once you get the rhythm, you'll wonder how you ever coded without TDD!

---

## 🎮 The Game Plan: Building a Project Model

Our PrezI application needs to manage presentation projects. Each project should:
- **Have a unique name** (required, non-empty)
- **Track when it was created** (automatic timestamping)
- **Store the file path** where presentations are stored
- **Have a unique identifier** for database operations
- **Validate input** to prevent invalid data

But here's the TDD twist - **we're going to write the tests BEFORE we write the Project class!**

---

## 🔴 RED PHASE: Writing Our First Failing Test

Let's start with the simplest possible test. Create `backend/tests/unit/models/test_project.py`:

```python
"""Tests for the Project model - our first TDD adventure!"""

import pytest
from datetime import datetime
from core.models.project import Project  # This doesn't exist yet - that's the point!


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

### The Moment of Truth - Watch It Fail!

Now let's run this test and watch it fail beautifully:

```bash
cd backend
pytest tests/unit/models/test_project.py -v
```

**Expected output:**
```
ImportError: No module named 'core.models.project'
```

🎉 **Congratulations!** You just wrote your first failing test! This is the "Red" phase - the test fails because the code doesn't exist yet.

**Why this is important:**
- You've defined the API before implementation
- You've thought about error cases upfront
- You have a clear goal for your implementation

---

## 🟢 GREEN PHASE: Making the Test Pass (Minimally)

Now we write **just enough** code to make our test pass. 

### Step 1: Create the Module Structure
```bash
mkdir -p backend/core/models
touch backend/core/__init__.py
touch backend/core/models/__init__.py
```

### Step 2: Implement the Minimal Project Model
Create `backend/core/models/project.py`:

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

### Step 3: Run the Test Again
```bash
pytest tests/unit/models/test_project.py -v
```

**Expected output:**
```
test_project.py::test_project_creation_with_name PASSED
test_project.py::test_project_requires_name PASSED

======================== 2 passed in 0.02s ========================
```

🎉 **GREEN!** Your tests are passing! Notice how we wrote the **minimal** code needed - no fancy features, no over-engineering.

**TDD Principle Applied:** Write the simplest code that makes the test pass. Don't add features that aren't tested.

---

## 🔵 REFACTOR PHASE: Making It Beautiful

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
    
    def __eq__(self, other) -> bool:
        """Compare projects for equality based on project_id."""
        if not isinstance(other, Project):
            return False
        return self.project_id == other.project_id
```

### Verify Refactoring Didn't Break Anything
```bash
pytest tests/unit/models/test_project.py -v
```

Still green? Perfect! That's the power of TDD - you can refactor fearlessly.

---

## 🚀 Adding More Features with TDD

Let's add more functionality using the Red-Green-Refactor cycle. Add these tests to `test_project.py`:

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


def test_project_equality():
    """Test that projects with same ID are equal."""
    project_id = "test-id-123"
    project1 = Project(name="Test", project_id=project_id)
    project2 = Project(name="Different Name", project_id=project_id)
    
    assert project1 == project2  # Same ID = equal projects


def test_project_inequality():
    """Test that projects with different IDs are not equal."""
    project1 = Project(name="Test")
    project2 = Project(name="Test")  # Same name, different auto-generated ID
    
    assert project1 != project2


@pytest.mark.parametrize("invalid_name", [
    "",           # Empty string
    "   ",        # Whitespace only
    None,         # None value
    123,          # Wrong type
])
def test_project_name_validation(invalid_name):
    """Test that various invalid names are rejected."""
    with pytest.raises(ValueError, match="Project name cannot be empty"):
        Project(name=invalid_name)
```

### Run the New Tests
```bash
pytest tests/unit/models/test_project.py -v
```

**Results**: Most tests should pass because our refactored code already handles these cases! This is TDD magic - good design emerges naturally.

If any tests fail, that's your cue to update the implementation (Green phase) and then refactor.

---

## 🎪 Your First CI/CD Integration

Now let's see your TDD tests work with your CI pipeline!

### Professional Git Commit
```bash
# Stage your changes
git add core/ tests/

# Commit with a descriptive message following conventional commits
git commit -m "feat(models): implement Project model with TDD

- Add Project class with comprehensive validation
- Include unique ID generation and path support
- Add extensive test coverage with edge cases
- Follow TDD Red-Green-Refactor cycle
- Support equality comparison and string representations

Tests: 8 passing, 0 failing
Coverage: 100% of Project model"

# Push to trigger CI pipeline
git push origin main
```

### What Happens Next (CI/CD Magic)
1. **GitHub Actions detects your push**
2. **Automatically sets up Python environment**
3. **Installs your dependencies**
4. **Runs ALL your tests** (including your new Project tests)
5. **Checks code quality** (linting, security)
6. **Reports results back to GitHub**

You can watch this happen in real-time by going to your GitHub repository → Actions tab!

---

## 🧠 What You Just Learned

In this first TDD cycle, you experienced:

### TDD Cycle Mastery
✅ **Red Phase**: Writing failing tests that describe desired behavior  
✅ **Green Phase**: Writing minimal code to make tests pass  
✅ **Refactor Phase**: Improving code quality while maintaining green tests  

### Professional Practices
✅ **CI Integration**: Your tests automatically run on every commit  
✅ **Professional Git Workflow**: Descriptive commits that tell a story  
✅ **Code Quality**: Comprehensive test coverage and clean code  

### Design Benefits
✅ **API-First Design**: Tests defined the interface before implementation  
✅ **Edge Case Handling**: Validation logic emerged from test requirements  
✅ **Maintainable Code**: Easy to modify with test safety net  

---

## 🎯 TDD Principles You Applied

### 1. **Test-First Design**
You thought about the API and behavior before writing implementation code. This leads to:
- Cleaner interfaces
- Better error handling
- User-focused design

### 2. **Incremental Development**
Small steps with frequent feedback:
- Write one test → Make it pass → Refactor → Repeat
- Reduces debugging time
- Maintains momentum

### 3. **Safety Net**
Tests protect you during refactoring:
- Confident code changes
- Catch regressions immediately
- Enable fearless improvement

### 4. **Living Documentation**
Your tests document how the code should behave:
- Examples of correct usage
- Clear error conditions
- Specification that stays up-to-date

---

## 🔄 Practice: Add More TDD Cycles

Now it's your turn! Practice the TDD cycle by adding these features:

### Challenge 1: Project File Count
Add a method to track how many PowerPoint files are in a project.

```python
# Start with a test (RED)
def test_project_file_count_starts_at_zero():
    """New projects should start with zero files."""
    project = Project(name="Empty Project")
    assert project.file_count == 0

def test_project_can_add_file():
    """Projects should be able to track added files."""
    project = Project(name="Project with Files")
    project.add_file("presentation1.pptx")
    assert project.file_count == 1
```

### Challenge 2: Project Description
Add optional description support.

```python
# Start with a test (RED)
def test_project_with_description():
    """Projects can have optional descriptions."""
    project = Project(
        name="Described Project",
        description="This project contains our Q4 slides"
    )
    assert project.description == "This project contains our Q4 slides"

def test_project_description_defaults_to_none():
    """Projects without description should have None."""
    project = Project(name="Simple Project")
    assert project.description is None
```

Follow the TDD cycle for each challenge:
1. **RED**: Write failing test
2. **GREEN**: Minimal implementation
3. **REFACTOR**: Clean up the code
4. **COMMIT**: Professional Git message

---

## 🚀 What's Next?

In the next module, **Database Layer TDD with Repository Pattern**, you'll:
- Connect your Project model to a SQLite database
- Learn the Repository pattern for data access
- Write integration tests for database operations
- Set up database migrations and schema management

### Preparation for Next Module
- [ ] Complete all Project model tests successfully
- [ ] Practice the TDD cycle with the challenges above
- [ ] Commit and push your work to GitHub
- [ ] Verify CI/CD pipeline runs green
- [ ] Feel comfortable with Red-Green-Refactor rhythm

---

## 💡 Pro Tips for TDD Mastery

### 1. Start with the Assert
When writing a test, start with the assertion and work backwards:
```python
# Start here
assert project.name == "Expected Name"

# Then figure out how to get a project
project = Project(name="Expected Name")

# Finally, add any setup needed
# (none needed in this simple case)
```

### 2. Use Descriptive Test Names
Good test names are like mini-specifications:
```python
# Good - tells a story
def test_project_name_cannot_be_empty_string()

# Bad - vague
def test_project_validation()
```

### 3. Test One Thing at a Time
Each test should verify one specific behavior:
```python
# Good - focused
def test_project_generates_unique_id()

# Bad - testing multiple things
def test_project_creation_and_validation_and_id_generation()
```

### 4. Keep Tests Simple
Tests should be easier to understand than the code they test:
```python
# Good - clear and simple
def test_project_name_is_stripped_of_whitespace():
    project = Project(name="  My Project  ")
    assert project.name == "My Project"

# Bad - complex test logic
def test_project_name_processing():
    names = ["  Project1  ", "\tProject2\n", " \r\n Project3 \t "]
    for original in names:
        project = Project(name=original)
        assert project.name == original.strip()
```

### 5. Use pytest Features
Leverage pytest's powerful features:
```python
# Parametrized tests for multiple inputs
@pytest.mark.parametrize("name,expected", [
    ("  Spaced  ", "Spaced"),
    ("\tTabbed\t", "Tabbed"),
    ("\nNewlined\n", "Newlined"),
])
def test_name_normalization(name, expected):
    project = Project(name=name)
    assert project.name == expected

# Fixtures for common test data
@pytest.fixture
def sample_project():
    return Project(name="Test Project", path="/test/path")
```

---

## ✅ Module 5 Completion Checklist

Before proceeding to the next module, ensure you can:
- [ ] Execute complete Red-Green-Refactor cycles
- [ ] Write failing tests that drive implementation
- [ ] Implement minimal code to make tests pass
- [ ] Refactor safely with test coverage
- [ ] Use pytest features effectively (parametrize, fixtures)
- [ ] Commit TDD work with professional Git messages
- [ ] See your tests run in CI/CD pipeline
- [ ] Feel confident with the TDD rhythm

**Module Status:** ⬜ Complete | **Next Module:** [06-database-repository-pattern.md](06-database-repository-pattern.md)

---

## 📚 Additional Resources

- **Practice**: Complete the TDD challenges above
- **Reading**: "Test Driven Development: By Example" by Kent Beck
- **Video**: Uncle Bob Martin's TDD episodes
- **Tool**: Use VS Code's pytest integration for easier test running
- **Community**: Share your TDD journey on developer forums