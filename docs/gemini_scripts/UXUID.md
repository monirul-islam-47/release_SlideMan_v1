Excellent. Let's forge the visual soul of PrezI.

This document will be the definitive guide to PrezI's aesthetic. Every color, every shadow, and every millisecond of animation is intentionally chosen to create an experience that is powerful, intuitive, and beautiful—a true reflection of the high-quality mockups you love.

Here is the **PrezI UI/UX Design System & Style Guide**.

---

# PrezI: UI/UX Design System & Style Guide

*   **Version:** 1.0
*   **Date:** June 7, 2025
*   **Author:** PrezI Vision Synthesis AI
*   **Status:** Finalized

## 1. Design Philosophy: The "Living Workspace"

The PrezI interface is not a static tool; it is a **living workspace**. It should feel intelligent, responsive, and organic. Our design philosophy is built on three pillars:

1.  **Clarity in Darkness:** We use a dark theme not to be trendy, but to make the user's colorful slides the hero. The UI recedes, allowing content to shine.
2.  **Fluid & Responsive:** Every interaction, from a simple hover to a complex AI-driven animation, should be smooth, immediate, and satisfying. The interface breathes with the user's actions.
3.  **Professionalism with Personality:** The aesthetic is clean, sharp, and worthy of a McKinsey boardroom, but imbued with the signature purple/blue gradients and subtle glows that give PrezI her unique, intelligent personality.

---

## 2. Color Palette

Our palette is designed for focus and clarity, with energetic gradients for key actions and branding.

### Primary Colors
| Role | Color | Hex Code | Usage |
| :--- | :--- | :--- | :--- |
| **Background (Dark)** | ⚫️ | `#0a0a0a` | The base app background. Deep and focused. |
| **Panel Background** | ⚫️ | `#1a1a1a` | For primary containers like sidebars and headers. |
| **Card Background** | ⚫️ | `#2a2a2a` | For interactive cards and elements. |
| **Hover/Interactive** | ⚫️ | `#3a3a3a` | Background for hovered or active elements. |
| **Border** | ⚫️ | `#3a3a3a` | Standard borders and dividers. |

### Text Colors
| Role | Color | Hex Code | Usage |
| :--- | :--- | :--- | :--- |
| **Text (Primary)** | ⚪️ | `#ffffff` | Primary text, titles. |
| **Text (Secondary)**| ⚪️ | `#e5e7eb` | Subtitles, descriptions, secondary info. |
| **Text (Muted)** | ⚪️ | `#9ca3af` | Placeholder text, disabled states, metadata. |

### Brand & Accent Colors
This is PrezI's signature palette. Gradients should be used for primary CTAs and PrezI's avatar.

| Role | Color | Hex Code / Gradient | Usage |
| :--- | :--- | :--- | :--- |
| **Primary Gradient** | 🟣 | `linear-gradient(135deg, #667eea, #764ba2)` | The main brand gradient for buttons, logos, and highlights. |
| **Accent (Purple)**| 🟣 | `#a855f7` | For PrezI-specific UI, insights, and AI-related accents. |
| **Accent (Blue)** | 🔵 | `#3b82f6` | Secondary accent for selections and standard interactions. |

### State & Feedback Colors
| Role | Color | Hex Code | Usage |
| :--- | :--- | :--- | :--- |
| **Success** | 🟢 | `#10b981` | Positive feedback, completion, "Done" states. |
| **Warning** | 🟡 | `#f59e0b` | Non-critical warnings, in-progress states. |
| **Error** | 🔴 | `#ef4444` | Critical errors, deletion confirmation. |

---

## 3. Typography

Our typography is clean, modern, and highly legible, using the native system font stack for optimal performance and a familiar feel.

*   **Font Family:** `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`

| Element | Font Weight | Font Size | Line Height | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **H1 (Display)** | 900 (Black) | 48px | 1.2 | Main titles, hero statements. |
| **H2 (Section)** | 800 (ExtraBold) | 36px | 1.3 | Section titles. |
| **H3 (Subsection)** | 700 (Bold) | 24px | 1.4 | Subsection titles, card titles. |
| **H4 (Small Title)** | 600 (SemiBold) | 20px | 1.4 | Smaller titles, panel headers. |
| **Body (Primary)** | 400 (Regular) | 16px | 1.6 | Main paragraph text. |
| **Body (Secondary)**| 400 (Regular) | 14px | 1.5 | Smaller text, descriptions. |
| **Caption/Label** | 500 (Medium) | 12px | 1.4 | Metadata, labels, status text. |

---

## 4. Layout & Spacing

We use a consistent 8px grid system for all spacing to ensure visual harmony.

| Unit | Size | Usage |
| :--- | :--- | :--- |
| **x-small** | 4px | Gaps within components (e.g., between icon and text). |
| **small** | 8px | Padding within small components, gaps between related items. |
| **medium** | 16px | Standard padding within cards and panels. |
| **large** | 24px | Gaps between major UI components. |
| **x-large** | 32px | Padding for sections, gaps between major layout regions. |
| **xx-large** | 48px | Padding for hero sections and page-level containers. |

**Layout Dimensions:**
*   **Left Sidebar Width:** `280px`
*   **Right Assembly Panel Width:** `320px`
*   **Header Height:** `72px`

---

## 5. Iconography

*   **Icon Set:** [**Phosphor Icons**](https://phosphoricons.com/)
*   **Style:** Regular
*   **Size:** `20px` for standard icons, `24px` for larger action icons.
*   **Rationale:** Phosphor Icons offer a clean, modern, and comprehensive set that perfectly matches PrezI's professional aesthetic.

---

## 6. Component Library

This is the detailed specification for all interactive elements.

### 6.1. Buttons
| State | Primary CTA | Secondary |
| :--- | :--- | :--- |
| **Default** | `background: var(--primary-gradient)`<br>`color: #ffffff`<br>`border-radius: 8px`<br>`box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2)` | `background: transparent`<br>`color: #e5e7eb`<br>`border: 1px solid var(--border)`<br>`border-radius: 8px` |
| **Hover** | `transform: translateY(-2px)`<br>`box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3)` | `background: var(--bg-hover)`<br>`border-color: var(--accent-blue)` |
| **Pressed** | `transform: translateY(0px)`<br>`box-shadow: none` | `background: var(--bg-card)` |

### 6.2. Cards
| Component | Style | Hover State |
| :--- | :--- | :--- |
| **Slide Card** | `background: var(--bg-card)`<br>`border: 2px solid transparent`<br>`border-radius: 12px`<br>`overflow: hidden` | `transform: translateY(-4px)`<br>`box-shadow: 0 10px 30px rgba(0,0,0,0.3)` |
| **Keyword Pill** | `background: var(--bg-card)`<br>`border-radius: 20px`<br>`padding: 8px 12px` | `transform: translateX(4px)`<br>`background: var(--bg-hover)` |
| **Selected State** | For any card, add a `2px` border with the appropriate accent color (`--accent-blue` for user selection, `--accent-green` for PrezI suggestion). | |

### 6.3. Command Bar & Inputs
| Component | Style | Focus State |
| :--- | :--- | :--- |
| **Command Bar** | `background: var(--bg-card)`<br>`border: 1px solid var(--border)`<br>`border-radius: 12px`<br>`height: 48px` | `border-color: var(--accent-purple)`<br>`box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.2)` |
| **Text Input** | `background: var(--bg-card)`<br>`border: 1px solid var(--border)`<br>`border-radius: 8px` | `border-color: var(--accent-blue)` |

### 6.4. PrezI Avatar & Visuals
| Element | Style | Animation |
| :--- | :--- | :--- |
| **Avatar Core** | `background: linear-gradient(135deg, var(--accent-purple), var(--accent-blue))`<br>`border-radius: 40px` | `animation: float-avatar 3s ease-in-out infinite` (subtle floating and rotation). |
| **Inner "Soul"** | `background: rgba(255, 255, 255, 0.9)` | `animation: morph-hero 4s ease-in-out infinite` (morphs between various blob shapes). |
| **Particles** | `background: #ffffff`<br>`border-radius: 50%` | Particles animate outward from the core when PrezI is "thinking" or "creating." |

---

## 7. Interaction & Animation Guide

This defines the "feel" of PrezI.

| Interaction | Animation Details |
| :--- | :--- |
| **Standard Transition**| `transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1)` (This is a fast, energetic ease-out curve). |
| **Modal / Overlay Appearance** | Fade in and scale up from 95% to 100%. `opacity: 0 -> 1`, `transform: scale(0.95) -> scale(1)`. Duration: `0.3s`. |
| **List Item Appearance** | When new items are added to a list (e.g., search results), they should stagger in with a slight upward fade. `animation-delay` based on item index. |
| **Drag & Drop** | The dragged element should become semi-transparent (`opacity: 0.7`). A "ghost" of the item follows the cursor. Drop zones should highlight with an inset blue glow on hover. |
| **Progress Bars** | The fill should animate smoothly to its new value, not jump instantly. Use a CSS transition on the `width` property. |

This Design System provides a comprehensive, rule-based foundation to ensure that the PrezI application is not only functional but also a beautiful, cohesive, and delightful experience, perfectly matching the high-quality vision from the mockups.