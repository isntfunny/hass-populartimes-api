# AGENTS.md

This repository uses an automated GitHub Release workflow for HACS-friendly releases.

## Release policy

- The integration version lives in `custom_components/populartimes/manifest.json`.
- Git tags must use a leading `v`, for example `v1.1.0`.
- `CHANGELOG.md` is the source of truth for release notes.
- The GitHub Action creates the GitHub Release automatically from the matching changelog section.
- HACS should consume the published GitHub Release and tag version, not a manually edited release in the UI.

## Required changelog format

Each release must have its own top-level section in `CHANGELOG.md` using exactly this format:

```md
## [1.1.0] - 2026-04-05

### Added
- ...

### Changed
- ...

### Fixed
- ...
```

Important:

- The version in the heading must match the manifest version without the `v` prefix.
- The Git tag must match the same version with a `v` prefix.
- Keep release notes user-facing and concise.

## Exact release workflow

When preparing a release, follow these steps in order:

1. Update `custom_components/populartimes/manifest.json`
   - Example: `1.1.0` -> `1.2.0`

2. Add a new section at the top of `CHANGELOG.md`
   - Example heading: `## [1.2.0] - 2026-04-05`

3. Commit the release changes

4. Create a matching git tag
   - Example: `v1.2.0`

5. Push the commit and the tag

6. The GitHub Action `.github/workflows/release.yml` will:
   - read the pushed tag
   - verify that `manifest.json` matches the tag version
   - extract the matching section from `CHANGELOG.md`
   - create the GitHub Release automatically using that text

## Example commands

```sh
git add custom_components/populartimes/manifest.json CHANGELOG.md
git commit -m "release 1.2.0"
git tag v1.2.0
git push origin master
git push origin v1.2.0
```

## Manual rerun option

The workflow also supports `workflow_dispatch`.

If needed, trigger it manually and provide a tag like:

- `v1.2.0`

This is useful if the tag already exists but the release needs to be recreated.

## Notes for future agents

- Do not create release notes manually in the GitHub UI unless explicitly requested.
- Prefer updating `CHANGELOG.md` and letting the workflow publish the release.
- Keep changelog headings stable so `scripts/extract_release_notes.py` can find them.
- If the workflow fails, first check:
  - tag/version mismatch
  - malformed changelog heading
  - missing `CHANGELOG.md` section for the tagged version
