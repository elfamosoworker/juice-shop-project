# Branch Protection Rules Configuration

This document provides step-by-step instructions for configuring GitHub branch protection rules for the `main` branch to enforce the DevSecOps pipeline.

## Overview

Branch protection rules ensure that all code merged to `main` (production) passes through the complete security pipeline with required approvals.

---

## Configuration Steps

### 1. Navigate to Branch Protection Settings

1. Go to your repository: `https://github.com/elfamosoworker/juice-shop-project`
2. Click **Settings** (top menu)
3. In the left sidebar, click **Branches** (under "Code and automation")
4. Click **Add branch protection rule** or edit existing rule for `main`

---

### 2. Branch Name Pattern

```
main
```

**Description:** Protects the production branch from direct commits and enforces pipeline checks.

---

### 3. Protection Rules Configuration

#### A. Require Pull Request Reviews

- ✅ **Require a pull request before merging**
  - ✅ **Require approvals:** `2`
    - Ensures at least 2 team members review and approve changes
  - ✅ **Dismiss stale pull request approvals when new commits are pushed**
    - Forces re-review after code changes
  - ✅ **Require review from Code Owners** (if CODEOWNERS file exists)
  - ✅ **Require approval of the most recent reviewable push**

#### B. Require Status Checks

- ✅ **Require status checks to pass before merging**
  - ✅ **Require branches to be up to date before merging**

**Required Status Checks (select all):**

```
✅ validate-branch
✅ build
✅ test
✅ sast
✅ sca
✅ dast
✅ regression-tests
✅ staging-tests
✅ load-tests
✅ quality-gate
✅ comment-pr
```

**How to add:**
- After the first PR is created, these checks will appear in the dropdown
- Search for each job name and select it
- All 11 jobs must pass before merge is allowed

#### C. Require Conversation Resolution

- ✅ **Require conversation resolution before merging**
  - All PR comments must be resolved

#### D. Require Signed Commits (Optional but Recommended)

- ⬜ **Require signed commits**
  - Enable if your team uses GPG signing

#### E. Require Linear History (Recommended)

- ✅ **Require linear history**
  - Prevents merge commits, enforces rebase or squash

#### F. Include Administrators

- ✅ **Include administrators**
  - Even repository admins must follow these rules
  - **CRITICAL:** Ensures no one bypasses security checks

#### G. Restrict Pushes

- ✅ **Restrict who can push to matching branches**
  - **Allowed actors:** Select specific users/teams or leave empty to block all direct pushes
  - Forces all changes through PR workflow

#### H. Allow Force Pushes

- ⬜ **Allow force pushes** (DISABLED)
  - Prevents rewriting history on main

#### I. Allow Deletions

- ⬜ **Allow deletions** (DISABLED)
  - Prevents accidental deletion of main branch

---

### 4. Additional Settings (Optional)

#### Require Deployments to Succeed

- ⬜ **Require deployments to succeed before merging**
  - Enable if you have deployment environments configured

#### Lock Branch

- ⬜ **Lock branch**
  - Makes branch read-only (use only for archived projects)

---

## Complete Configuration Summary

```yaml
Branch Protection Rule for 'main':

  Pull Request Requirements:
    - Require pull requests: YES
    - Required approvals: 2
    - Dismiss stale reviews: YES
    - Require code owner review: YES (if applicable)
    - Require approval of latest push: YES

  Status Check Requirements:
    - Require status checks: YES
    - Require branches up to date: YES
    - Required checks:
        • validate-branch
        • build
        • test
        • sast
        • sca
        • dast
        • regression-tests
        • staging-tests
        • load-tests
        • quality-gate
        • comment-pr

  Additional Requirements:
    - Require conversation resolution: YES
    - Require signed commits: OPTIONAL
    - Require linear history: YES
    - Include administrators: YES
    - Restrict direct pushes: YES
    - Allow force pushes: NO
    - Allow deletions: NO
```

---

## Verification Steps

### Step 1: Create Test Pull Request

```bash
# Create a test branch from release branch
git checkout release/v.19.0.251104
git checkout -b test/verify-protection
echo "# Test" >> TEST.md
git add TEST.md
git commit -m "test: verify branch protection"
git push -u origin test/verify-protection

# Create PR from GitHub UI targeting main
```

### Step 2: Verify Pipeline Runs

- ✅ All 11 workflow jobs should execute automatically
- ✅ Check Actions tab for workflow progress
- ✅ Estimated runtime: 30 minutes

### Step 3: Verify Merge Restrictions

Before all checks pass:
- ❌ **Merge button should be disabled**
- ⚠️ Message: "Required status checks must pass before merging"

After all checks pass:
- ✅ **Merge button becomes enabled**
- ✅ Message: "This branch has no conflicts with the base branch"
- ⚠️ Still requires 2 approvals

### Step 4: Test Approval Requirement

- Request reviews from 2 team members
- Verify merge button only enables after 2 approvals
- Verify that new commits reset approvals

### Step 5: Test Direct Push Block

```bash
# This should FAIL with protection rules enabled
git checkout main
echo "test" >> README.md
git commit -am "test: direct push"
git push origin main

# Expected error:
# remote: error: GH006: Protected branch update failed
```

---

## Pipeline Job Dependencies

The workflow uses job dependencies to optimize runtime:

```
validate-branch
      ↓
    build
   ↙  ↓  ↘
test sast sca dast
   ↘  ↓  ↙
regression-tests
      ↓
staging-tests
      ↓
  load-tests
      ↓
quality-gate
      ↓
  comment-pr
```

**Parallel Execution:**
- `test`, `sast`, `sca`, and `dast` run in parallel after `build`
- Reduces total pipeline time from 48+ minutes to ~30 minutes

---

## Quality Gate Thresholds

The pipeline enforces **STRICT** thresholds for production:

| Severity | Threshold | Action if Exceeded |
|----------|-----------|-------------------|
| 🔴 Critical (CVSS ≥9.0) | **0** | Pipeline FAILS |
| 🟠 High (CVSS 7.0-8.9) | **0** | Pipeline FAILS |
| 🟡 Medium (CVSS 4.0-6.9) | **0** | Pipeline FAILS |
| 🔵 Low (CVSS <4.0) | **0** | Pipeline FAILS |

**Zero-tolerance policy:** Any vulnerability at any severity blocks the merge.

To adjust thresholds, edit: [`.github/scripts/quality-gate.py`](scripts/quality-gate.py)

---

## Troubleshooting

### Issue: Required checks don't appear in dropdown

**Solution:**
1. Ensure workflow file is in `main` branch: `.github/workflows/release-to-main.yml`
2. Create a test PR to trigger the workflow
3. Wait for workflow to complete
4. Go back to branch protection settings
5. Refresh the page - checks should now appear

### Issue: Pipeline takes longer than 30 minutes

**Causes:**
- DAST scan (OWASP ZAP) may take longer on first run
- npm install on cold cache
- GitHub Actions runner queue delays

**Solutions:**
- Use `actions/cache` for dependencies (already configured)
- Consider self-hosted runners for consistent performance
- Adjust timeouts in workflow if needed

### Issue: DAST fails to start application

**Solutions:**
1. Check `app.log` artifact for startup errors
2. Verify `NODE_VERSION` in workflow matches `package.json`
3. Increase wait time in DAST job (currently 60 seconds)
4. Check port 3000 availability

### Issue: Quality gate fails on expected vulnerabilities

**Note:** Juice Shop is **intentionally vulnerable** for training purposes.

**Solutions for Production Apps:**
1. Fix all vulnerabilities before merging
2. For false positives: Add exceptions in `quality-gate.py`
3. For accepted risks: Document in security exceptions file

**Solutions for Juice Shop Training:**
- The pipeline will correctly identify vulnerabilities
- This is expected behavior for a training application
- Use this to learn remediation techniques
- For demo purposes, you may temporarily relax thresholds

### Issue: Merge blocked even after all checks pass

**Possible Causes:**
1. Missing required approvals (need 2)
2. Stale approvals (new commits pushed)
3. Unresolved conversations
4. Branch not up to date with main

**Solutions:**
- Request additional approvals
- Resolve all PR comments
- Rebase or merge main into your branch
- Re-approve after resolving issues

---

## Security Best Practices

### 1. Never Bypass Protection Rules

- ❌ Don't disable protection temporarily "just once"
- ❌ Don't use admin privileges to force merge
- ✅ Fix issues properly and re-run pipeline

### 2. Regular Security Updates

- 🔄 Run `npm audit fix` weekly
- 🔄 Update Semgrep rulesets monthly
- 🔄 Review OWASP ZAP scan configurations quarterly

### 3. Team Training

- 📚 Ensure all developers understand the pipeline
- 📚 Train team on interpreting security scan results
- 📚 Document remediation patterns for common findings

### 4. Audit Trail

- 📝 All merges have PR number and approvers
- 📝 Pipeline results archived as artifacts
- 📝 Quality gate decisions are logged

---

## Additional Security Tools (Optional)

Consider adding these tools to enhance security:

### Code Scanning (GitHub Advanced Security)

```yaml
- name: Initialize CodeQL
  uses: github/codeql-action/init@v3
  with:
    languages: javascript, typescript

- name: Perform CodeQL Analysis
  uses: github/codeql-action/analyze@v3
```

### Secrets Scanning

- Enable in repository settings
- Prevents committing API keys, tokens, passwords
- Automatically blocks pushes with detected secrets

### Dependency Review

```yaml
- name: Dependency Review
  uses: actions/dependency-review-action@v4
```

### Container Scanning (for Docker builds)

```yaml
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'your-image:tag'
```

---

## Maintenance

### Weekly Tasks
- [ ] Review failed pipeline runs
- [ ] Update vulnerable dependencies
- [ ] Check for new Semgrep rules

### Monthly Tasks
- [ ] Review and update quality gate thresholds
- [ ] Audit branch protection settings
- [ ] Update OWASP ZAP scan configuration
- [ ] Review pipeline performance metrics

### Quarterly Tasks
- [ ] Security tools version updates
- [ ] Pipeline optimization review
- [ ] Team training on new vulnerabilities
- [ ] Disaster recovery drill (branch protection disabled scenario)

---

## Support & Resources

- **GitHub Actions Documentation:** https://docs.github.com/en/actions
- **Branch Protection Rules:** https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- **OWASP Juice Shop:** https://owasp.org/www-project-juice-shop/
- **Semgrep Documentation:** https://semgrep.dev/docs/
- **OWASP ZAP Documentation:** https://www.zaproxy.org/docs/

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-04 | Initial branch protection configuration | DevSecOps Team |

---

**Last Updated:** 2025-11-04
**Version:** 1.0.0
**Maintained by:** DevSecOps Team
