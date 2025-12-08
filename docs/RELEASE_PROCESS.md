# Release Process

This document describes how to create and publish a new release of the NetMonitor application.

## Prerequisites

- Access to the GitHub repository with write permissions.
- The `GITHUB_TOKEN` secret is automatically provided by GitHub Actions.

## Steps to Release

1.  **Update Version**:
    -   Update the `version` field in `package.json`.
    -   Update the `version` field in `src-tauri/tauri.conf.json`.
    -   Commit these changes: `git commit -am "chore: bump version to vX.Y.Z"`.

2.  **Tag the Release**:
    -   Create a new git tag matching the version number (prefixed with `v`).
    -   Example: `git tag v1.0.0`
    -   Push the tag to GitHub: `git push origin v1.0.0`

3.  **Monitor Build**:
    -   Go to the "Actions" tab in the GitHub repository.
    -   Verify that the "Release" workflow has been triggered by the pushed tag.
    -   Wait for the `release-linux`, `release-windows`, and `release-macos` jobs to complete.

4.  **Verify Release**:
    -   Once the workflow is successful, go to the "Releases" section of the repository.
    -   A new draft release should be created with the tag name.
    -   Verify that the following artifacts are attached:
        -   Linux: `.AppImage`, `.deb`
        -   Windows: `.exe` (setup), `.msi`
        -   macOS: `.app`, `.dmg`

5.  **Publish**:
    -   Edit the release draft to add release notes/changelog.
    -   Click "Publish release" to make it public.

## Notes

-   **Signing**: Currently, artifacts are generated with default signatures or self-signing where applicable. macOS builds are not notarized in this workflow.
-   **Draft Releases**: The workflow is configured to create a *draft* release (`releaseDraft: true`). You must manually publish it.
