# Publishing cambium-mcp to PyPI

The installable package in this repository is `mcp_server/`, published to PyPI as
**cambium-mcp**. Releases are automated with GitHub Actions and PyPI Trusted
Publishing (OIDC): no API token is ever stored in the repository. A short-lived
credential is minted from the workflow's OIDC identity at publish time, and PyPI
accepts it only because the maintainer has registered this repository and workflow
as a trusted publisher.

The workflow lives at `.github/workflows/publish.yml`. It builds an sdist and a
wheel from `mcp_server/`, runs `twine check`, and publishes on a GitHub Release.

## What is a human action (do this once)

These steps require a person with a PyPI account and cannot be automated:

1. **Create or sign in to a PyPI account.** Use the maintainer account (pkjaslam).
   Enable two-factor authentication if it is not already on.

2. **Register the trusted publisher on PyPI.** This links the PyPI project to this
   exact GitHub workflow so no token is needed.

   For a brand-new project (recommended, before the first upload), use a
   *pending* publisher so the project name is claimed on first publish:

   - Go to <https://pypi.org/manage/account/publishing/>.
   - Under "Add a new pending publisher", enter:
     - **PyPI Project Name:** `cambium-mcp`
     - **Owner:** `pkjaslam`
     - **Repository name:** `Cambium_AI`
     - **Workflow name:** `publish.yml`
     - **Environment name:** `pypi`
   - Save.

   If the `cambium-mcp` project already exists on PyPI, add the same publisher
   instead from the project page: **Manage project -> Publishing -> Add a new
   publisher**, with the identical Owner / Repository / Workflow / Environment
   values above.

3. **(Optional but recommended) Protect the `pypi` GitHub environment.** In the
   GitHub repo: **Settings -> Environments -> pypi -> Required reviewers**, and add
   yourself. Publishing then waits for a human approval click even after a Release
   is created. The workflow already targets this `pypi` environment.

That is the entire one-time human setup. After it is done, every release publishes
automatically.

## Releasing a new version (the routine flow)

1. **Bump the version.** Edit `version` in `mcp_server/pyproject.toml` to the new
   release (for example `1.42.0`). PyPI rejects re-uploading a version that already
   exists, so this must change for each release.

2. **Commit and push** the version bump to `main`.

3. **Tag and create a GitHub Release.**

   ```bash
   git tag mcp-v1.42.0
   git push origin mcp-v1.42.0
   ```

   Then on GitHub: **Releases -> Draft a new release**, pick the tag, add release
   notes, and click **Publish release**. Publishing the Release is the trigger.

4. **The workflow runs automatically.** It builds `mcp_server`, runs `twine check`,
   and (after the optional environment approval) uploads to PyPI. Watch it under
   the repo's **Actions** tab. When it is green, the new version is live at
   <https://pypi.org/project/cambium-mcp/>.

## Dry run without releasing

Trigger the workflow manually from **Actions -> Publish cambium-mcp to PyPI ->
Run workflow** (`workflow_dispatch`). It builds and `twine check`s the package. If
the trusted publisher is configured, it will also attempt the upload, so only run
a manual dispatch when you actually intend to publish, or comment out the publish
job first.

## Verify locally before releasing

```bash
cd mcp_server
python -m pip install --upgrade build twine
python -m build                 # writes dist/*.whl and dist/*.tar.gz
python -m twine check dist/*     # expect: PASSED for both files
```

A local `twine check` PASS is the same check CI runs before uploading.

## Notes

- The package name on PyPI is `cambium-mcp`; the import name is `cambium_mcp`.
- Trusted Publishing means there is no `PYPI_API_TOKEN` secret to rotate or leak.
- If a publish fails with an identity error, re-check that the Owner, Repository,
  Workflow filename (`publish.yml`), and Environment (`pypi`) on PyPI match this
  repository exactly.
