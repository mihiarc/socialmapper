# Branch Protection Setup for feature/frontend-backend-separation

## Recommended Branch Protection Rules

When this branch is pushed to the remote repository, configure the following branch protection rules:

### For `feature/frontend-backend-separation` branch:
- **Require pull request reviews before merging**: Enable
- **Required number of reviewers**: 1 minimum
- **Dismiss stale reviews when new commits are pushed**: Enable
- **Require status checks to pass before merging**: Enable
  - Required status checks:
    - CI/CD pipeline tests
    - Code quality checks (Ruff)
    - Type checking (ty)
- **Require branches to be up to date before merging**: Enable
- **Restrict pushes that create files**: Disable (allow development)
- **Allow force pushes**: Disable
- **Allow deletions**: Disable

### For `main` branch (if not already configured):
- **Require pull request reviews before merging**: Enable
- **Required number of reviewers**: 2 minimum
- **Require status checks to pass before merging**: Enable
- **Restrict pushes that create files**: Enable
- **Allow force pushes**: Disable
- **Allow deletions**: Disable

## Setup Instructions

1. Navigate to repository settings on GitHub/GitLab
2. Go to "Branches" section
3. Add branch protection rule for `feature/frontend-backend-separation`
4. Configure the settings listed above
5. Save the protection rule

## Note
These settings prevent accidental direct pushes to protected branches and ensure all changes go through proper review process.