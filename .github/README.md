# DevSecOps CI/CD Pipeline

This directory contains the complete GitHub Actions workflow for the OWASP Juice Shop DevSecOps pipeline.

## 📁 Structure

```
.github/
├── workflows/
│   └── release-to-main.yml          # Main CI/CD pipeline (11 steps, ~30 min)
├── scripts/
│   ├── quality-gate.py              # Security quality gate parser
│   ├── pr-comment.sh                # PR comment generator
│   └── zap-config.conf              # OWASP ZAP DAST configuration
├── BRANCH_PROTECTION_SETUP.md       # Branch protection configuration guide
└── README.md                        # This file
```

## 🚀 Pipeline Overview

### Workflow: Release to Main

**Trigger:** Pull request from `release/*` branches to `main`

**Total Duration:** ~30 minutes

**Pipeline Steps:**

1. **Validate Branch Name** (<1 min)
   - Enforces naming convention: `release/v.X.X.YYMMDD`

2. **Build Application** (~2 min)
   - `npm ci --legacy-peer-deps`
   - `npm run build`
   - Caches artifacts for subsequent jobs

3. **Test Suite** (~3 min)
   - Unit and integration tests
   - Code coverage analysis (threshold: ≥70%)

4. **SAST - Static Analysis** (~5 min)
   - Tool: Semgrep
   - Scans: TypeScript, JavaScript, YAML, JSON
   - Detects: OWASP Top 10 vulnerabilities in source code

5. **SCA - Dependency Scanning** (~4 min)
   - Tools: npm audit + Snyk
   - Scans: Direct and transitive dependencies
   - Detects: Known CVEs in packages

6. **DAST - Dynamic Scanning** (~12 min)
   - Tool: OWASP ZAP Baseline Scan
   - Scans: Running application on port 3000
   - Detects: Runtime vulnerabilities (XSS, SQLi, etc.)

7. **Full Regression Tests** (~5 min)
   - Runs complete test suite
   - Validates no regressions introduced

8. **Staging & E2E Tests** (~5 min)
   - Smoke tests on critical functions
   - End-to-end user journey validation

9. **Load Testing** (~3 min)
   - Apache Bench load tests
   - Validates application performance under load

10. **Quality Gate** (<1 min)
    - Aggregates SAST + SCA + DAST results
    - Enforces strict thresholds (0 vulnerabilities)
    - Blocks merge if thresholds exceeded

11. **PR Comment** (<1 min)
    - Posts detailed results to PR
    - Shows vulnerability counts by severity
    - Provides pass/fail status

## 🎯 Quality Gate Thresholds

The pipeline enforces **ZERO-TOLERANCE** for production:

| Severity | CVSS Range | Threshold | Aggregation |
|----------|------------|-----------|-------------|
| 🔴 Critical | ≥9.0 | **0** | SAST + SCA + DAST |
| 🟠 High | 7.0-8.9 | **0** | SAST + SCA + DAST |
| 🟡 Medium | 4.0-6.9 | **0** | SCA + DAST |
| 🔵 Low | <4.0 | **0** | SCA + DAST |

**If any threshold is exceeded, the pipeline FAILS and merge is blocked.**

## 🛡️ Security Tools

### SAST: Semgrep
- **What:** Static Application Security Testing
- **Scans:** Source code without execution
- **Detects:** Code-level vulnerabilities (injection flaws, insecure crypto, etc.)
- **Config:** `semgrep --config=auto` (community rules)

### SCA: npm audit + Snyk
- **What:** Software Composition Analysis
- **Scans:** Dependencies in `package.json` and `package-lock.json`
- **Detects:** Known CVEs in third-party libraries
- **Config:** `--audit-level=high` for npm, `--severity-threshold=high` for Snyk

### DAST: OWASP ZAP
- **What:** Dynamic Application Security Testing
- **Scans:** Running application via HTTP requests
- **Detects:** Runtime vulnerabilities (XSS, SQLi, CSRF, etc.)
- **Config:** Baseline scan with custom rules in `zap-config.conf`

## 📊 Workflow Artifacts

Each pipeline run generates downloadable artifacts:

- `coverage-reports/` - Code coverage HTML/JSON reports
- `sast-results/` - Semgrep JSON output
- `sca-results/` - npm audit + Snyk JSON output
- `dast-results/` - OWASP ZAP JSON/HTML reports
- `quality-gate-summary/` - Aggregated security summary
- `e2e-logs/` - E2E test execution logs
- `load-test-results/` - Load test metrics

## 🔧 Configuration Files

### quality-gate.py
Python script that:
- Parses JSON outputs from SAST, SCA, DAST tools
- Aggregates vulnerabilities by CVSS severity
- Enforces thresholds (configurable)
- Generates JSON summary for PR comments
- Exits with code 1 if thresholds exceeded

### pr-comment.sh
Bash script that:
- Reads `quality-gate-summary.json`
- Generates formatted markdown comment
- Shows vulnerability breakdown by tool and severity
- Lists pipeline step execution status
- Provides actionable next steps

### zap-config.conf
OWASP ZAP configuration:
- Defines which rules to WARN vs FAIL
- Customized for Juice Shop's intentional vulnerabilities
- Balances detection with false positive reduction

## 🚦 Branch Protection Requirements

To enable this pipeline, configure these branch protection rules on `main`:

### Required Settings:
- ✅ Require pull request reviews: **2 approvals**
- ✅ Require status checks to pass:
  - `validate-branch`
  - `build`
  - `test`
  - `sast`
  - `sca`
  - `dast`
  - `regression-tests`
  - `staging-tests`
  - `load-tests`
  - `quality-gate`
  - `comment-pr`
- ✅ Include administrators: **YES**
- ✅ Restrict direct pushes: **YES**
- ❌ Allow force pushes: **NO**

**See:** [BRANCH_PROTECTION_SETUP.md](BRANCH_PROTECTION_SETUP.md) for detailed setup guide.

## 📝 Usage

### Creating a Release PR

```bash
# Ensure you're on dev branch
git checkout dev

# Create release branch (follow naming convention)
git checkout -b release/v.19.1.251105

# Make your changes
git add .
git commit -m "feat: new feature for release v19.1"
git push -u origin release/v.19.1.251105

# Create PR on GitHub targeting 'main'
# Pipeline will automatically run
```

### Monitoring Pipeline

1. Go to **Actions** tab in GitHub
2. Click on the workflow run
3. Monitor each job's progress
4. Download artifacts for detailed reports

### Interpreting Results

**Green (✅):**
- All security checks passed
- Zero vulnerabilities detected
- Safe to merge after approvals

**Red (❌):**
- Security vulnerabilities detected
- Check PR comment for details
- Fix issues and push new commits
- Pipeline will re-run automatically

## 🐛 Troubleshooting

### Pipeline Timeout
- Increase `timeout-minutes` in workflow file
- Check if external services (Snyk API) are slow
- Consider using self-hosted runners

### DAST Fails to Start App
- Check `app.log` artifact for errors
- Verify Node.js version compatibility
- Increase wait time in DAST job

### False Positives in SAST/DAST
- Review findings manually
- Add exceptions in tool configs
- Document accepted risks

### Quality Gate Too Strict
**Note:** Juice Shop is intentionally vulnerable!
- For production apps: Fix all vulnerabilities
- For training/demo: Temporarily adjust thresholds in `quality-gate.py`

## 🔐 Security Considerations

### Secrets Management
Required secrets (configure in repository settings):
- `SNYK_TOKEN` - For Snyk SCA scanning (optional)
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions

### Artifact Retention
- Security scan results contain sensitive findings
- Artifacts auto-expire after 90 days (GitHub default)
- Consider reducing retention for compliance

### Public vs Private Repositories
- Be cautious with public repos (findings are public)
- Use private repos for production applications
- Juice Shop is public (intentionally vulnerable for training)

## 📚 Documentation

- [GitHub Actions Workflows](https://docs.github.com/en/actions/using-workflows)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Semgrep Rules](https://semgrep.dev/docs/writing-rules/overview/)
- [OWASP ZAP Baseline Scan](https://www.zaproxy.org/docs/docker/baseline-scan/)
- [npm audit](https://docs.npmjs.com/cli/v8/commands/npm-audit)
- [Snyk CLI](https://docs.snyk.io/snyk-cli)

## 🤝 Contributing

To modify the pipeline:

1. Edit workflow file: `.github/workflows/release-to-main.yml`
2. Update scripts in `.github/scripts/` as needed
3. Test changes in a feature branch first
4. Document changes in this README
5. Submit PR with clear description

## 📞 Support

For issues with the pipeline:
1. Check [BRANCH_PROTECTION_SETUP.md](BRANCH_PROTECTION_SETUP.md) troubleshooting section
2. Review workflow run logs in Actions tab
3. Download and analyze artifacts
4. Open an issue with:
   - Workflow run URL
   - Error messages
   - Relevant logs

---

**Version:** 1.0.0
**Last Updated:** 2025-11-04
**Maintained by:** DevSecOps Team
**License:** MIT (same as OWASP Juice Shop)
