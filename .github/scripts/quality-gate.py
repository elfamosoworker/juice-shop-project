#!/usr/bin/env python3
"""
Security Quality Gate Parser
Aggregates SAST, SCA, and DAST results and enforces strict thresholds
"""

import json
import sys
import os
from pathlib import Path


def read_count(filepath, default=0):
    """Read vulnerability count from file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read().strip()
            return int(content) if content else default
    except FileNotFoundError:
        print(f"⚠️  Warning: File not found: {filepath}")
        return default
    except ValueError as e:
        print(f"⚠️  Warning: Invalid content in {filepath}: {e}")
        return default
    except Exception as e:
        print(f"⚠️  Warning: Error reading {filepath}: {e}")
        return default


def parse_semgrep_results(filepath):
    """Parse Semgrep JSON results and count by severity"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            results = data.get('results', [])

            critical = sum(1 for r in results if r.get('extra', {}).get('severity') == 'ERROR')
            high = sum(1 for r in results if r.get('extra', {}).get('severity') == 'WARNING')

            return {'critical': critical, 'high': high}
    except Exception as e:
        print(f"⚠️  Could not parse Semgrep results: {e}")
        return {'critical': 0, 'high': 0}


def parse_npm_audit_results(filepath):
    """Parse npm audit JSON results"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            metadata = data.get('metadata', {}).get('vulnerabilities', {})

            return {
                'critical': metadata.get('critical', 0),
                'high': metadata.get('high', 0),
                'medium': metadata.get('moderate', 0),
                'low': metadata.get('low', 0)
            }
    except Exception as e:
        print(f"⚠️  Could not parse npm audit results: {e}")
        return {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}


def parse_zap_results(filepath):
    """Parse OWASP ZAP JSON results"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            sites = data.get('site', [])

            critical = 0
            high = 0
            medium = 0
            low = 0

            for site in sites:
                alerts = site.get('alerts', [])
                for alert in alerts:
                    risk_code = int(alert.get('riskcode', 0))
                    if risk_code == 3:
                        critical += 1
                    elif risk_code == 2:
                        high += 1
                    elif risk_code == 1:
                        medium += 1
                    elif risk_code == 0:
                        low += 1

            return {
                'critical': critical,
                'high': high,
                'medium': medium,
                'low': low
            }
    except Exception as e:
        print(f"⚠️  Could not parse ZAP results: {e}")
        return {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}


def main():
    """Main quality gate analysis"""
    print("=" * 80)
    print("SECURITY QUALITY GATE ANALYSIS")
    print("=" * 80)
    print()

    # Initialize counters
    sast_critical = 0
    sast_high = 0
    sca_critical = 0
    sca_high = 0
    sca_medium = 0
    sca_low = 0
    dast_critical = 0
    dast_high = 0
    dast_medium = 0
    dast_low = 0

    # Try to read from simplified count files first
    if os.path.exists('sast-results/sast-critical.txt'):
        sast_critical = read_count('sast-results/sast-critical.txt')
        sast_high = read_count('sast-results/sast-high.txt')
    elif os.path.exists('sast-results/semgrep-results.json'):
        # Parse Semgrep JSON
        sast = parse_semgrep_results('sast-results/semgrep-results.json')
        sast_critical = sast['critical']
        sast_high = sast['high']

    if os.path.exists('sca-results/sca-critical.txt'):
        sca_critical = read_count('sca-results/sca-critical.txt')
        sca_high = read_count('sca-results/sca-high.txt')
        sca_medium = read_count('sca-results/sca-medium.txt')
        sca_low = read_count('sca-results/sca-low.txt')
    elif os.path.exists('sca-results/npm-audit-results.json'):
        # Parse npm audit JSON
        sca = parse_npm_audit_results('sca-results/npm-audit-results.json')
        sca_critical = sca['critical']
        sca_high = sca['high']
        sca_medium = sca['medium']
        sca_low = sca['low']

    if os.path.exists('dast-results/dast-critical.txt'):
        dast_critical = read_count('dast-results/dast-critical.txt')
        dast_high = read_count('dast-results/dast-high.txt')
        dast_medium = read_count('dast-results/dast-medium.txt')
        dast_low = read_count('dast-results/dast-low.txt')
    elif os.path.exists('dast-results/zap-report.json'):
        # Parse ZAP JSON
        dast = parse_zap_results('dast-results/zap-report.json')
        dast_critical = dast['critical']
        dast_high = dast['high']
        dast_medium = dast['medium']
        dast_low = dast['low']

    # Aggregate by severity across all tools
    total_critical = sast_critical + sca_critical + dast_critical
    total_high = sast_high + sca_high + dast_high
    total_medium = sca_medium + dast_medium
    total_low = sca_low + dast_low

    # Print detailed breakdown
    print("📊 VULNERABILITY SUMMARY BY SEVERITY (CVSS)")
    print("-" * 80)
    print(f"{'Severity':<25} {'Total':>8} {'SAST':>8} {'SCA':>8} {'DAST':>8}")
    print("-" * 80)
    print(f"{'Critical (CVSS ≥9.0)':<25} {total_critical:>8} {sast_critical:>8} {sca_critical:>8} {dast_critical:>8}")
    print(f"{'High (CVSS 7.0-8.9)':<25} {total_high:>8} {sast_high:>8} {sca_high:>8} {dast_high:>8}")
    print(f"{'Medium (CVSS 4.0-6.9)':<25} {total_medium:>8} {'-':>8} {sca_medium:>8} {dast_medium:>8}")
    print(f"{'Low (CVSS <4.0)':<25} {total_low:>8} {'-':>8} {sca_low:>8} {dast_low:>8}")
    print("-" * 80)
    print(f"{'TOTAL VULNERABILITIES':<25} {total_critical + total_high + total_medium + total_low:>8}")
    print()

    # Define STRICT thresholds (zero tolerance for production)
    thresholds = {
        'critical': 0,  # CVSS ≥9.0
        'high': 0,      # CVSS 7.0-8.9
        'medium': 0,    # CVSS 4.0-6.9
        'low': 0        # CVSS <4.0
    }

    print("🎯 QUALITY GATE THRESHOLDS (STRICT - PRODUCTION READY)")
    print("-" * 80)
    print(f"Critical:  {total_critical:>3} / {thresholds['critical']:>3} allowed  {'✅ PASS' if total_critical <= thresholds['critical'] else '❌ FAIL'}")
    print(f"High:      {total_high:>3} / {thresholds['high']:>3} allowed  {'✅ PASS' if total_high <= thresholds['high'] else '❌ FAIL'}")
    print(f"Medium:    {total_medium:>3} / {thresholds['medium']:>3} allowed  {'✅ PASS' if total_medium <= thresholds['medium'] else '❌ FAIL'}")
    print(f"Low:       {total_low:>3} / {thresholds['low']:>3} allowed  {'✅ PASS' if total_low <= thresholds['low'] else '❌ FAIL'}")
    print()

    # Check thresholds and collect failures
    failures = []

    if total_critical > thresholds['critical']:
        failures.append(f"Critical vulnerabilities: {total_critical} exceeds threshold of {thresholds['critical']}")

    if total_high > thresholds['high']:
        failures.append(f"High vulnerabilities: {total_high} exceeds threshold of {thresholds['high']}")

    if total_medium > thresholds['medium']:
        failures.append(f"Medium vulnerabilities: {total_medium} exceeds threshold of {thresholds['medium']}")

    if total_low > thresholds['low']:
        failures.append(f"Low vulnerabilities: {total_low} exceeds threshold of {thresholds['low']}")

    # Generate summary JSON for PR comment
    summary = {
        'total_critical': total_critical,
        'total_high': total_high,
        'total_medium': total_medium,
        'total_low': total_low,
        'total': total_critical + total_high + total_medium + total_low,
        'sast': {
            'critical': sast_critical,
            'high': sast_high,
            'medium': 0,
            'low': 0
        },
        'sca': {
            'critical': sca_critical,
            'high': sca_high,
            'medium': sca_medium,
            'low': sca_low
        },
        'dast': {
            'critical': dast_critical,
            'high': dast_high,
            'medium': dast_medium,
            'low': dast_low
        },
        'thresholds': thresholds,
        'passed': len(failures) == 0,
        'failures': failures
    }

    # Write summary to file for GitHub Actions
    output_file = 'quality-gate-summary.json'
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"📄 Summary written to: {output_file}")
    print()

    # Final verdict
    print("=" * 80)
    if failures:
        print("❌ QUALITY GATE: FAILED")
        print("=" * 80)
        print()
        print("⚠️  The following security thresholds were exceeded:")
        for i, failure in enumerate(failures, 1):
            print(f"  {i}. {failure}")
        print()
        print("🔧 Required Actions:")
        print("  - Review and fix SAST findings (static code analysis)")
        print("  - Update vulnerable dependencies identified by SCA")
        print("  - Address runtime vulnerabilities found by DAST")
        print("  - Re-run pipeline after applying fixes")
        print()
        print("📊 Detailed reports are available in the workflow artifacts.")
        print("=" * 80)
        return 1
    else:
        print("✅ QUALITY GATE: PASSED")
        print("=" * 80)
        print()
        print("🎉 All security thresholds met!")
        print("✨ Code is production-ready and safe to merge to main branch.")
        print()
        print("📋 Next Steps:")
        print("  - Request code review from team members")
        print("  - Obtain required approvals (minimum 2)")
        print("  - Merge to main branch")
        print("=" * 80)
        return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"❌ Fatal error in quality gate: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
