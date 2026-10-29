# GitHub Actions workflow templates

Use a workflow template when you create a repository or add a CI workflow.

1. Open the repository **Actions** tab.
2. Select **New workflow**.
3. Select **Fantastiq Labs Private Project CI** for a private repository.
4. Select **Fantastiq Labs Public Project CI** for a public repository.

The private template calls the shared runner selector. It uses GitHub-hosted runners while the monthly budget allows, then uses the Unraid self-hosted runner. The public template uses GitHub-hosted runners. Both templates run tests and build a Docker image when the repository has a Dockerfile. They do not publish images or use deployment secrets.

GitHub offers workflow templates for selection. It does not add them to new repositories automatically. Keep the workflow in each repository. Check that the workflow is active on `main` before you rely on pull request checks.
