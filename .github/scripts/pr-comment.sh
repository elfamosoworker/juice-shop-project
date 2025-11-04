#!/bin/bash
# PR Comment Generator for DevSecOps Pipeline Results
# Generates a formatted markdown comment with security scan results

set -e

SUMMARY_FILE="${1:-quality-gate-summary.json}"

if [ ! -f "$SUMMARY_FILE" ]; then
    echo "Error: Summary file not found: $SUMMARY_FILE"
    exit 1
fi

# Parse JSON summary
TOTAL_CRITICAL=$(jq -r '.total_critical' "$SUMMARY_FILE")
TOTAL_HIGH=$(jq -r '.total_high' "$SUMMARY_FILE")
TOTAL_MEDIUM=$(jq -r '.total_medium' "$SUMMARY_FILE")
TOTAL_LOW=$(jq -r '.total_low' "$SUMMARY_FILE")
TOTAL=$(jq -r '.total' "$SUMMARY_FILE")
PASSED=$(jq -r '.passed' "$SUMMARY_FILE")

SAST_CRITICAL=$(jq -r '.sast.critical' "$SUMMARY_FILE")
SAST_HIGH=$(jq -r '.sast.high' "$SUMMARY_FILE")

SCA_CRITICAL=$(jq -r '.sca.critical' "$SUMMARY_FILE")
SCA_HIGH=$(jq -r '.sca.high' "$SUMMARY_FILE")
SCA_MEDIUM=$(jq -r '.sca.medium' "$SUMMARY_FILE")
SCA_LOW=$(jq -r '.sca.low' "$SUMMARY_FILE")

DAST_CRITICAL=$(jq -r '.dast.critical' "$SUMMARY_FILE")
DAST_HIGH=$(jq -r '.dast.high' "$SUMMARY_FILE")
DAST_MEDIUM=$(jq -r '.dast.medium' "$SUMMARY_FILE")
DAST_LOW=$(jq -r '.dast.low' "$SUMMARY_FILE")

# Determine status
if [ "$PASSED" = "true" ]; then
    STATUS_EMOJI="✅"
    STATUS_TEXT="PASSED"
    STATUS_COLOR="🟢"
else
    STATUS_EMOJI="❌"
    STATUS_TEXT="FAILED"
    STATUS_COLOR="🔴"
fi

# Generate severity status
CRITICAL_STATUS="✅"
[ "$TOTAL_CRITICAL" -gt 0 ] && CRITICAL_STATUS="❌"

HIGH_STATUS="✅"
[ "$TOTAL_HIGH" -gt 0 ] && HIGH_STATUS="❌"

MEDIUM_STATUS="✅"
[ "$TOTAL_MEDIUM" -gt 0 ] && MEDIUM_STATUS="❌"

LOW_STATUS="✅"
[ "$TOTAL_LOW" -gt 0 ] && LOW_STATUS="❌"

# Generate PR comment
cat <<EOF
## $STATUS_EMOJI DevSecOps Pipeline - Quality Gate $STATUS_TEXT

$STATUS_COLOR **Status:** $STATUS_TEXT | **Total Vulnerabilities:** $TOTAL

---

### 📊 Security Vulnerability Summary

| Severity | Count | SAST | SCA | DAST | Threshold | Status |
|----------|------:|-----:|----:|-----:|----------:|:------:|
| 🔴 **Critical** (CVSS ≥9.0) | **$TOTAL_CRITICAL** | $SAST_CRITICAL | $SCA_CRITICAL | $DAST_CRITICAL | 0 | $CRITICAL_STATUS |
| 🟠 **High** (CVSS 7.0-8.9) | **$TOTAL_HIGH** | $SAST_HIGH | $SCA_HIGH | $DAST_HIGH | 0 | $HIGH_STATUS |
| 🟡 **Medium** (CVSS 4.0-6.9) | **$TOTAL_MEDIUM** | - | $SCA_MEDIUM | $DAST_MEDIUM | 0 | $MEDIUM_STATUS |
| 🔵 **Low** (CVSS <4.0) | **$TOTAL_LOW** | - | $SCA_LOW | $DAST_LOW | 0 | $LOW_STATUS |

---

### 🔍 Pipeline Execution Summary

| Step | Description | Duration | Status |
|-----:|------------|----------|:------:|
| 1 | Branch name validation | <1 min | ✅ |
| 2 | Build application | ~2 min | ✅ |
| 3 | Unit & integration tests (coverage ≥70%) | ~3 min | ✅ |
| 4 | **SAST** - Semgrep static analysis | ~5 min | ✅ |
| 5 | **SCA** - Dependency scanning (npm audit + Snyk) | ~4 min | ✅ |
| 6 | **DAST** - OWASP ZAP dynamic scan | ~12 min | ✅ |
| 7 | Full regression test suite | ~5 min | ✅ |
| 8 | Staging & E2E tests | ~5 min | ✅ |
| 9 | Load testing | ~3 min | ✅ |
| 10 | **Quality gate analysis** | <1 min | $STATUS_EMOJI |
| 11 | PR comment (this message) | <1 min | ✅ |

**Total Pipeline Runtime:** ~30 minutes

---

### 📋 Security Tool Details

#### 🔍 SAST (Static Application Security Testing)
- **Tool:** Semgrep with OWASP ruleset
- **Findings:** Critical: $SAST_CRITICAL, High: $SAST_HIGH
- **Coverage:** TypeScript, JavaScript, YAML, JSON

#### 📦 SCA (Software Composition Analysis)
- **Tools:** npm audit + Snyk
- **Findings:** Critical: $SCA_CRITICAL, High: $SCA_HIGH, Medium: $SCA_MEDIUM, Low: $SCA_LOW
- **Scanned:** Direct + transitive dependencies

#### 🌐 DAST (Dynamic Application Security Testing)
- **Tool:** OWASP ZAP Baseline Scan
- **Findings:** Critical: $DAST_CRITICAL, High: $DAST_HIGH, Medium: $DAST_MEDIUM, Low: $DAST_LOW
- **Target:** Running Juice Shop instance

---

### 🎯 Next Steps

EOF

if [ "$PASSED" = "true" ]; then
    cat <<EOF
✅ **Quality gate passed!** This release branch is ready for production.

**Pre-merge checklist:**
- [ ] Code review by 2+ team members
- [ ] All required approvals obtained
- [ ] Release notes updated
- [ ] Stakeholders notified
- [ ] Merge to \`main\` branch

🚀 **Ready to deploy to production!**
EOF
else
    cat <<EOF
❌ **Quality gate failed!** Security vulnerabilities must be resolved before merging.

**Required actions:**
1. 🔍 **Review SAST findings** - Check \`semgrep-results.json\` in artifacts
2. 📦 **Update dependencies** - Fix vulnerable packages identified by SCA
3. 🌐 **Fix runtime issues** - Address DAST findings from OWASP ZAP
4. ✅ **Re-run pipeline** - Push fixes and wait for green status

**Failure reasons:**
EOF

    # Add failure details if available
    FAILURES=$(jq -r '.failures[]' "$SUMMARY_FILE" 2>/dev/null || echo "")
    if [ -n "$FAILURES" ]; then
        echo "$FAILURES" | while IFS= read -r failure; do
            echo "- ❌ $failure"
        done
    fi

    cat <<EOF

⚠️  **Merge is blocked until all security issues are resolved.**
EOF
fi

cat <<EOF

---

### 📚 Additional Resources

- 📊 [View detailed security reports](../../actions) (check workflow artifacts)
- 📖 [DevSecOps Documentation](https://owasp.org/www-project-devsecops-guideline/)
- 🔒 [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- 🛡️ [Vulnerability Remediation Guide](https://cheatsheetseries.owasp.org/)

---

<sub>🤖 Generated by DevSecOps Pipeline | 🔐 OWASP Juice Shop | ⚡ Powered by GitHub Actions</sub>
EOF
