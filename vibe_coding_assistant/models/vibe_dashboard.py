# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3)
#    (https://www.gnu.org/licenses/lgpl-3.0-standalone.html).
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
################################################################################

"""Admin analytics dashboard for the Vibe Coding Assistant.

A TransientModel that aggregates stats across all conversations, modules,
and providers. The dashboard is opened from the menu and computes its
fields fresh on every load — no caching, no background jobs.

Why TransientModel: we don't need to persist these values, and we want
admins to always see live data. Odoo cleans up transient records
periodically so there's no maintenance burden.

The "no real-time auto-refresh" call is deliberate — the dashboard
recomputes when the admin opens it. That's the right cost/value tradeoff
for usage data that doesn't need to be live-streamed.
"""

import datetime
import html
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


def _escape(text):
    """Escape user-supplied text for safe HTML interpolation.

    User and provider names come from the DB but might still contain
    characters that need escaping for HTML output. sanitize=False on the
    HTML fields means Odoo does NOT sanitise — so we do it ourselves on
    every string-interpolated value.
    """
    return html.escape(str(text or ""), quote=True)



class VibeDashboard(models.TransientModel):
    _name = "vibe.dashboard"
    _description = "Vibe Coding Assistant Dashboard"

    # ── Display name override ────────────────────────────────────────────
    # Without this the breadcrumb falls back to "vibe.dashboard,<id>" since
    # the model has no `name` field and no `_rec_name`. Hard-coding the
    # display via a computed name field gives every transient instance a
    # consistent friendly title in breadcrumbs.

    name = fields.Char(
        string="Title",
        compute="_compute_name",
    )

    def _compute_name(self):
        for rec in self:
            rec.name = "Dashboard"

    # ── Headline KPIs ─────────────────────────────────────────────────────

    total_conversations = fields.Integer(
        string="Conversations",
        compute="_compute_stats",
    )
    total_modules = fields.Integer(
        string="Modules Generated",
        compute="_compute_stats",
    )
    total_tokens = fields.Integer(
        string="Total Tokens Used",
        compute="_compute_stats",
        help="Sum of input + output tokens across all conversations.",
    )
    total_users = fields.Integer(
        string="Active Users",
        compute="_compute_stats",
        help="Number of distinct users who have at least one conversation.",
    )

    # ── Quality metrics ───────────────────────────────────────────────────

    valid_modules = fields.Integer(
        string="Valid Modules",
        compute="_compute_stats",
    )
    invalid_modules = fields.Integer(
        string="Invalid Modules",
        compute="_compute_stats",
    )
    pending_modules = fields.Integer(
        string="Pending Validation",
        compute="_compute_stats",
    )
    success_rate = fields.Float(
        string="Success Rate",
        compute="_compute_stats",
        help="Valid / (Valid + Invalid) as a fraction. Excludes pending and "
             "conversations that produced no module (errors, quota limits). "
             "Rendered as a percentage in the view.",
    )

    # ── Token splits ──────────────────────────────────────────────────────

    total_input_tokens = fields.Integer(
        string="Input Tokens",
        compute="_compute_stats",
    )
    total_output_tokens = fields.Integer(
        string="Output Tokens",
        compute="_compute_stats",
    )

    # ── Downloads ─────────────────────────────────────────────────────────

    total_downloads = fields.Integer(
        string="Module Downloads",
        compute="_compute_stats",
    )

    # ── Efficiency metrics ────────────────────────────────────────────────

    avg_tokens_per_module = fields.Integer(
        string="Avg Tokens / Module",
        compute="_compute_stats",
        help="Total tokens ÷ modules generated. Lower is better — signals "
             "that prompts are precise and the AI isn't burning tokens "
             "wandering. Useful for spotting prompt-template quality issues.",
    )
    avg_messages_per_conversation = fields.Float(
        string="Avg Messages / Chat",
        compute="_compute_stats",
        help="Average messages per conversation. Higher means more "
             "back-and-forth (refinement); lower means one-shot generations.",
    )

    # ── Recent activity ───────────────────────────────────────────────────

    modules_last_24h = fields.Integer(
        string="Last 24h",
        compute="_compute_stats",
    )
    modules_last_7d = fields.Integer(
        string="Last 7 days",
        compute="_compute_stats",
    )
    modules_last_30d = fields.Integer(
        string="Last 30 days",
        compute="_compute_stats",
    )

    # ── Rich-content sections (HTML-rendered) ─────────────────────────────
    # These are built server-side into safe HTML and rendered via widget="html"
    # in the form. Cheaper than writing a custom OWL component for each
    # section, and admins rarely need interactivity in these views.

    provider_breakdown_html = fields.Html(
        string="Provider Breakdown",
        compute="_compute_stats",
        sanitize=False,
    )
    top_users_html = fields.Html(
        string="Top Users",
        compute="_compute_stats",
        sanitize=False,
    )
    activity_sparkline_html = fields.Html(
        string="Activity (Last 14 Days)",
        compute="_compute_stats",
        sanitize=False,
    )

    # ── Compute ───────────────────────────────────────────────────────────

    def _compute_stats(self):
        """Pull aggregate stats from related models.

        Uses sudo() so the admin sees a complete picture regardless of any
        per-user record rules — the dashboard menu is admin-only at the
        view level (groups="base.group_system" on the action).
        """
        Conv = self.env["vibe.conversation"].sudo()
        Mod  = self.env["vibe.generated.module"].sudo()
        Msg  = self.env["vibe.message"].sudo()

        all_convs = Conv.search([])
        all_mods  = Mod.search([])

        for rec in self:
            rec.total_conversations = len(all_convs)
            rec.total_modules       = len(all_mods)
            rec.total_input_tokens  = sum(all_convs.mapped("tokens_input_total"))
            rec.total_output_tokens = sum(all_convs.mapped("tokens_output_total"))
            rec.total_tokens        = rec.total_input_tokens + rec.total_output_tokens
            rec.total_users         = len(set(all_convs.mapped("user_id.id")))
            rec.total_downloads     = sum(all_mods.mapped("download_count"))

            valid   = all_mods.filtered(lambda m: m.validation_state == "valid")
            invalid = all_mods.filtered(lambda m: m.validation_state == "invalid")
            pending = all_mods.filtered(lambda m: m.validation_state == "pending")
            rec.valid_modules   = len(valid)
            rec.invalid_modules = len(invalid)
            rec.pending_modules = len(pending)

            total_judged = len(valid) + len(invalid)
            # Store as a fraction 0.0–1.0; the view uses widget="percentage"
            # which multiplies by 100 for display, so storing 30 here would
            # render as 3000%.
            rec.success_rate = (
                (len(valid) / total_judged) if total_judged else 0.0
            )

            # Efficiency
            rec.avg_tokens_per_module = (
                rec.total_tokens // len(all_mods) if all_mods else 0
            )
            total_msgs = Msg.search_count([])
            rec.avg_messages_per_conversation = (
                round(total_msgs / len(all_convs), 1) if all_convs else 0.0
            )

            # Recent activity windows
            now = fields.Datetime.now()
            since_24h = now - datetime.timedelta(hours=24)
            since_7d  = now - datetime.timedelta(days=7)
            since_30d = now - datetime.timedelta(days=30)
            rec.modules_last_24h = Mod.search_count([("create_date", ">=", since_24h)])
            rec.modules_last_7d  = Mod.search_count([("create_date", ">=", since_7d)])
            rec.modules_last_30d = Mod.search_count([("create_date", ">=", since_30d)])

            # Rich HTML sections
            rec.provider_breakdown_html = rec._build_provider_breakdown(all_convs)
            rec.top_users_html          = rec._build_top_users(all_convs, all_mods)
            rec.activity_sparkline_html = rec._build_activity_sparkline(all_mods)

    # ── HTML section builders ─────────────────────────────────────────────

    def _build_provider_breakdown(self, all_convs):
        """Horizontal stacked bar showing token-share per provider."""
        # Group token totals by provider name
        by_provider = {}  # name -> tokens
        for conv in all_convs:
            cfg = conv.provider_config_id
            if not cfg or not cfg.provider_id:
                continue
            pname = cfg.provider_id.name
            by_provider[pname] = by_provider.get(pname, 0) + conv.tokens_total

        total = sum(by_provider.values())
        if not total:
            return (
                '<div class="o_vibe_dash_empty_section">'
                'No provider usage yet — generate a module to see the breakdown.'
                '</div>'
            )

        # Color palette per known provider; falls back to gray for unknowns
        colors = {
            "Google Gemini":  "#4285f4",
            "Anthropic Claude": "#d97a2c",
            "OpenAI":         "#10a37f",
        }

        sorted_providers = sorted(by_provider.items(), key=lambda kv: -kv[1])

        # Stacked bar — one segment per provider, width proportional
        segments = []
        legend_rows = []
        for name, tokens in sorted_providers:
            pct = (tokens / total) * 100
            color = colors.get(name, "#6c757d")
            segments.append(
                '<div class="o_vibe_dash_bar_seg" '
                'style="width: %.2f%%; background: %s;" title="%s: %s tokens (%.1f%%)"></div>'
                % (pct, color, _escape(name), f"{tokens:,}", pct)
            )
            legend_rows.append(
                '<div class="o_vibe_dash_legend_row">'
                '<span class="o_vibe_dash_legend_dot" style="background: %s;"></span>'
                '<span class="o_vibe_dash_legend_name">%s</span>'
                '<span class="o_vibe_dash_legend_value">%s tokens</span>'
                '<span class="o_vibe_dash_legend_pct">%.1f%%</span>'
                '</div>'
                % (color, _escape(name), f"{tokens:,}", pct)
            )

        return (
            '<div class="o_vibe_dash_bar">' + "".join(segments) + '</div>'
            '<div class="o_vibe_dash_legend">' + "".join(legend_rows) + '</div>'
        )

    def _build_top_users(self, all_convs, all_mods):
        """Leaderboard table of the top 5 users by total tokens consumed."""
        # Aggregate per user
        per_user = {}  # uid -> {name, convs, mods, tokens}
        for conv in all_convs:
            uid = conv.user_id.id
            if not uid:
                continue
            entry = per_user.setdefault(uid, {
                "name":   conv.user_id.name or "User #%d" % uid,
                "convs":  0,
                "mods":   0,
                "tokens": 0,
            })
            entry["convs"]  += 1
            entry["tokens"] += conv.tokens_total

        for mod in all_mods:
            uid = mod.conversation_id.user_id.id if mod.conversation_id else None
            if uid in per_user:
                per_user[uid]["mods"] += 1

        # Sort by tokens descending
        ranked = sorted(per_user.values(), key=lambda u: -u["tokens"])[:5]

        if not ranked:
            return (
                '<div class="o_vibe_dash_empty_section">'
                'No user activity yet.'
                '</div>'
            )

        rows = []
        max_tokens = max(u["tokens"] for u in ranked) or 1
        for i, u in enumerate(ranked, start=1):
            bar_pct = (u["tokens"] / max_tokens) * 100
            rows.append(
                '<tr>'
                '<td class="o_vibe_dash_rank">#%d</td>'
                '<td class="o_vibe_dash_username">%s</td>'
                '<td class="o_vibe_dash_num">%d</td>'
                '<td class="o_vibe_dash_num">%d</td>'
                '<td class="o_vibe_dash_token_cell">'
                  '<div class="o_vibe_dash_token_bar_wrap">'
                    '<div class="o_vibe_dash_token_bar" style="width: %.1f%%;"></div>'
                  '</div>'
                  '<span class="o_vibe_dash_token_label">%s</span>'
                '</td>'
                '</tr>'
                % (i, _escape(u["name"]), u["convs"], u["mods"], bar_pct, f"{u['tokens']:,}")
            )

        return (
            '<table class="o_vibe_dash_top_users">'
            '<thead><tr>'
            '<th></th>'
            '<th>User</th>'
            '<th class="text-end">Chats</th>'
            '<th class="text-end">Modules</th>'
            '<th>Tokens</th>'
            '</tr></thead>'
            '<tbody>' + "".join(rows) + '</tbody>'
            '</table>'
        )

    def _build_activity_sparkline(self, all_mods):
        """SVG sparkline of modules generated per day over the last 14 days."""
        days = 14
        today = fields.Date.today()
        # Build the date bucket — modules per day
        buckets = {today - datetime.timedelta(days=i): 0 for i in range(days)}
        for mod in all_mods:
            if not mod.create_date:
                continue
            d = fields.Date.to_date(mod.create_date)
            if d in buckets:
                buckets[d] += 1

        # Order oldest → newest for left-to-right reading
        ordered = sorted(buckets.items())
        counts = [c for _, c in ordered]
        max_c = max(counts) if counts else 0

        if max_c == 0:
            return (
                '<div class="o_vibe_dash_empty_section">'
                'No module generation activity in the last 14 days.'
                '</div>'
            )

        # SVG dimensions
        w, h, pad = 600, 100, 10
        bar_w = (w - 2 * pad) / days
        bars = []
        for i, c in enumerate(counts):
            bh = (c / max_c) * (h - 2 * pad) if max_c else 0
            x = pad + i * bar_w
            y = h - pad - bh
            d_str = ordered[i][0].isoformat()
            bars.append(
                '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
                'rx="2" ry="2" fill="#875a7b" opacity="%.2f">'
                '<title>%s: %d module%s</title>'
                '</rect>'
                % (x + 2, y, max(bar_w - 4, 1), bh,
                   0.4 + 0.6 * (c / max_c) if max_c else 0,
                   d_str, c, "s" if c != 1 else "")
            )

        return (
            '<svg viewBox="0 0 %d %d" preserveAspectRatio="none" '
            'class="o_vibe_dash_sparkline">'
            '%s'
            '</svg>'
            '<div class="o_vibe_dash_sparkline_labels">'
            '<span>%s</span><span>Today</span>'
            '</div>'
            % (w, h, "".join(bars), ordered[0][0].strftime("%b %d"))
        )

    # ── Action: open the dashboard ────────────────────────────────────────

    @api.model
    def action_open_dashboard(self):
        """Create a transient record and open it in form view."""
        rec = self.create({})
        return {
            "type":     "ir.actions.act_window",
            "name":     _("Vibe Coding Dashboard"),
            "res_model": "vibe.dashboard",
            "res_id":    rec.id,
            "view_mode": "form",
            "target":    "current",
        }

    # ── Drill-down actions (open the underlying records pre-filtered) ─────

    def action_view_all_conversations(self):
        return {
            "type":     "ir.actions.act_window",
            "name":     _("All Conversations"),
            "res_model": "vibe.conversation",
            "view_mode": "list,form",
            "context":   {"search_default_group_by_user": 1},
        }

    def action_view_all_modules(self):
        return {
            "type":     "ir.actions.act_window",
            "name":     _("All Generated Modules"),
            "res_model": "vibe.generated.module",
            "view_mode": "list,form",
        }

    def action_view_valid_modules(self):
        return {
            "type":     "ir.actions.act_window",
            "name":     _("Valid Modules"),
            "res_model": "vibe.generated.module",
            "view_mode": "list,form",
            "domain":    [("validation_state", "=", "valid")],
        }

    def action_view_invalid_modules(self):
        return {
            "type":     "ir.actions.act_window",
            "name":     _("Invalid Modules"),
            "res_model": "vibe.generated.module",
            "view_mode": "list,form",
            "domain":    [("validation_state", "=", "invalid")],
        }
