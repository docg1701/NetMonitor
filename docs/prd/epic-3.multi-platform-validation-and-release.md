# Epic 3: Multi-Platform Validation & Release v1.0

## Goal
Configure CI/CD and build processes to successfully generate and publish v1.0 installers for Windows, Linux, macOS, and Android on GitHub.

## Stories
- **Story 3.1**: GitHub Actions CI/CD Configuration (Desktop)
    - **Goal**: Configure a GitHub Action workflow that builds Tauri apps for Windows, Linux, and macOS.
- **Story 3.2**: Mobile Release Build Pipeline (Android & iOS)
    - **Goal**: Generate signed Android APK/AAB and iOS IPA files.
- **Story 3.3**: v1.0 Final Verification
    - **Goal**: Install and run the generated artifacts on each platform to validate functionality.

## Key Requirements
- **Automation**: Use GitHub Actions for desktop builds.
- **Cross-Platform**: Support Linux (`ubuntu-latest`), Windows (`windows-latest`), and macOS (`macos-latest`).
- **Mobile**: Android and iOS builds (integrated if possible, or documented manual process).
- **Artifacts**: AppImage/Deb (Linux), MSI/Exe (Windows), DMG/App (macOS), APK/AAB (Android), IPA (iOS).
- **Documentation**: `RELEASE_PROCESS.md` to guide future releases.

## Acceptance Criteria
1. A `.github/workflows/release.yml` exists and triggers on `v*` tags.
2. Builds pass on all desktop platforms.
3. Artifacts are successfully attached to GitHub Releases.
4. Mobile artifacts are generated and signed.
5. All artifacts are verified to work on target devices.

## Reference Material
- `docs/prd/epic-and-story-structure.md`: Original definition of Epic 3 (Stories 7, 8, 9).
