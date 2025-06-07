Of course. We have laid the architectural and visual foundations. Now, we must define PrezI's "brain" in this new, collaborative cloud environment.

While the core intelligence and personality remain, the AI's capabilities must evolve to understand the context of teams, shared knowledge, and real-time collaboration. This document outlines that evolution.

Here is **Document 4 of 10**, the definitive AI guide for the PrezI SaaS platform.

---
---

### **Document 4 of 10: AI Design Document - SaaS Edition**

# PrezI Cloud: AI Design Document (AIDD)

*   **Version:** 2.0 (SaaS)
*   **Date:** June 7, 2025
*   **Status:** Finalized

## 1. Core Cognitive Model: The Collaborative Loop

PrezI's cognitive loop evolves from a personal assistant to a **team's collective intelligence**.

1.  **Observe (Team & Global Context):** PrezI now observes actions from the entire team. She is aware of which slides are being used most frequently across the organization, which presentations are most effective (e.g., lead to closed deals, if integrated), and what topics are currently trending.
2.  **Orient (Understand Collaborative Intent):** PrezI's analysis now includes team context. A command like "create a pitch" from a Sales user may yield different results than the same command from a Marketing user, as PrezI learns which slides are most relevant to each role.
3.  **Decide (Formulate a Collaborative Plan):** When building a presentation, PrezI's plan can now include collaborative steps, such as: *"Step 3: Suggest that 'Sarah' from the design team review these slides for brand consistency."*
4.  **Act (Execute & Share Insights):** PrezI's actions are now visible to the team. When she creates a new "gold standard" deck, this can be shared with the entire team as a new, valuable asset.

## 2. Personality & Communication Matrix (Evolved)

PrezI's core personality remains, but her communication style now incorporates team awareness.

| Situation | Tone | Language Style | Example |
| :--- | :--- | :--- | :--- |
| **Analyzing Team Content** | Analytical, Insightful | Data-driven, helpful | `I've noticed our most successful sales decks all include the 'Customer Testimonials' slide from the Q3 marketing presentation. I'll prioritize that.` |
| **Facilitating Collaboration**| Proactive, Encouraging| Suggestive, inclusive | `It looks like you're working on the financials. Chen is our expert on that. Should I share this assembly with him for feedback?` |
| **Enforcing Brand Standards**| Gentle, Authoritative| Informative, clear | `This slide uses a slightly outdated logo. I can update it to the official version from our team's Brand Kit with one click.` |

## 3. The Master Prompt Engineering Library - SaaS Edition

The prompts are enhanced to include team and collaborative context.

### 3.1. Prompt: `ANALYZE_SLIDE_WITH_TEAM_CONTEXT`
*   **Goal:** To analyze a slide while being aware of how similar content is used across the team.
*   **User Prompt (Amended):**
    ```json
    Analyze the following slide content. Use the provided 'Team Context' to suggest keywords that align with our organization's successful patterns. Return a single, minified JSON object.

    Slide Content: { ... }

    Team Context:
    {
      "most_used_keywords_for_topic_X": ["revenue", "growth", "YoY"],
      "most_effective_slides_for_audience_Y": ["SlideID_45", "SlideID_102"]
    }
    
    JSON Schema to follow: { ... }
    ```

### 3.2. Prompt: `GENERATE_COLLABORATIVE_PLAN`
*   **Goal:** To create a presentation plan that leverages team members' expertise.
*   **User Prompt (Amended):**
    ```json
    Based on the user's intent, create a step-by-step plan. If relevant, include a 'collaboration_suggestion' step that recommends involving a specific team member based on their role. Return a single, minified JSON object.

    Structured User Intent: { ... }
    
    Team Roster:
    [
      { "name": "Sarah", "role": "Designer" },
      { "name": "Chen", "role": "Analyst" }
    ]

    JSON Schema to follow:
    {
      "plan": [
        {
          "title": "...", "details": "...", 
          "collaboration_suggestion": "Suggest involving 'Sarah' to review the final design." 
        }
      ]
    }
    ```

### 3.3. **`**[NEW]**`** Prompt: `SUMMARIZE_ASSEMBLY_COMMENTS`
*   **Goal:** To help users quickly get up to speed on feedback.
*   **Trigger:** When a user opens an assembly with unread comments.
*   **Model:** GPT-4o.
*   **User Prompt:**
    ```json
    Analyze the following comments on a presentation assembly. Provide a brief, 3-point bulleted summary of the key feedback themes.

    Comments:
    [
      { "author": "Sarah", "comment": "The data on slide 3 is outdated. We should use the new Q4 numbers." },
      { "author": "David", "comment": "I love the flow, but the call to action on the final slide feels a bit weak." },
      { "author": "Sarah", "comment": "Also, can we make the chart on slide 3 bigger? It's hard to read." }
    ]
    ```

## 4. Team-Based Learning & Intelligence

*   **Slide Effectiveness Score:** PrezI will maintain an internal "effectiveness score" for slides. This score increases when a slide is included in presentations that are marked as "successful" or are frequently copied and reused by other team members. This score will be used to prioritize slides in AI-generated presentations.
*   **Brand Kit Adherence:** Admins can upload a "Brand Kit" (logos, color palettes, font files). PrezI will use this as the ground truth for the "Harmonize Style" feature. The AI will be prompted to compare slide elements against the Brand Kit and suggest corrections.
*   **Role-Based Suggestions:** The AI Service will be aware of user roles. When a "Sales" user asks for a pitch, PrezI will prioritize slides that have been tagged or used frequently by other high-performing sales reps.

This evolved AI design transforms PrezI from a personal assistant into the intelligent, collaborative hub for an entire organization's presentation knowledge, creating compounding value as more team members use the platform.