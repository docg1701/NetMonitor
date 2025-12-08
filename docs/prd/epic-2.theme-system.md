# Epic 2: Theme System Implementation

## Goal
Implement a robust Light/Dark theme system with user control, allowing users to switch between modes and ensuring the application is visually consistent and accessible in both.

## Stories
- **Story 2.1**: CSS Variable Refactoring
    - **Goal**: Refactor existing hardcoded colors into CSS variables to support dynamic theming.
    - **Status**: Done (docs/stories/2.1.css-variable-refactoring.story.md)
- **Story 2.2**: Theme Toggle & Persistence
    - **Goal**: Implement the UI control to switch themes and persist the user's choice.
    - **Status**: Done (docs/stories/2.2.theme-toggle-and-persistence.story.md)

## Key Requirements
- **Theme Support**:
    - Dark Mode (Default/Existing)
    - Light Mode (New)
- **Technical Implementation**:
    - Use Ionic CSS Variables for structural colors.
    - Remove hardcoded colors from `global.scss` and components.
    - Implement class-based theme switching (`.light-theme` / `.dark-theme` or standard Ionic palette switching).
- **Persistence**: Save user preference to local storage (or Ionic Storage).
- **Charts**: Ensure Chart.js visualizations adapt to the active theme (grid lines, labels, data colors).

## Acceptance Criteria
1. Application supports both Light and Dark themes.
2. User can toggle between themes via a UI control.
3. Theme preference persists across sessions.
4. Visual regression testing passes for Dark Mode (must match original).
5. Light Mode meets WCAG AA contrast standards.

## Reference Material
- `docs/prd/epic-and-story-structure.md`: Original definition of Epic 2 (referred to as Story 5 and 6).
- `docs/prd/user-interface-enhancement-goals.md`: UI requirements for the new theme.
