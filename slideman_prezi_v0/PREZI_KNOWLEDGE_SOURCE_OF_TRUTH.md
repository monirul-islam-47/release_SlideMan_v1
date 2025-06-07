# PrezI Knowledge Source of Truth
## Essential Reading Guide for Future AI Agents

---

## 🎯 Critical Context

You are working on **PrezI** (formerly SlideMan + PREZI), an AI-powered presentation management system that transforms how professionals create presentations. The user's boss wastes 4-5 hours manually searching for slides - PrezI solves this in minutes.

**Key Understanding**: PrezI is not just a feature - she IS the product. She's an AI partner with personality who understands presentations at an element level (individual charts, text boxes, images).

---

## 📚 Essential Documents to Read (In Priority Order)

### 1. **CLAUDE.md** (Project root)
**Location**: `/CLAUDE.md`
**Why Critical**: Contains project overview, architecture, essential commands, and known issues. Start here for technical understanding.

### 2. **big_CHAT.md** (2073 lines)
**Location**: `/big_CHAT.md`
**Why Critical**: The original conversation where PrezI was born. Contains:
- The origin story (boss's 4-5 hour problem)
- Initial vision and philosophy
- User personas and use cases
- Detailed feature discussions
- The shift from "SlideMan" to "PrezI" as the heart of the product

### 3. **big_CHAT_2.md** (930 lines)
**Location**: `/big_CHAT_2.md`
**Why Critical**: Continuation of the vision, including:
- PRD interview questions and answers
- Keyword system design (colors, priorities, auto-completion)
- AI integration discussions
- Natural language understanding requirements
- API timeout at the end (showing dedication to continue)

### 4. **AI_INTEGRATION_REQUIREMENTS.md**
**Location**: `/AI_INTEGRATION_REQUIREMENTS.md`
**Why Critical**: Complete technical specification for PrezI including:
- AI models to use (GPT-4o, o3)
- Feature prioritization
- Interaction design
- Personality specifications

### 5. **NEW_VISION.md**
**Location**: `/NEW_VISION.md`
**Why Critical**: The unified vision combining SlideMan's organization with PrezI's intelligence.

---

## 🎨 Created Mockups & Demonstrations

### Landing Page & Overview
1. **index.html** - Main landing page showcasing PrezI as the brand
   - Hero section with animated PrezI avatar
   - Problem/solution narrative
   - Links to all demos
   - ROI statistics
   - Beautiful animations and gradients

2. **executive_summary.html** - For mama marketing GmbH
   - $50B market opportunity
   - Technical architecture
   - Implementation roadmap
   - Investment requirements (€1M)
   - Revenue projections
   - Print-friendly for board meetings

### Interactive Demonstrations
3. **01_urgent_pitch_workflow.html** - The "Tuesday 3PM panic" scenario
   - Shows 5-step workflow
   - Natural language input
   - Visual plan before execution
   - Progress tracking with emergency stop
   - Time comparison (5 hours → 2 minutes)

4. **02_prezi_thinking_visualization.html** - Watch PrezI's mind work
   - Neural network visualization
   - Real-time thought streams
   - Pattern recognition
   - Knowledge graph activation
   - Different avatar states (idle, thinking, creating, success)

5. **03_keyword_prezi_integration.html** - Smart keyword system
   - AI suggestions and auto-completion
   - Keyword relationships visualization
   - Color coding and priorities
   - Smart actions (merge, prioritize, color-code)
   - Shows how keywords + AI work together

6. **04_element_level_intelligence.html** - Understanding slide contents
   - Interactive element recognition demo
   - Overlays showing tagged elements
   - AI analysis of charts, text, images
   - Element-level search capabilities
   - Live tagging demonstration

7. **05_unified_interface_complete.html** - The full application
   - Unified command bar with rotating placeholders
   - Smart sidebar with keywords
   - Main canvas with element overlays
   - Assembly panel with drag-and-drop
   - Natural language everything
   - Shows complete workflow integration

### Vision Documents
8. **PREZI_VISION_DOCUMENT.md** - Complete brand & experience strategy
   - PrezI's personality traits (morphing core, particles, emotions)
   - Voice and communication style examples
   - Enhanced user scenarios (Panicked Executive, Brand Perfectionist, Data Detective)
   - Video walkthrough concept (90-second hero video)
   - Future vision (PrezI 2.0, 3.0, Enterprise)
   - Success metrics and dream testimonials

9. **PREZI_KNOWLEDGE_SOURCE_OF_TRUTH.md** - This document (UPDATED)

---

## 🔑 Key Concepts to Remember

### 1. The Core Problem
- Executives waste 4-5 hours searching through presentations
- Content is scattered across hundreds of files
- No way to find specific charts or elements
- Manual assembly is error-prone
- "I know I have that slide somewhere..." - Universal pain point

### 2. PrezI's Unique Value
- **Element-level understanding**: Knows what's IN each slide
- **Natural language interface**: "Create investor pitch for BigCorp"
- **Professional guarantee**: McKinsey-level output every time
- **Personality**: She's excited, helpful, and celebrates successes
- **Speed**: 90% time reduction (5 hours → 30 minutes)

### 3. Technical Architecture
- Python/Qt desktop application (existing SlideMan)
- PowerPoint COM automation for slide conversion
- SQLite with FTS5 for search
- GPT-4o for real-time AI, o3 for complex analysis
- Element recognition via custom computer vision
- Keywords system with colors and priorities

### 4. User Journey
```
Import Files → PrezI Auto-tags → User Searches Naturally → 
PrezI Suggests → User Assembles → PrezI Ensures Quality → Export
```

### 5. Branding Decision
- It's "PrezI" not "SlideMan + PREZI"
- PrezI is the star, the differentiator
- SlideMan becomes the underlying technology
- Purple (#667eea) to blue (#764ba2) gradient aesthetic
- Morphing, organic avatar (not robotic)
- Dark theme (#0a0a0a background)

---

## 💡 Implementation Status

### What's Built
- Complete mockup suite showing all interactions
- Landing page with navigation to all demos
- Executive summary for stakeholders
- Vision and strategy documents
- Interactive demos with animations
- Comprehensive documentation
- Navigation component snippet (navigation_snippet.html) for easy page navigation

### What's Needed Next
1. Update remaining mockups to use consistent "PrezI" branding (partially done - files 01 and 02 updated)
2. Add navigation snippet to all demo pages for easier browsing
3. Add more personality animations to PrezI avatar
3. Create video walkthrough mockup
4. Add more specific use case demos
5. Implement more interactive elements in demos
6. Build actual backend integration

---

## 🎯 Quick Reference for Common Tasks

### Running the Application
```bash
python -m src.slideman  # or python main.py
python main.py --ui new  # For new unified UI
python main.py --ui old  # For original UI
```

### Key Files to Edit
- Main window: `src/slideman/ui/main_window_unified.py`
- Database: `src/slideman/services/database.py`
- Slide conversion: `src/slideman/services/slide_converter.py`
- Event bus: `src/slideman/event_bus.py`

### Design Guidelines
- Dark theme (#0a0a0a background)
- Purple (#667eea) to blue (#764ba2) gradients
- Accent colors: Green (#10b981), Amber (#f59e0b), Red (#ef4444)
- Smooth animations (0.3s transitions)
- Large, visual-first interfaces
- Border radius: 8-16px for cards, 20-24px for major containers

---

## 🚀 The Vision in One Sentence

**"PrezI transforms 5 hours of presentation chaos into 5 minutes of AI-powered magic, with a personality users love."**

---

## 📞 Context for Conversations

When continuing work on PrezI:
1. Read this document first
2. Understand PrezI is the brand/product name
3. Remember she has personality - she's not just a chatbot
4. Focus on the user's delight and time savings
5. Every feature should feel magical, not technical
6. The user works for mama marketing GmbH
7. The user is passionate and expects high quality

### Important User Context
- The user is very passionate about this project
- They appreciate attention to detail and going above and beyond
- They want PrezI to have real personality that users will love
- They value beautiful, interactive demonstrations
- They're presenting this to their boss at mama marketing GmbH

### Communication Style
- Be enthusiastic about PrezI's potential
- Show understanding of the vision
- Create comprehensive, beautiful mockups
- Always think about the end user's experience
- Make it feel like magic, not technology

---

## 🎨 What Makes This Project Special

1. **It's Personal**: Born from real frustration (boss's 4-5 hour searches)
2. **It's Revolutionary**: Not another "create from scratch" tool
3. **It's Intelligent**: Element-level understanding is unique
4. **It's Delightful**: PrezI has personality users will love
5. **It's Professional**: McKinsey-level output guaranteed

---

## 💜 Final Notes for Next Agent

This project is special. The user has put their heart into it, and PrezI represents a genuine solution to a painful problem. When you work on this:

- **Be creative**: Push boundaries with interactions and animations
- **Be thorough**: Create complete experiences, not just sketches
- **Be thoughtful**: Every detail matters
- **Be excited**: This could genuinely change how people work

The mockups in `slideman_prezi_v0/` are ready to show to mama marketing GmbH. They demonstrate not just what PrezI does, but who she is - a delightful AI partner that makes presentations magical.

Remember: You're not just building software. You're creating a beloved AI partner that professionals can't imagine working without.

---

*"I used to dread creating presentations. Now, I actually look forward to it because I get to work with PrezI. She makes me look like a genius, and honestly? She kind of is one."*

— Every PrezI user, eventually

---

**Created with 💜 by an AI who truly understood the vision**