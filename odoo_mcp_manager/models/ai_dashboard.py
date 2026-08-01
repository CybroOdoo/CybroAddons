# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import logging
from datetime import timedelta
from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class AiDashboard(models.Model):
    """Singleton dashboard record that surfaces live MCP Gateway status counters."""

    _name = 'ai.dashboard'
    _description = 'MCP Gateway Dashboard'

    name = fields.Char(default='MCP Gateway Dashboard')
    mcp_status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')],
        default='active',
    )

    # ── Computed counters ────────────────────────────────────────────────────

    provider_count = fields.Integer(compute='_compute_counts')
    tool_count = fields.Integer(compute='_compute_counts')
    session_count = fields.Integer(compute='_compute_counts')
    active_provider_count = fields.Integer(compute='_compute_counts')
    enabled_tool_count = fields.Integer(compute='_compute_counts')
    custom_tool_count = fields.Integer(compute='_compute_counts')
    key_count = fields.Integer(compute='_compute_counts')
    pending_consent_count = fields.Integer(compute='_compute_counts')
    log_count_today = fields.Integer(compute='_compute_counts')

    def _compute_counts(self) -> None:
        """Populate all dashboard counters."""
        for rec in self:
            rec.provider_count = self.env['ai.provider'].search_count([])
            rec.active_provider_count = self.env['ai.provider'].search_count(
                [('active', '=', True)]
            )
            rec.tool_count = self.env['ai.tool'].search_count([])
            rec.enabled_tool_count = self.env['ai.tool'].search_count(
                [('active', '=', True)]
            )
            rec.custom_tool_count = self.env['ai.tool'].search_count(
                [('active', '=', True), ('implementation', '=', 'builtin')]
            )
            rec.session_count = self.env['ai.session'].search_count(
                [('state', '=', 'initialized')]
            )
            # Count providers that have an API key configured
            rec.key_count = self.env['ai.provider'].search_count(
                [('api_key', '!=', False), ('api_key', '!=', ''), ('active', '=', True)]
            )
            rec.pending_consent_count = self.env['ai.consent'].search_count(
                [('state', '=', 'pending')]
            )
            today_start = fields.Datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            rec.log_count_today = self.env['ai.tool.log'].search_count(
                [('timestamp', '>=', today_start)]
            )

    # ── JSON-RPC Dashboard Data Endpoint ────────────────────────────────────

    @api.model
    def get_dashboard_data(self) -> dict:
        """
        Return a comprehensive dashboard data dict for the OWL component.
        Called via JSON-RPC every N seconds for real-time updates.
        """
        today_start = fields.Datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        yesterday_start = today_start - timedelta(days=1)

        # ── Session stats ─────────────────────────────────────────────────
        # Use raw SQL to safely handle the case where client_name column does
        # not yet exist in the database (pre-upgrade state).
        sessions_list = []
        active_sessions = 0
        try:
            # Check which columns exist
            self.env.cr.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'ai_session' "
                "AND column_name IN ('client_name', 'client_version')"
            )
            existing_cols = {row[0] for row in self.env.cr.fetchall()}
            has_client = 'client_name' in existing_cols

            if has_client:
                self.env.cr.execute("""
                    SELECT s.id, s.mcp_source, s.client_name, s.client_version,
                           u.name AS user_name
                    FROM ai_session s
                    LEFT JOIN res_users ru ON ru.id = s.user_id
                    LEFT JOIN res_partner u ON u.id = ru.partner_id
                    WHERE s.state = 'initialized' AND s.active = true
                    ORDER BY s.write_date DESC
                """)
            else:
                self.env.cr.execute("""
                    SELECT s.id, s.mcp_source, NULL AS client_name,
                           NULL AS client_version, u.name AS user_name
                    FROM ai_session s
                    LEFT JOIN res_users ru ON ru.id = s.user_id
                    LEFT JOIN res_partner u ON u.id = ru.partner_id
                    WHERE s.state = 'initialized' AND s.active = true
                    ORDER BY s.write_date DESC
                """)

            rows = self.env.cr.fetchall()
            active_sessions = len(rows)
            sessions_list = [{
                'client_name': row[2] or 'MCP Client',
                'client_version': row[3] or '',
                'transport': row[1] or 'mcp',
                'user': row[4] or 'Unknown',
            } for row in rows]

        except Exception as e:
            _logger.warning('Dashboard: session stats query failed — %s', e)
            active_sessions = self.env['ai.session'].search_count([
                ('state', '=', 'initialized'), ('active', '=', True)
            ])
            sessions_list = []

        # ── Provider stats ───────────────────────────────────────────────
        all_providers = self.env['ai.provider'].search([])
        active_providers = all_providers.filtered(lambda p: p.active)
        provider_list = []
        for p in active_providers[:6]:
            provider_list.append({
                'name': p.name,
                'service': p.service,
                'status': p.connection_status or 'unchecked',
                'last_checked': p.last_checked.strftime('%H:%M') if p.last_checked else None,
                'error': p.connection_error or '',
            })

        # ── Tool stats ───────────────────────────────────────────────────
        all_tools = self.env['ai.tool'].search([])
        enabled_tools = all_tools.filtered(lambda t: t.active)
        custom_tools = all_tools.filtered(
            lambda t: t.active and t.implementation == 'builtin'
        )

        # ── Log stats ────────────────────────────────────────────────────
        logs_today = self.env['ai.tool.log'].search_count(
            [('timestamp', '>=', today_start)]
        )
        logs_yesterday = self.env['ai.tool.log'].search_count([
            ('timestamp', '>=', yesterday_start),
            ('timestamp', '<', today_start),
        ])
        success_today = self.env['ai.tool.log'].search_count([
            ('timestamp', '>=', today_start),
            ('status', '=', 'success'),
        ])
        success_yesterday = self.env['ai.tool.log'].search_count([
            ('timestamp', '>=', yesterday_start),
            ('timestamp', '<', today_start),
            ('status', '=', 'success'),
        ])

        success_rate = round(
            (success_today / logs_today * 100) if logs_today else 0, 1
        )
        success_rate_yesterday = round(
            (success_yesterday / logs_yesterday * 100) if logs_yesterday else 0, 1
        )

        # ── Avg response time ────────────────────────────────────────────
        today_logs = self.env['ai.tool.log'].search([
            ('timestamp', '>=', today_start),
            ('status', '=', 'success'),
            ('execution_time_ms', '>', 0),
        ], limit=200)
        yesterday_logs_q = self.env['ai.tool.log'].search([
            ('timestamp', '>=', yesterday_start),
            ('timestamp', '<', today_start),
            ('status', '=', 'success'),
            ('execution_time_ms', '>', 0),
        ], limit=200)

        avg_ms_today = (
            sum(l.execution_time_ms for l in today_logs) / len(today_logs)
            if today_logs else 0
        )
        avg_ms_yesterday = (
            sum(l.execution_time_ms for l in yesterday_logs_q) / len(yesterday_logs_q)
            if yesterday_logs_q else 0
        )
        avg_s = round(avg_ms_today / 1000, 2) if avg_ms_today else 0
        avg_s_yesterday = round(avg_ms_yesterday / 1000, 2) if avg_ms_yesterday else 0

        # ── Consent stats ────────────────────────────────────────────────
        pending_consents = self.env['ai.consent'].search_count(
            [('state', '=', 'pending')]
        )

        # ── Active Providers ──────────────────────────────────────────────────
        active_api_keys = self.env['ai.provider'].search_count([
            ('active', '=', True),
        ])

        # ── Active Bot Channels ───────────────────────────────────────────
        try:
            active_bot_channels = self.env['ai.bot.channel'].search_count(
                [('status', '=', 'active')]
            )
        except Exception:
            active_bot_channels = 0

        # ── Recent activity logs ─────────────────────────────────────────
        recent_logs = self.env['ai.tool.log'].search(
            [], order='timestamp desc', limit=50
        )
        activity = []
        for log in recent_logs:
            if log.timestamp:
                # Convert UTC → user's configured timezone before formatting
                local_dt = fields.Datetime.context_timestamp(log, log.timestamp)
                time_str = local_dt.strftime('%I:%M %p')
            else:
                time_str = ''
            # Resolve the actual client app that triggered this log entry
            source_label = self._resolve_source_label(log)
            activity.append({
                'time': time_str,
                'action': log.call_label or (log.tool_id.name if log.tool_id else 'Unknown'),
                'model': self._guess_model_from_params(log.input_params),
                'status': log.status or 'success',
                'agent': source_label,
            })

        # ── Uptime ───────────────────────────────────────────────────────
        last_log = self.env['ai.tool.log'].search(
            [], order='timestamp desc', limit=1
        )
        last_request_label = 'Never'
        if last_log:
            # Use UTC-aware comparison: fields.Datetime.now() returns UTC naive datetime
            delta = fields.Datetime.now() - last_log.timestamp
            mins = int(delta.total_seconds() // 60)
            if mins < 1:
                last_request_label = 'Just now'
            elif mins < 60:
                last_request_label = f'{mins} min ago'
            else:
                hours = mins // 60
                last_request_label = f'{hours}h ago'

        # ── Key count: providers with a configured API key ────────────────
        key_count = self.env['ai.provider'].search_count(
            [('api_key', '!=', False), ('api_key', '!=', ''), ('active', '=', True)]
        )

        # ── Calls today ──────────────────────────────────────────────────
        calls_today = logs_today

        # Delta labels
        def _delta_label(today_val, yesterday_val, suffix=''):
            if yesterday_val == 0:
                return f'+{today_val}{suffix} vs yesterday' if today_val else 'No data yet'
            diff = today_val - yesterday_val
            pct = round((diff / yesterday_val) * 100, 1)
            sign = '+' if pct >= 0 else ''
            return f'{sign}{pct}% vs yesterday'

        return {
            'status': 'active',
            'last_request': last_request_label,
            'mcp_server': {
                'sessions': active_sessions,
                'sessions_list': sessions_list,
                'keys': key_count,
                'uptime': self._get_uptime_label(),
                'last_request': last_request_label,
            },
            'providers': {
                'active_count': len(active_providers),
                'list': provider_list,
            },
            'tools': {
                'total': len(all_tools),
                'enabled': len(enabled_tools),
                'custom': len(custom_tools),
                'calls_today': calls_today,
                'success_rate': success_rate,
            },
            'stats': {
                'active_api_keys': active_api_keys,
                'active_bot_channels': active_bot_channels,
                'avg_response_s': avg_s,
                'avg_response_delta': _delta_label_inverted(avg_s, avg_s_yesterday, 's'),
                'pending_consents': pending_consents,
                'consents_require_review': pending_consents > 0,
            },
            'operations': {
                'sessions': active_sessions,
                'logs_today': logs_today,
                'pending_consents': pending_consents,
            },
            'activity': activity,
        }

    def _get_uptime_label(self) -> str:
        """Return a human-readable uptime label based on first log record."""
        first_log = self.env['ai.tool.log'].search([], order='timestamp asc', limit=1)
        if not first_log:
            return '0d 0h'
        # Both fields.Datetime.now() and log.timestamp are UTC-naive — safe to subtract
        delta = fields.Datetime.now() - first_log.timestamp
        days = delta.days
        hours = int((delta.total_seconds() % 86400) // 3600)
        return f'{days}d {hours}h'

    def _guess_model_from_params(self, params_text: str) -> str:
        """Try to extract the Odoo model name from the input_params JSON text."""
        if not params_text:
            return 'General'
        try:
            import json
            params = json.loads(params_text)
            return params.get('model', params.get('res_model', 'General'))
        except Exception:
            return 'General'

    def _resolve_source_label(self, log) -> str:
        """
        Return a human-readable label for the client that triggered a tool log.

        Priority:
          1. Stored client_name on the log record (if present and set)
          2. Platform-specific sources (telegram, whatsapp, discord, web) → immediate label
          3. mcp source → look up session's client_name via safe raw SQL
          4. Fallback → 'MCP Client'
        """
        # 1. Use the persisted client_name on the log record if it exists
        try:
            self.env.cr.execute(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = 'ai_tool_log' AND column_name = 'client_name' LIMIT 1"
            )
            if self.env.cr.fetchone() and log.client_name:
                return log.client_name
        except Exception:
            pass

        source = log.source or 'mcp'
        user_id = log.user_id.id if log.user_id else False

        # Unambiguous platform sources — no DB lookup needed
        _PLATFORM_LABELS = {
            'telegram': 'Telegram Bot',
            'whatsapp': 'WhatsApp Bot',
            'discord':  'Discord Bot',
            'web':      'Web Chat',
            'bot':      'Bot Gateway',
            'rpc':      'Direct RPC',
        }
        if source in _PLATFORM_LABELS:
            return _PLATFORM_LABELS[source]

        # For 'mcp' source: resolve real client app name via safe raw SQL
        if source == 'mcp' and user_id:
            try:
                self.env.cr.execute(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_name = 'ai_session' AND column_name = 'client_name' LIMIT 1"
                )
                if self.env.cr.fetchone():
                    self.env.cr.execute("""
                        SELECT client_name, client_version FROM ai_session
                        WHERE user_id = %s AND mcp_source = 'mcp' AND active = true
                        ORDER BY write_date DESC LIMIT 1
                    """, (user_id,))
                    row = self.env.cr.fetchone()
                    if row and row[0] and row[0] not in ('MCP Client', 'Unknown'):
                        ver = f' {row[1]}' if row[1] else ''
                        return f'{row[0]}{ver}'
            except Exception:
                pass

        return 'MCP Client'

    @api.model
    def action_open_dashboard(self) -> dict:
        """Open (or create) the singleton dashboard record and return its window action."""
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({})
        return {
            'type': 'ir.actions.act_window',
            'name': _('MCP Gateway Dashboard'),
            'res_model': 'ai.dashboard',
            'res_id': dashboard.id,
            'view_mode': 'form',
            'target': 'main',
        }


def _delta_label_inverted(today_val, yesterday_val, suffix=''):
    """Like _delta_label but negative change is shown as positive (for response time)."""
    if yesterday_val == 0:
        return ''
    diff = today_val - yesterday_val
    pct = round((diff / yesterday_val) * 100, 1)
    sign = '+' if pct >= 0 else ''
    return f'{sign}{pct}{suffix} vs yesterday'
