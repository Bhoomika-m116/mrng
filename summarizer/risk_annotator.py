import re
import html

# Comprehensive Legal Risk Factor Definitions covering all contractual risk domains
RISK_RULES = [
    {
        "id": "unilateral_termination",
        "title": "Unilateral Termination",
        "severity": "Critical",
        "color": "#dc2626", # Red
        "badge_class": "danger",
        "pattern": r"(?i)\b(terminat\w*\s+(?:immediately|forthwith|without\s+cause|at\s+will|for\s+convenience|upon\s+\d+\s+days)|immediate\s+cancellation|unilateral\s+termination|sole\s+discretion\s+to\s+terminat\w*|without\s+(?:prior\s+)?notice\s+terminat\w*|terminat\w*\s+without\s+(?:prior\s+)?notice|right\s+to\s+terminate|notice\s+of\s+default|cancel\w*\s+(?:immediately|without\s+notice))\b",
        "explanation": "Allows one party to unilaterally cancel or terminate the agreement immediately or with minimal notice without opportunity to cure default."
    },
    {
        "id": "unlimited_indemnity",
        "title": "Indemnification & Hold Harmless",
        "severity": "Critical",
        "color": "#dc2626", # Red
        "badge_class": "danger",
        "pattern": r"(?i)\b(indemnif\w*\s+and\s+hold\s+harmless|shall\s+indemnify|indemnif\w*\s+(?:against|from)\s+all|unlimited\s+liability|defend\s+and\s+indemnif\w*|sole\s+expense\s+defend|fullest\s+extent\s+permitted\s+by\s+law\s+indemnif\w*|indemnif\w*|hold\s+harmless|reimburse\s+against\s+losses)\b",
        "explanation": "Shifts legal liability, third-party claims, and uncapped financial damages directly onto the counterparty."
    },
    {
        "id": "liquidated_damages",
        "title": "Liquidated Damages & Penalties",
        "severity": "High",
        "color": "#ea580c", # Orange-Red
        "badge_class": "danger",
        "pattern": r"(?i)\b(liquidated\s+damages|penalt(?:y|ies)\s+of|forfeiture\s+of\s+(?:the\s+)?deposit|punitive\s+damages|default\s+(?:fee|fine|penalt\w*)|forfeit\w*\s+all\s+sums|accrue\s+interest\s+at|late\s+(?:fee|charge|penalty)|penal\s+interest|forfeit\w*)\b",
        "explanation": "Imposes predetermined severe financial penalties, late interest fees, or immediate deposit forfeiture upon alleged default."
    },
    {
        "id": "liability_exposure",
        "title": "Liability & Damage Exposure",
        "severity": "High",
        "color": "#ea580c", # Orange-Red
        "badge_class": "danger",
        "pattern": r"(?i)\b(joint\s+and\s+several(?:\s+liability)?|jointly\s+and\s+severally\s+liable|unlimited\s+liability|strictly\s+liable|sole\s+liability|liab\w*\s+for\s+all|liab\w*\s+for\s+any|aggregate\s+liability|consequential\s+damages|indirect\s+damages|losses\s+and\s+damages|liable|liability)\b",
        "explanation": "Broad liability exposure holding the party financially accountable for full losses, defaults, or consequential harms."
    },
    {
        "id": "non_compete",
        "title": "Non-Compete & Restraint of Trade",
        "severity": "High",
        "color": "#d97706", # Amber
        "badge_class": "warning",
        "pattern": r"(?i)\b(non[\s-]compete|covenant\s+not\s+to\s+compete|restraint\s+of\s+trade|prohibited\s+from\s+engaging|shall\s+not\s+solicit\s+(?:any\s+)?(?:client|employee|customer|vendor)|non[\s-]solicitation|restrictive\s+covenant)\b",
        "explanation": "Strict post-termination covenant prohibiting independent commercial practice, competing employment, or client solicitation."
    },
    {
        "id": "binding_arbitration",
        "title": "Binding Arbitration & Forum Lock",
        "severity": "Moderate",
        "color": "#b45309", # Amber
        "badge_class": "warning",
        "pattern": r"(?i)\b(binding\s+arbitration|waiv\w*\s+(?:the\s+)?right\s+to\s+trial\s+by\s+jury|class\s+action\s+waiver|exclusive\s+jurisdiction\s+of|irrevocably\s+submits?\s+to\s+the\s+jurisdiction|arbitrat\w*|exclusive\s+jurisdiction|governed\s+by\s+the\s+laws\s+of)\b",
        "explanation": "Bars public court litigation and jury trials, locking legal disputes into private arbitration or distant predetermined courts."
    },
    {
        "id": "as_is_disclaimer",
        "title": "Warranty Disclaimer ('As Is')",
        "severity": "Moderate",
        "color": "#b45309", # Amber
        "badge_class": "warning",
        "pattern": r"(?i)\b(as[\s-]is|without\s+warrant\w*\s+of\s+any\s+kind|disclaims?\s+all\s+warrant\w*|caveat\s+emptor|express\s+or\s+implied\s+warrant\w*\s+excluded|no\s+warranty|warrants?\s+nothing)\b",
        "explanation": "Shifts all operational defect and failure risks directly onto the buyer by excluding merchantability and fitness guarantees."
    },
    {
        "id": "auto_renewal",
        "title": "Silent Auto-Renewal & Lock-In",
        "severity": "Moderate",
        "color": "#ca8a04", # Amber
        "badge_class": "warning",
        "pattern": r"(?i)\b(automatically\s+renew\w*|auto[\s-]renewal|lock[\s-]in\s+period|evergreen\s+clause|irrevocable\s+for\s+a\s+period\s+of|successive\s+terms)\b",
        "explanation": "Automatically extends financial commitments for successive terms unless formal cancellation notice is given within strict deadlines."
    },
    {
        "id": "unilateral_modification",
        "title": "Unilateral Modification Rights",
        "severity": "High",
        "color": "#ea580c", # Orange-Red
        "badge_class": "danger",
        "pattern": r"(?i)\b(sole\s+discretion|unilateral\s+right\s+to\s+(?:amend|modify|change)|modify\s+at\s+any\s+time\s+without|at\s+its\s+absolute\s+discretion|amend\s+these\s+terms\s+without\s+notice)\b",
        "explanation": "Permits one contracting party to alter contractual obligations, price tiers, or performance terms without mutual assent."
    },
    {
        "id": "material_breach",
        "title": "Material Breach & Default Forfeiture",
        "severity": "Critical",
        "color": "#dc2626", # Red
        "badge_class": "danger",
        "pattern": r"(?i)\b(material\s+breach|immediate\s+repossession|event\s+of\s+default|cure\s+period\s+waived|immediate\s+eviction|breach\s+of\s+contract|in\s+the\s+event\s+of\s+breach|remed\w*\s+for\s+default)\b",
        "explanation": "Strict breach conditions triggering rapid legal remedies, asset repossession, forfeiture of rights, or accelerated debt collection."
    },
    {
        "id": "confidentiality_restrictions",
        "title": "Strict Confidentiality & Non-Disclosure",
        "severity": "Moderate",
        "color": "#b45309", # Amber
        "badge_class": "warning",
        "pattern": r"(?i)\b(strictest\s+confidence|non[\s-]disclosure|proprietary\s+information|trade\s+secret\w*|restricted\s+data|shall\s+not\s+(?:disclose|publish|transmit|reverse\s+engineer)|confidential\w*)\b",
        "explanation": "Heavy non-disclosure obligation; unauthorized release or leakage of protected information triggers immediate injunctions and damages."
    }
]

class RiskFactorAnnotator:
    def __init__(self):
        self.rules = RISK_RULES

    def has_any_risk(self, text):
        """Quick check whether text contains any risk keyword."""
        for rule in self.rules:
            if re.search(rule["pattern"], text):
                return True
        return False

    def get_sentence_risk_score(self, text):
        """Computes a risk boost weight for extractive summarizer ranking."""
        score = 0.0
        for rule in self.rules:
            matches = len(re.findall(rule["pattern"], text))
            if matches > 0:
                if rule["severity"] == "Critical":
                    score += 0.40 * matches
                elif rule["severity"] == "High":
                    score += 0.30 * matches
                else:
                    score += 0.15 * matches
        return min(score, 1.0)

    def analyze_and_underline_summary(self, summary_sentences):
        """
        Processes summary sentences, detects all risk factors, and applies
        bold, highly visible HTML underlining with inline warning badges and tooltips.
        """
        annotated_sentences = []
        all_detected_risks = []
        underlined_texts = []

        for sent_idx, sentence in enumerate(summary_sentences):
            sent_text = sentence.strip()
            if not sent_text:
                continue

            sentence_risks = []
            matches_to_apply = []

            for rule in self.rules:
                for match in re.finditer(rule["pattern"], sent_text):
                    start, end = match.span()
                    matched_phrase = match.group(0)
                    
                    risk_item = {
                        "rule_id": rule["id"],
                        "title": rule["title"],
                        "severity": rule["severity"],
                        "color": rule["color"],
                        "badge_class": rule["badge_class"],
                        "explanation": rule["explanation"],
                        "phrase": matched_phrase,
                        "sentence_index": sent_idx + 1,
                        "start": start,
                        "end": end
                    }
                    matches_to_apply.append(risk_item)
                    sentence_risks.append(risk_item)
                    all_detected_risks.append(risk_item)

            # Sort matches by start position ascending, longest match first
            matches_to_apply.sort(key=lambda x: (x["start"], -(x["end"] - x["start"])))
            
            # Non-overlapping filter
            non_overlapping = []
            last_end = -1
            for m in matches_to_apply:
                if m["start"] >= last_end:
                    non_overlapping.append(m)
                    last_end = m["end"]

            # Build underlined HTML
            underlined_html = self._apply_underlines(sent_text, non_overlapping, sent_idx + 1)
            underlined_texts.append(underlined_html)

            annotated_sentences.append({
                "sentence_index": sent_idx + 1,
                "original_text": sent_text,
                "underlined_html": underlined_html,
                "has_risk": len(sentence_risks) > 0,
                "risk_count": len(sentence_risks),
                "risks": sentence_risks
            })

        summary_underlined_text = " ".join(underlined_texts)

        # Deduplicate all_detected_risks by title and phrase for clean summary display
        unique_risks = []
        seen = set()
        for r in all_detected_risks:
            key = (r["rule_id"], r["phrase"].lower())
            if key not in seen:
                seen.add(key)
                unique_risks.append(r)

        return {
            "annotated_sentences": annotated_sentences,
            "detected_risks": unique_risks,
            "total_risk_count": len(all_detected_risks),
            "summary_underlined_html": summary_underlined_text
        }

    def _apply_underlines(self, sentence_text, matches, sent_num):
        """
        Replaces matched risk phrases with bold, highly visible underlined spans and warning badges.
        """
        if not matches:
            return html.escape(sentence_text)

        matches.sort(key=lambda x: x["start"], reverse=True)
        result = sentence_text

        for idx, m in enumerate(matches):
            start = m["start"]
            end = m["end"]
            matched_phrase = result[start:end]
            
            title_esc = html.escape(m["title"], quote=True)
            expl_esc = html.escape(m["explanation"], quote=True)
            sev_esc = html.escape(m["severity"], quote=True)
            phrase_esc = html.escape(matched_phrase)
            risk_id = f"risk-ref-{sent_num}-{idx}"

            # Bold underline styling with inline risk indicator
            if m["severity"] in ["Critical", "High"]:
                underline_style = "border-bottom: 3px solid #DC2626; text-decoration: underline wavy #DC2626; text-underline-offset: 4px; background: rgba(220,38,38,0.12); color: #991B1B; font-weight: 700; padding: 2px 5px; border-radius: 4px;"
                badge_html = f'<span class="badge bg-danger text-white ms-1 fw-bold" style="font-size: 0.72rem; vertical-align: middle;"><i class="bi bi-shield-fill-exclamation me-1"></i>RISK: {title_esc}</span>'
            else:
                underline_style = "border-bottom: 3px solid #D97706; text-decoration: underline wavy #D97706; text-underline-offset: 4px; background: rgba(217,119,6,0.12); color: #92400E; font-weight: 700; padding: 2px 5px; border-radius: 4px;"
                badge_html = f'<span class="badge bg-warning text-dark ms-1 fw-bold" style="font-size: 0.72rem; vertical-align: middle;"><i class="bi bi-exclamation-triangle-fill me-1"></i>CAUTION: {title_esc}</span>'

            replacement = (
                f'<span class="risk-underlined-factor risk-{m["severity"].lower()}" '
                f'id="{risk_id}" '
                f'data-risk-title="{title_esc}" '
                f'data-risk-severity="{sev_esc}" '
                f'data-risk-desc="{expl_esc}" '
                f'data-sentence="{sent_num}" '
                f'style="{underline_style}" '
                f'tabindex="0" '
                f'role="button" '
                f'data-bs-toggle="tooltip" '
                f'title="⚠️ {title_esc} ({sev_esc} Risk): {expl_esc}">'
                f'<span class="risk-highlight-text">{phrase_esc}</span>'
                f'{badge_html}'
                f'</span>'
            )

            result = result[:start] + replacement + result[end:]

        return result
