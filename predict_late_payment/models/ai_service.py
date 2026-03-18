# -- coding: utf-8 --
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json
import logging
import urllib.request
import urllib.error

from odoo import models, api, _

_logger = logging.getLogger(__name__)

# Gemini's OpenAI-compatible endpoint
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
DEFAULT_MODEL  = "gemini-2.5-flash"

SYSTEM_PROMPT = """\
You are an expert credit-risk analyst embedded in an Odoo ERP system.
Analyse the customer invoice and payment history and produce a structured JSON risk assessment.

Rules:
- Be objective and strictly data-driven.
- Recency matters most — recent behaviour is more predictive than historical averages.
- Score 0 = zero late-payment risk. Score 100 = near-certain late payment.
- followup_email must be professional, personalised, and immediately sendable as-is.
- ai_reasoning must be 3-5 sentences explaining the KEY risk drivers for this specific customer.
- You MUST respond with ONLY valid JSON — no preamble, no explanation, no markdown fences.

Required JSON schema (return exactly this structure):
{
  "score": <float 0-100>,
  "risk_level": <"low"|"medium"|"high"|"critical">,
  "delay_score": <float 0-30>,
  "overdue_score": <float 0-25>,
  "consistency_score": <float 0-15>,
  "recency_score": <float 0-15>,
  "volume_score": <float 0-10>,
  "trend_score": <float -5 to 5>,
  "suggested_credit_limit": <float>,
  "ai_reasoning": "<3-5 sentences on key risk drivers>",
  "followup_suggestion": "<plain text action steps for finance team>",
  "followup_email": "<complete ready-to-send professional email body>"
}"""


class PaymentRiskAIService(models.AbstractModel):
    """
    ai_service.py  —  Google Gemini AI backend
    ==========================================
    Uses Google Gemini 2.5 Flash via the OpenAI-compatible endpoint.

    Endpoint : https://generativelanguage.googleapis.com/v1beta/openai/chat/completions
    Auth     : Authorization: Bearer <GEMINI_API_KEY>
    Default  : gemini-2.5-flash  (free tier available, very capable)

    Get a free API key at: https://aistudio.google.com/apikey
    """
    _name        = 'payment.risk.ai.service'
    _description = 'Google Gemini AI Service for Payment Risk Scoring'

    @api.model
    def analyse_customer(self, partner, invoice_stats: dict) -> dict:
        """
        Analyse a customer's payment stats using Google Gemini.
        Falls back to statistical rules if the API key is missing or call fails.
        """
        api_key = self._get_param('predict_late_payment.gemini_api_key')
        if not api_key:
            _logger.warning(
                "Gemini API key not configured — using statistical fallback. "
                "Add key at: Settings → Payment Risk AI → Gemini API Key"
            )
            fb = self._fallback_score(invoice_stats)
            fb['ai_powered']   = False
            fb['ai_reasoning'] = (
                "Gemini API key not configured. "
                "Go to Settings → Payment Risk AI to add your free key from "
                "https://aistudio.google.com/apikey. "
                "Score computed using statistical rules."
            )
            return fb

        model  = self._get_param('predict_late_payment.gemini_model', DEFAULT_MODEL)
        prompt = self._build_prompt(partner, invoice_stats)
        try:
            raw    = self._call_gemini(api_key, model, prompt)
            _logger.debug("Gemini raw response for %s: %r", partner.name, raw[:500])
            result = self._parse_response(raw)
            result['ai_powered'] = True
            result['ai_backend'] = f"Google Gemini ({model})"
            return result
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            _logger.error("Gemini HTTP %s for partner %s: %s", e.code, partner.name, body)
            fb = self._fallback_score(invoice_stats)
            fb['ai_powered'] = False
            if e.code == 429:
                fb['ai_reasoning'] = (
                    "Gemini free-tier rate limit reached (20 requests/day for gemini-2.5-flash). "
                    "Switch to gemini-2.0-flash (1,500 free requests/day) in "
                    "Settings → Payment Risk AI → Choose Model, or wait until tomorrow. "
                    "Statistical fallback used."
                )
            elif e.code in (401, 403):
                fb['ai_reasoning'] = (
                    f"Gemini API authentication error ({e.code}). "
                    "Check your API key in Settings → Payment Risk AI. "
                    "Statistical fallback used."
                )
            elif e.code == 400:
                fb['ai_reasoning'] = (
                    "Gemini API error 400 — invalid request or API key. "
                    "Verify your key at aistudio.google.com. "
                    "Statistical fallback used."
                )
            else:
                fb['ai_reasoning'] = (
                    f"Gemini API error {e.code}. "
                    "Check your key at aistudio.google.com. "
                    "Statistical fallback used."
                )
            return fb
        except Exception as e:
            _logger.error(
                "Gemini error for partner %s: %s. Raw response was: %r",
                partner.name, e,
                locals().get('raw', 'N/A')[:1000],
            )
            fb = self._fallback_score(invoice_stats)
            fb['ai_powered']   = False
            fb['ai_reasoning'] = (
                f"Gemini AI unavailable ({type(e).__name__}). "
                "Statistical fallback used."
            )
            return fb

    def _call_gemini(self, api_key: str, model: str, prompt: str) -> str:
        """
        POST to Gemini's OpenAI-compatible chat completions endpoint.
        Docs: https://ai.google.dev/gemini-api/docs/openai
        """
        payload = json.dumps({
            "model":           model,
            "temperature":     0.1,
            "max_tokens":      4096,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
        }).encode("utf-8")
        req = urllib.request.Request(
            GEMINI_API_URL,
            data=payload,
            headers={
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))

        return body["choices"][0]["message"]["content"]

    def _build_prompt(self, partner, stats: dict) -> str:
        """
        Build the structured prompt sent to the Gemini model.

        This method converts the customer's payment statistics and invoice
        history into a formatted text prompt that the AI model can analyse
        to generate a risk assessment.
        """
        currency = self.env.company.currency_id.name or 'USD'
        industry = getattr(partner, 'industry_id', None)

        history_lines = "\n".join(
            f"  - {r['name']}: due {r['due_date']}, paid {r['paid_date']}, "
            f"delay {r['delay_days']:+d} days, amount {r['amount']:.2f} {currency}"
            for r in stats.get('paid_invoice_history', [])[-20:]
        ) or "  (none)"

        overdue_lines = "\n".join(
            f"  - {r['name']}: due {r['due_date']}, "
            f"outstanding {r['amount']:.2f} {currency}, "
            f"{r['days_overdue']} days overdue"
            for r in stats.get('overdue_invoices', [])
        ) or "  (none)"

        return f"""Analyse this Odoo customer and return a JSON risk assessment.

CUSTOMER PROFILE
================
Name         : {partner.name}
Industry     : {industry.name if industry else 'Unknown'}
Country      : {partner.country_id.name if partner.country_id else 'Unknown'}
Customer since: {stats.get('first_invoice_date', 'Unknown')}
Currency     : {currency}

PAYMENT STATISTICS (ALL TIME)
==============================
Total invoices       : {stats['total_invoices']}
Paid on time / late  : {stats['paid_on_time']} / {stats['paid_late']}
Average delay        : {stats['avg_delay_days']:.1f} days
Maximum delay ever   : {stats['max_delay_days']:.1f} days
Std dev of delays    : {stats['std_dev_delays']:.1f} days
Currently overdue    : {stats['currently_overdue']} invoice(s)
Total overdue amount : {stats['total_overdue_amount']:.2f} {currency}
Average invoice amt  : {stats['avg_invoice_amount']:.2f} {currency}

RECENT BEHAVIOUR (last 6 months)
==================================
Count / avg delay    : {stats['recent_total']} / {stats['recent_avg_delay']:.1f} days
Trend vs prior 6m    : {stats['trend_delta']:+.1f} days (positive = worsening)

PAID INVOICE HISTORY (newest first)
=====================================
{history_lines}

CURRENTLY OVERDUE INVOICES
===========================
{overdue_lines}

Return ONLY the JSON object. No explanation. No markdown.
Set suggested_credit_limit in {currency}."""

    def _parse_response(self, raw: str) -> dict:
        """
        Parse and normalize the JSON response returned by Gemini.
        Ensures the score and suggested credit limit fall within valid ranges
        and derives the risk level from the final score.
        """
        data = json.loads(raw.strip())
        data['score'] = max(0.0, min(100.0, float(data.get('score', 50))))
        data['suggested_credit_limit'] = max(0.0, float(data.get('suggested_credit_limit', 0)))
        s = data['score']
        if   s < 25: data['risk_level'] = 'low'
        elif s < 50: data['risk_level'] = 'medium'
        elif s < 75: data['risk_level'] = 'high'
        else:        data['risk_level'] = 'critical'
        return data

    def _get_param(self, key: str, default: str = '') -> str:
        """
        Retrieve a configuration parameter from Odoo system settings.
        Returns the provided default value if the parameter is not defined.
        """
        return (
            self.env['ir.config_parameter'].sudo()
            .get_param(key, default=default) or default
        )

    @api.model
    def test_connection(self) -> str:
        """
        Test connectivity with the Gemini API.
        Sends a simple request to verify that the configured API key and
        model are working correctly.
        """
        api_key = self._get_param('predict_late_payment.gemini_api_key')
        if not api_key:
            return "No API key configured. Get a free key at https://aistudio.google.com/apikey"

        model = self._get_param('predict_late_payment.gemini_model', DEFAULT_MODEL)
        try:
            raw = self._call_gemini(api_key, model, "Reply with exactly the word: CONNECTED")
            return f"OK — Gemini ({model}) responded: {raw.strip()[:80]}"
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            return f"HTTP {e.code}: {body[:200]}"
        except urllib.error.URLError as e:
            return f"Network error: {e.reason}"
        except Exception as e:
            return f"{type(e).__name__}: {e}"

    def _fallback_score(self, stats: dict) -> dict:
        """
        Compute a statistical risk score when the AI service is unavailable.

        Uses payment delay metrics, overdue ratios, payment consistency,
        recent behaviour, and trend analysis to estimate the customer's
        payment risk level.
        """
        avg_delay    = stats.get('avg_delay_days', 0)
        overdue_ratio= stats.get('overdue_ratio',  0)
        std_dev      = stats.get('std_dev_delays',  0)
        recent_avg   = stats.get('recent_avg_delay', avg_delay)
        open_count   = stats.get('currently_overdue', 0)
        trend        = stats.get('trend_delta', 0)
        avg_amount   = stats.get('avg_invoice_amount', 0)
        d = min(30.0, max(0.0,  (avg_delay    / 90) * 30))
        o = min(25.0,           (overdue_ratio / 100) * 25)
        c = min(15.0,           (std_dev       / 60) * 15) if std_dev else 7.5
        r = min(15.0, max(0.0,  (recent_avg    / 90) * 15))
        v = min(10.0,           (open_count    / 10) * 10)
        t = min(5.0,  max(-5.0, (trend         / 30) * 5))
        score = max(0.0, min(100.0, d + o + c + r + v + t))
        if   score < 25: rl = 'low'
        elif score < 50: rl = 'medium'
        elif score < 75: rl = 'high'
        else:            rl = 'critical'
        msgs = {
            'critical': 'CRITICAL: Immediate contact required. Pause credit. Request upfront payment.',
            'high':     'HIGH RISK: Send formal reminder. Reduce credit limit. Schedule a call.',
            'medium':   'MEDIUM RISK: Send a courtesy reminder 5 days before due date.',
            'low':      'LOW RISK: Standard follow-up process applies.',
        }
        return {
            'score': round(score, 2), 'risk_level': rl,
            'delay_score':       round(d, 2),
            'overdue_score':     round(o, 2),
            'consistency_score': round(c, 2),
            'recency_score':     round(r, 2),
            'volume_score':      round(v, 2),
            'trend_score':       round(t, 2),
            'suggested_credit_limit': round(
                avg_amount * 3 * max(0.2, 1 - score / 100), 2),
            'ai_reasoning':       'Statistical fallback (AI service not configured).',
            'followup_suggestion': msgs[rl],
            'followup_email':      '',
        }
