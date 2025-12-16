#!/usr/bin/env python3
"""Format code review JSON into beautiful GitHub markdown."""

import json
import sys


def format_finding_details(finding):
    """Format a single finding with nice structure."""
    lines = []
    location = f"`{finding['file']}:{finding['line']}`" if finding.get('line') else f"`{finding['file']}`"
    
    # Category icons
    category_icons = {
        'security': '🔒',
        'performance': '⚡',
        'maintainability': '🔧',
        'style': '💅',
        'logic': '🧠',
        'documentation': '📝'
    }
    icon = category_icons.get(finding.get('category', '').lower(), '📌')
    
    lines.append(f"**{icon} {finding['category'].title()}** · {location}")
    lines.append("")
    lines.append(f"**Issue:** {finding['message']}")
    lines.append("")
    lines.append(f"**💡 Suggestion:** {finding['suggestion']}")
    lines.append("")
    
    return "\n".join(lines)


def main():
    try:
        # Load review data
        with open('review.json', 'r') as f:
            review = json.load(f)
        
        summary = review.get('summary', 'Code review completed')
        score = review.get('score', 0)
        findings = review.get('findings', [])
        metadata = review.get('metadata', {})
        model = metadata.get('model', 'unknown')
        execution_time = metadata.get('execution_time_ms', 0)
        
        # Group by severity
        critical = [f for f in findings if f['severity'] == 'critical']
        high = [f for f in findings if f['severity'] == 'high']
        medium = [f for f in findings if f['severity'] == 'medium']
        low = [f for f in findings if f['severity'] == 'low']
        
        # Build markdown
        md = []
        
        # Header
        md.append("# 🤖 AI Code Review Report")
        md.append("")
        
        # Critical Issues Alert
        if critical:
            md.append("> [!WARNING]")
            md.append("> ### ⚠️ Critical Issues Detected")
            md.append(">")
            md.append(f"> Found **{len(critical)} critical** issue(s) that require immediate attention!")
            md.append("> Please address these before merging.")
            md.append("")
        
        # Summary Table
        score_emoji = "🟢" if score >= 8 else "🟡" if score >= 6 else "🟠" if score >= 4 else "🔴"
        
        md.append("## 📊 Review Summary")
        md.append("")
        md.append("| Metric | Value |")
        md.append("|--------|-------|")
        md.append(f"| **Quality Score** | {score_emoji} **{score:.1f}/10** |")
        md.append(f"| **Total Issues** | {len(findings)} |")
        md.append(f"| 🔴 Critical | {len(critical)} |")
        md.append(f"| 🟠 High | {len(high)} |")
        md.append(f"| 🟡 Medium | {len(medium)} |")
        md.append(f"| 🟢 Low | {len(low)} |")
        md.append("")
        
        # Summary Text
        if findings:
            md.append("### 💭 Overall Assessment")
            md.append("")
            md.append(f"> {summary}")
            md.append("")
        
        # Findings sections
        if not findings:
            md.append("---")
            md.append("")
            md.append("## ✅ Excellent Work!")
            md.append("")
            md.append("No issues found in this pull request. The code looks great! 🎉")
            md.append("")
        else:
            # Critical Issues
            if critical:
                md.append("---")
                md.append("")
                md.append("## 🔴 Critical Issues")
                md.append("")
                for idx, finding in enumerate(critical, 1):
                    md.append(f"<details open>")
                    md.append(f"<summary><b>#{idx} · {finding.get('category', 'Issue').title()}</b> in <code>{finding.get('file', 'unknown')}</code></summary>")
                    md.append("")
                    md.append(format_finding_details(finding))
                    md.append("</details>")
                    md.append("")
            
            # High Severity Issues
            if high:
                md.append("---")
                md.append("")
                md.append("## 🟠 High Severity Issues")
                md.append("")
                for idx, finding in enumerate(high, 1):
                    md.append(f"<details open>")
                    md.append(f"<summary><b>#{idx} · {finding.get('category', 'Issue').title()}</b> in <code>{finding.get('file', 'unknown')}</code></summary>")
                    md.append("")
                    md.append(format_finding_details(finding))
                    md.append("</details>")
                    md.append("")
            
            # Medium Severity Issues (Collapsed by default)
            if medium:
                md.append("---")
                md.append("")
                md.append("<details>")
                md.append(f"<summary><h2>🟡 Medium Severity Issues ({len(medium)})</h2></summary>")
                md.append("")
                for idx, finding in enumerate(medium, 1):
                    md.append(f"### #{idx} · {finding.get('category', 'Issue').title()}")
                    md.append("")
                    md.append(format_finding_details(finding))
                    if idx < len(medium):
                        md.append("---")
                        md.append("")
                md.append("</details>")
                md.append("")
            
            # Low Severity Issues (Collapsed by default)
            if low:
                md.append("---")
                md.append("")
                md.append("<details>")
                md.append(f"<summary><h2>🟢 Low Severity Issues ({len(low)})</h2></summary>")
                md.append("")
                for idx, finding in enumerate(low, 1):
                    md.append(f"### #{idx} · {finding.get('category', 'Issue').title()}")
                    md.append("")
                    md.append(format_finding_details(finding))
                    if idx < len(low):
                        md.append("---")
                        md.append("")
                md.append("</details>")
                md.append("")
        
        # Footer
        md.append("---")
        md.append("")
        md.append("<div align='center'>")
        md.append("")
        md.append(f"🤖 *Powered by AI Code Review Agents*")
        md.append("")
        md.append(f"Model: `{model}` · Execution Time: `{execution_time}ms`")
        md.append("")
        md.append("</div>")
        
        # Join and write
        markdown = "\n".join(md)
        with open('review_comment.md', 'w') as f:
            f.write(markdown)
        
        print("✅ Review formatted successfully")
        
        # Print summary to logs
        print(f"\n📊 Review Summary:")
        print(f"  Quality Score: {score:.1f}/10")
        print(f"  Total Findings: {len(findings)}")
        if findings:
            print(f"  🔴 Critical: {len(critical)}")
            print(f"  🟠 High: {len(high)}")
            print(f"  🟡 Medium: {len(medium)}")
            print(f"  🟢 Low: {len(low)}")
            if critical:
                print(f"\n⚠️  WARNING: {len(critical)} critical issue(s) detected!")
        else:
            print("  ✅ No issues found!")
        
    except Exception as e:
        print(f"❌ Error formatting review: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
