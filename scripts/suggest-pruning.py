#!/usr/bin/env python3
"""
Enhanced pruning analyzer with guardrail detection for Issue #119.
Safely identifies pruning targets while protecting critical workflow content.
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Set

from sst3_limits import count_tokens as _count_tokens

class GuardrailAwarePruningAnalyzer:
    """Analyze SST3 content for pruning with guardrail protection."""

    # Critical patterns that indicate workflow guardrails
    GUARDRAIL_MARKERS = [
        # Workflow critical sections
        'housekeeping', 'Housekeeping', 'File Housekeeping',
        'cleanup', 'Cleanup', 'Post-Stage Cleanup',

        # Stage markers and workflow structure
        'Stage 1', 'Stage 2', 'Stage 3', 'Stage 4', 'Stage 5',
        'Meta-Testing', 'Test & Refine',

        # Quality and validation gates
        'Self-Check', 'self-check', 'Entry validation', 'Exit criteria',
        'Token Budget', 'context management', 'Context Management',

        # Critical instructions
        'CRITICAL', 'MANDATORY', 'MUST NOT', 'NEVER', 'DO NOT',
        'Common Mistake', 'DON\'Ts', "DON'Ts L",

        # Self-healing and automation
        'self-healing', 'Self-healing', 'autonomous', 'Autonomous',
        'Verification', 'verification gate',

        # Orchestrator and delegation
        'Orchestrator', 'orchestrator', 'Subagent', 'subagent',
        'delegation', 'Delegation',

        # Templates and standards
        'Quick-Fix', 'quick-fix', 'Template', 'STANDARDS',
        'Handover', 'handover', 'Checkpoint',

        # Architecture and structure
        '5-stage', '5 stages', 'workflow flow', 'Workflow Flow',
    ]

    # Section headers that are critical (exact match)
    PROTECTED_SECTIONS = {
        'Pre-Stage Housekeeping',
        'Post-Stage Cleanup',
        'Self-Check',
        'Entry Validation',
        'DON\'Ts',
        'Common Mistakes',
        'Token Budget Check',
        'File Tracking',
        'Handover Process',
        'Quick-Fix Criteria',
        'Stage Summaries',
    }

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.sst3_path = base_path / 'SST3'
        self.issue_history_limit = 20

    def count_tokens(self, text: str) -> int:
        """Count tokens using character approximation."""
        return _count_tokens(text)

    def is_guardrail(self, content: str, context: str = '') -> Tuple[bool, str]:
        """
        Check if content contains guardrail markers.
        Returns (is_protected, reason)
        """
        # Check for explicit guardrail markers
        for marker in self.GUARDRAIL_MARKERS:
            if marker in content:
                return True, f"Contains guardrail marker: '{marker}'"

        # Check if content is in a protected section
        for section in self.PROTECTED_SECTIONS:
            if section in context or section in content:
                return True, f"Part of protected section: '{section}'"

        # Check for DON'T lists (critical instructions)
        if re.search(r'-\s+(NEVER|DO NOT|AVOID|MUST NOT)', content):
            return True, "Contains critical DON'T instruction"

        # Check for workflow structure markers
        if re.search(r'Stage \d+:', content):
            return True, "Contains stage workflow structure"

        # Check for checklist items with critical markers
        if re.search(r'-\s+\[\s*\]\s+(CRITICAL|MANDATORY)', content, re.IGNORECASE):
            return True, "Contains critical checklist item"

        return False, ""

    def analyze_section_safety(self, section: str, file_path: Path) -> Dict:
        """
        Deep safety analysis of a section.
        Returns safety score and reasons.
        """
        safety_flags = []
        risk_score = 0  # Lower is safer

        # Check 1: Guardrail detection
        is_protected, reason = self.is_guardrail(section)
        if is_protected:
            risk_score += 100  # Extremely high risk
            safety_flags.append(f"GUARDRAIL: {reason}")

        # Check 2: Contains workflow instructions
        if re.search(r'(\[\s*\]|Step \d+:|###\s+\d+\.)', section):
            risk_score += 20
            safety_flags.append("Contains structured workflow steps")

        # Check 3: Contains code examples or commands
        if '```' in section or re.search(r'`[^`]+`', section):
            risk_score += 5
            safety_flags.append("Contains code examples (may be illustrative)")

        # Check 4: References other critical files
        if re.search(r'\.\./\w+/[\w-]+\.md', section):
            risk_score += 10
            safety_flags.append("References other workflow files")

        # Check 5: Part of template or standard
        if 'template' in str(file_path).lower() or 'standard' in str(file_path).lower():
            risk_score += 30
            safety_flags.append("Part of template or standard file")

        return {
            'risk_score': risk_score,
            'safety_flags': safety_flags,
            'is_safe_to_prune': risk_score < 10  # Only low-risk items safe to prune
        }

    def _read_all_md_files(self) -> Dict[Path, str]:
        """Read all non-archived .md files once into a dict."""
        files = {}
        for md_file in self.sst3_path.rglob('*.md'):
            if 'archive' in str(md_file):
                continue
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    files[md_file] = f.read()
            except UnicodeDecodeError:
                try:
                    with open(md_file, 'r', encoding='cp1252') as f:
                        files[md_file] = f.read()
                except Exception:
                    continue
        return files

    def find_duplicate_content(self, all_files: Dict[Path, str]) -> List[Dict]:
        """Find duplicate content with guardrail awareness."""
        duplicates = []
        content_map = {}

        for md_file, content in all_files.items():

            # Extract paragraphs
            paragraphs = re.split(r'\n\n+', content)
            for para in paragraphs:
                para_clean = para.strip()
                if len(para_clean) < 100:  # Only longer paragraphs
                    continue

                # Check if this paragraph is protected
                is_protected, reason = self.is_guardrail(para_clean)
                if is_protected:
                    continue  # Skip guardrails

                # Normalize for comparison
                para_normalized = re.sub(r'\s+', ' ', para_clean.lower())

                if para_normalized in content_map:
                    # Found duplicate - analyze safety
                    safety = self.analyze_section_safety(para_clean, md_file)
                    tokens = self.count_tokens(para_clean)

                    duplicates.append({
                        'type': 'duplicate',
                        'file1': str(content_map[para_normalized].relative_to(self.base_path)),
                        'file2': str(md_file.relative_to(self.base_path)),
                        'content': para_clean[:100] + '...',
                        'tokens': tokens,
                        'reason': 'Duplicate content across files',
                        'risk_score': safety['risk_score'],
                        'safety_flags': safety['safety_flags'],
                        'is_safe': safety['is_safe_to_prune']
                    })
                else:
                    content_map[para_normalized] = md_file

        return duplicates

    def find_verbose_sections(self, all_files: Dict[Path, str]) -> List[Dict]:
        """Identify verbose sections with guardrail protection."""
        verbose_sections = []

        for md_file, content in all_files.items():

            # Split into sections
            sections = re.split(r'\n## ', content)
            for section in sections:
                # Check if section is protected
                section_header = section.split('\n')[0] if section else ''
                is_protected, reason = self.is_guardrail(section, section_header)
                if is_protected:
                    continue

                lines = section.split('\n')
                if len(lines) < 15:  # Only consider longer sections
                    continue

                # Check for verbose patterns
                verbose_indicators = [
                    len(re.findall(r'\bfor example\b', section, re.IGNORECASE)),
                    len(re.findall(r'\bi\.e\.\b', section, re.IGNORECASE)),
                    len(re.findall(r'\be\.g\.\b', section, re.IGNORECASE)),
                    len(re.findall(r'\bin other words\b', section, re.IGNORECASE)),
                    len(re.findall(r'\bspecifically\b', section, re.IGNORECASE)),
                ]

                verbose_score = sum(verbose_indicators)
                if verbose_score > 4:  # Raised threshold
                    safety = self.analyze_section_safety(section, md_file)
                    tokens = self.count_tokens(section)

                    verbose_sections.append({
                        'file': str(md_file.relative_to(self.base_path)),
                        'type': 'verbose',
                        'section': lines[0][:80],
                        'lines': len(lines),
                        'tokens': tokens,
                        'verbose_score': verbose_score,
                        'reason': f'Verbose section with {verbose_score} explanation markers',
                        'potential_savings': tokens // 4,  # Conservative estimate
                        'risk_score': safety['risk_score'],
                        'safety_flags': safety['safety_flags'],
                        'is_safe': safety['is_safe_to_prune']
                    })

        return verbose_sections

    def find_obsolete_content(self, all_files: Dict[Path, str]) -> List[Dict]:
        """Find obsolete content with guardrail protection."""
        obsolete_items = []

        obsolete_patterns = [
            (r'186 files', 'References old file count (reduced to 99)'),
            (r'SST/archive/', 'References archived content'),
            (r'stage[-\s]*(7|8|9|10|11|12)\b', 'References non-existent stages'),
        ]

        for md_file, content in all_files.items():
            for pattern, reason in obsolete_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    lines = content.split('\n')
                    obsolete_lines = [line for line in lines if re.search(pattern, line, re.IGNORECASE)]

                    # Check each line for guardrails
                    safe_lines = []
                    for line in obsolete_lines:
                        is_protected, _ = self.is_guardrail(line)
                        if not is_protected:
                            safe_lines.append(line)

                    if safe_lines:
                        tokens = sum(self.count_tokens(line) for line in safe_lines)
                        safety = self.analyze_section_safety('\n'.join(safe_lines), md_file)

                        obsolete_items.append({
                            'file': str(md_file.relative_to(self.base_path)),
                            'type': 'obsolete',
                            'pattern': pattern,
                            'occurrences': len(safe_lines),
                            'tokens': tokens,
                            'reason': reason,
                            'risk_score': safety['risk_score'],
                            'safety_flags': safety['safety_flags'],
                            'is_safe': safety['is_safe_to_prune']
                        })

        return obsolete_items

    def find_redundant_examples(self, all_files: Dict[Path, str]) -> List[Dict]:
        """Find excessive examples that could be consolidated."""
        redundant = []

        for md_file, content in all_files.items():
            # Find example sections
            example_sections = re.findall(
                r'(###?\s*Example[s]?.*?(?=\n##|\Z))',
                content,
                re.DOTALL | re.IGNORECASE
            )

            for example in example_sections:
                # Check if protected
                is_protected, reason = self.is_guardrail(example)
                if is_protected:
                    continue

                tokens = self.count_tokens(example)
                if tokens > 200:  # Only flag large examples
                    safety = self.analyze_section_safety(example, md_file)

                    redundant.append({
                        'file': str(md_file.relative_to(self.base_path)),
                        'type': 'verbose-example',
                        'tokens': tokens,
                        'reason': f'Large example section ({tokens} tokens)',
                        'potential_savings': tokens // 3,
                        'risk_score': safety['risk_score'],
                        'safety_flags': safety['safety_flags'],
                        'is_safe': safety['is_safe_to_prune']
                    })

        return redundant

    def generate_pruning_report(self) -> str:
        """Generate guardrail-aware pruning recommendations."""
        print("[*] Analyzing SST3 for safe pruning opportunities...")
        print("    (Guardrail protection enabled)")

        # Read all files once (eliminates 3 redundant rglob+open passes)
        print("  [*] Reading all markdown files...")
        all_files = self._read_all_md_files()

        # Collect all candidates
        candidates = []

        print("  [*] Checking for obsolete content...")
        candidates.extend(self.find_obsolete_content(all_files))

        print("  [*] Detecting duplicate content...")
        candidates.extend(self.find_duplicate_content(all_files))

        print("  [*] Identifying verbose sections...")
        candidates.extend(self.find_verbose_sections(all_files))

        print("  [*] Finding verbose examples...")
        candidates.extend(self.find_redundant_examples(all_files))

        # Filter to safe items only
        safe_candidates = [c for c in candidates if c.get('is_safe', False)]
        unsafe_candidates = [c for c in candidates if not c.get('is_safe', False)]

        # Sort by risk score (safest first) then by tokens
        safe_candidates.sort(key=lambda x: (x.get('risk_score', 0), -x.get('tokens', 0)))

        # Generate report
        report = []
        report.append("# SST3 Safe Pruning Recommendations (Issue #119)")
        report.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"**Analysis Method**: Guardrail-aware scanning")
        report.append(f"**Total candidates found**: {len(candidates)}")
        report.append(f"**Safe to prune**: {len(safe_candidates)}")
        report.append(f"**Protected (unsafe)**: {len(unsafe_candidates)}")

        total_safe_savings = sum(c.get('tokens', 0) for c in safe_candidates)
        potential_savings = sum(c.get('potential_savings', c.get('tokens', 0)) for c in safe_candidates)

        report.append(f"\n**Safe pruning savings**: {total_safe_savings:,} tokens (direct removal)")
        report.append(f"**Potential with edits**: {potential_savings:,} tokens (after condensing)\n")

        # Safe candidates by type
        report.append("## [SAFE] SAFE PRUNING TARGETS\n")
        report.append("*These items passed all 5 guardrail checks*\n")

        by_type = {}
        for candidate in safe_candidates:
            cat_type = candidate['type']
            if cat_type not in by_type:
                by_type[cat_type] = []
            by_type[cat_type].append(candidate)

        for cat_type, items in sorted(by_type.items(), key=lambda x: -sum(c.get('tokens', 0) for c in x[1])):
            type_savings = sum(c.get('tokens', 0) for c in items)
            report.append(f"### {cat_type.replace('-', ' ').title()} ({len(items)} items, {type_savings:,} tokens)\n")

            for i, item in enumerate(items[:10], 1):  # Show top 10 per category
                report.append(f"**{i}. {item.get('file', 'Multiple files')}**")
                report.append(f"   - Tokens: {item.get('tokens', 0):,}")
                report.append(f"   - Risk Score: {item.get('risk_score', 0)} (lower is safer)")
                report.append(f"   - Reason: {item['reason']}")

                if item.get('safety_flags'):
                    report.append(f"   - Notes: {', '.join(item['safety_flags'])}")

                if 'potential_savings' in item and item['potential_savings'] != item.get('tokens', 0):
                    report.append(f"   - Suggested: Condense to save ~{item['potential_savings']:,} tokens")

                report.append("")

            if len(items) > 10:
                report.append(f"*... and {len(items) - 10} more safe items*\n")

        # Protected items summary
        report.append("\n## [PROTECTED] PROTECTED ITEMS (DO NOT PRUNE)\n")
        report.append(f"*{len(unsafe_candidates)} items flagged as critical workflow content*\n")

        protected_by_reason = {}
        for item in unsafe_candidates:
            for flag in item.get('safety_flags', []):
                if flag not in protected_by_reason:
                    protected_by_reason[flag] = 0
                protected_by_reason[flag] += 1

        report.append("**Protection reasons:**\n")
        for reason, count in sorted(protected_by_reason.items(), key=lambda x: -x[1])[:10]:
            report.append(f"- {reason}: {count} items")

        report.append("")

        # Recommended action plan
        report.append("\n## [PLAN] RECOMMENDED ACTION PLAN\n")
        report.append("### Phase 1: Quick Wins (Safest, ~1-2 hours)\n")
        report.append("Target: Remove exact duplicates and obsolete references\n")

        phase1_items = [c for c in safe_candidates if c['type'] in ['obsolete', 'duplicate'] and c['risk_score'] == 0]
        phase1_savings = sum(c.get('tokens', 0) for c in phase1_items)
        report.append(f"- Items: {len(phase1_items)}")
        report.append(f"- Savings: {phase1_savings:,} tokens")
        report.append(f"- Risk: Minimal (zero-risk items only)\n")

        report.append("### Phase 2: Verbose Reduction (Medium risk, ~2-3 hours)\n")
        report.append("Target: Condense verbose sections and examples\n")

        phase2_items = [c for c in safe_candidates if c['type'] in ['verbose', 'verbose-example'] and c['risk_score'] < 10]
        phase2_savings = sum(c.get('potential_savings', c.get('tokens', 0)) for c in phase2_items)
        report.append(f"- Items: {len(phase2_items)}")
        report.append(f"- Potential savings: {phase2_savings:,} tokens")
        report.append(f"- Risk: Low (requires careful editing)\n")

        report.append("### Phase 3: Review & Test (Critical, ~1 hour)\n")
        report.append("- Run check-size-limits.py")
        report.append("- Verify workflow files still functional")
        report.append("- Test one complete SST3 workflow execution")
        report.append("- Commit with clear documentation\n")

        # Quality checks
        report.append("\n## [CHECKS] QUALITY CHECKS FOR EACH TARGET\n")
        report.append("Before pruning any item, verify:\n")
        report.append("1. [X] NOT in Protected Sections list above")
        report.append("2. [X] Does NOT contain CRITICAL/MANDATORY/NEVER markers")
        report.append("3. [X] Does NOT reference housekeeping or self-checks")
        report.append("4. [X] Does NOT contain stage workflow instructions")
        report.append("5. [X] Does NOT break file references in other documents\n")

        return '\n'.join(report)

def main():
    """Main function."""
    base_path = Path.cwd()

    # Ensure we're in the right directory
    if not (base_path / 'SST3').exists():
        print("[ERROR] SST3 directory not found. Run from dotfiles root.")
        print(f"        Current directory: {base_path}")
        return 1

    analyzer = GuardrailAwarePruningAnalyzer(base_path)

    # Generate and display report
    report = analyzer.generate_pruning_report()
    print("\n" + "=" * 60)
    print(report)

    # Save to file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    output_file = base_path / 'analysis' / f'pruning-recommendations-{timestamp}.md'
    output_file.parent.mkdir(exist_ok=True)

    try:
        tmp = output_file.with_suffix('.tmp')
        tmp.write_text(report, encoding='utf-8')
        tmp.replace(output_file)
        print(f"\n[SAVED] Report saved to: {output_file}")
        return 0
    except Exception as e:
        print(f"\n[WARNING] Could not save report: {e}")
        print("         Report displayed above can be copied manually.")
        return 0

if __name__ == '__main__':
    exit(main())
