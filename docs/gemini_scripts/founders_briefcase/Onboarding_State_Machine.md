# PrezI: Onboarding Integration & State Machine Definition

*   **Version:** 1.1
*   **Date:** June 15, 2025
*   **Author:** PrezI Vision Synthesis AI
*   **Status:** Final & Ready

## 1. Onboarding Integration Overview

This document provides a comprehensive reference for the PrezI onboarding feature integration across all project documentation. It defines the onboarding state machine in detail, confirms consistency across documents, and serves as the single source of truth for implementation.

## 2. Document Updates Summary

| Document | Version | Status | Key Updates |
|----------|---------|--------|-------------|
| Operations & Experience Handbook | 1.1 | Amended & Finalized | Added detailed onboarding state machine, interactive flows with branching paths, analytics tracking |
| Development & Testing Plan | 1.2 | Amended & Finalized | Added Sprint 6 focused on first-time user experience, onboarding state machine and assistant implementation |
| API Specification | 1.2 | Amended & Finalized | Enhanced onboarding API with state machine endpoints, branching paths, API key management |
| Database Schema | 1.2 | Amended & Finalized | Updated with comprehensive onboarding tables supporting state machine, transitions, analytics |
| Project Layout | 1.1 | Amended & Finalized | Added onboarding components to backend and frontend folders |
| Feature & Functionality Checklist | 1.1 | Amended & Finalized | Added onboarding features and platform support section |

## 3. Onboarding State Machine Definition

This section serves as the definitive reference for the PrezI onboarding state machine. It explicitly defines all states, transitions, branching paths, and validation rules to ensure consistency across implementation in code, database, and user interface.

### 3.1. Onboarding States

| State ID | Display Name | Description | UI Component | Available Actions |
|----------|--------------|-------------|-------------|-------------------|
| `WELCOME` | Welcome to PrezI | Initial welcome screen introducing PrezI | `WelcomeDialog` | Next, Skip |
| `API_SETUP` | Set Up Your AI | API key configuration and validation | `ApiKeySetupDialog` | Validate, Skip, Back |
| `BRANCH_CHOICE` | How Do You Want to Start? | User decides their preferred path | `BranchChoiceDialog` | Feature Tour, Import First |
| `FEATURE_TOUR` | Feature Tour | Overview of key app features | `FeatureTourDialog` | Next, Skip to Import |
| `IMPORT_FIRST` | Import Your First Slides | Guide to importing slides | `ImportDialog` | Import, Skip |
| `COMMAND_BAR` | Meet the Command Bar | Introduction to command functionality | `CommandBarTutorial` | Try Command, Next |
| `ASSEMBLY_PANEL` | Assemble Your Story | Introduction to assembly workflow | `AssemblyPanelTutorial` | Try Assembly, Next |
| `AI_ASSISTANT` | Meet Your AI Assistant | Introduction to AI capabilities | `AssistantDialog` | Try Assistant, Next |
| `GRADUATION` | You're Ready! | Completion of onboarding | `GraduationDialog` | Finish |
| `COMPLETED` | (Non-UI State) | Terminal state indicating completion | None | None |

### 3.2. Transition Rules

#### 3.2.1. Valid State Transitions

```
WELCOME → API_SETUP → BRANCH_CHOICE → [FEATURE_TOUR or IMPORT_FIRST]

FEATURE_TOUR → COMMAND_BAR → ASSEMBLY_PANEL → AI_ASSISTANT → GRADUATION → COMPLETED

IMPORT_FIRST → ASSEMBLY_PANEL → COMMAND_BAR → AI_ASSISTANT → GRADUATION → COMPLETED
```

#### 3.2.2. Special Transitions

- **Skip All**: From any state, user can skip directly to `COMPLETED`
- **Back Navigation**: User can move back one state at any time except from `COMPLETED`
- **Branch Path Switch**: User can switch from `FEATURE_TOUR` to `IMPORT_FIRST` at any time

### 3.3. Branching Paths

The onboarding flow contains two main paths after API setup:

1. **Feature-First Path (`FEATURE_TOUR`)**: 
   - Focuses on showcasing PrezI's features before hands-on usage
   - Ideal for users wanting to explore capabilities first
   - Sequence: FEATURE_TOUR → COMMAND_BAR → ASSEMBLY_PANEL → AI_ASSISTANT

2. **Import-First Path (`IMPORT_FIRST`)**:
   - Focuses on getting users to import slides immediately
   - Hands-on approach for practical users
   - Sequence: IMPORT_FIRST → ASSEMBLY_PANEL → COMMAND_BAR → AI_ASSISTANT

### 3.4. State Persistence

All state information will be stored in the `onboarding_state` table with:
- Current state ID
- Selected branch path
- Progression index
- Completion status

### 3.5. Implementation References

- **Database**: Tables defined in `DB_Schema.md` section 8
- **API Endpoints**: Endpoints defined in `API_Spec.md` section 4.5
- **Backend Logic**: Implementation in `core/onboarding_manager.py`
- **Frontend Components**: Implementation in `frontend/components/onboarding/`

## 4. API Key Security Implementation

Secure API key management is integrated across:
- Database table for credential status tracking
- API endpoints for validation and secure storage
- OS-native credential stores for key security
- Client-side validation UI components

## 5. Next Implementation Steps

According to the updated Development & Testing Plan, Sprint 6 should proceed with:

1. Implementing the onboarding state machine backend logic (`core/onboarding_manager.py`)
2. Creating the API endpoints in `api/v1/onboarding.py`
3. Developing welcome screens and interactive UI flows
4. Implementing the API key setup & validation UI
5. Creating the onboarding assistant with personalized guidance
6. Adding analytics tracking for onboarding completion rates

## 6. Windows-First Implementation Notes

### 6.1. Windows Implementation

- API keys stored in Windows Credential Manager
- PowerPoint COM automation used for slide import tutorials
- Windows-specific dialog styling and behavior

### 6.2. Future Cross-Platform Support

While initial implementation is Windows-first, the state machine design accommodates future cross-platform support via:
- Abstract credential storage interface
- Platform-agnostic state machine logic
- UI component isolation from platform-specific code


---

This document serves as the definitive reference for the PrezI onboarding integration and state machine. It should be consulted during implementation to ensure consistency across all components. All documentation now consistently reflects these specifications with the June 15, 2025 update.
