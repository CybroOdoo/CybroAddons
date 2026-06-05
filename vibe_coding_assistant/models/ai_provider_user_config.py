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

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from ..services.provider_base import (
    get_provider,
    AIProviderError,
    AIQuotaError,
    AIAuthError,
    AINotFoundError,
    AINetworkError,
)

_logger = logging.getLogger(__name__)


class AIProviderUserConfig(models.Model):
    _name = "ai.provider.user.config"
    _description = "AI Provider User Configuration"
    _order = "is_active desc, provider_id"

    user_id = fields.Many2one(
        "res.users",
        string="User",
        required=True,
        default=lambda self: self.env.user,
        ondelete="cascade",
    )
    provider_id = fields.Many2one(
        "ai.provider",
        string="Provider",
        required=True,
        ondelete="restrict",
    )
    api_key = fields.Char(
        string="API Key",
        required=True,
        help="Your personal API key for this provider. Stored as plain text.",
    )
    selected_model = fields.Char(
        string="Model",
        required=True,
        help="Model ID to use when generating modules. "
             "Must be one of the provider's available models.",
    )
    is_active = fields.Boolean(
        string="Active",
        default=False,
        help="Only one config can be active at a time. "
             "Activating this one will deactivate the others.",
    )
    # ── Connection test status ────────────────────────────────────────────
    last_test_state = fields.Selection(
        [
            ("untested", "Not Tested"),
            ("success",  "Connection OK"),
            ("failed",   "Connection Failed"),
        ],
        string="Connection Status",
        default="untested",
        readonly=True,
        copy=False,
    )
    last_test_message = fields.Char(
        string="Last Test Result",
        readonly=True,
        copy=False,
    )
    last_test_date = fields.Datetime(
        string="Last Tested",
        readonly=True,
        copy=False,
    )
    # ── Display helpers ───────────────────────────────────────────────────
    name = fields.Char(
        string="Label",
        compute="_compute_name",
        store=False,
    )
    available_models_hint = fields.Text(
        string="Available Models",
        related="provider_id.available_models",
    )

    # ── Aggregate token usage across this user/provider pair ──────────────
    tokens_used_total = fields.Integer(
        string="Total Tokens Used",
        compute="_compute_tokens_used_total",
        help="Sum of input + output tokens for every conversation that used this config.",
    )
    tokens_used_input = fields.Integer(
        string="Input Tokens",
        compute="_compute_tokens_used_total",
    )
    tokens_used_output = fields.Integer(
        string="Output Tokens",
        compute="_compute_tokens_used_total",
    )
    tokens_conversation_count = fields.Integer(
        string="Conversations",
        compute="_compute_tokens_used_total",
        help="Number of conversations that have run against this config.",
    )

    def _compute_tokens_used_total(self):
        Conv = self.env["vibe.conversation"]
        for rec in self:
            convs = Conv.search([("provider_config_id", "=", rec.id)])
            rec.tokens_used_input = sum(convs.mapped("tokens_input_total"))
            rec.tokens_used_output = sum(convs.mapped("tokens_output_total"))
            rec.tokens_used_total = sum(convs.mapped("tokens_total"))
            rec.tokens_conversation_count = len(convs)

    _sql_constraints = [
        (
            "user_provider_unique",
            "unique(user_id, provider_id)",
            "You already have a configuration for this provider.",
        ),
    ]

    # ── Computed / onchange ───────────────────────────────────────────────

    @api.depends("provider_id", "selected_model")
    def _compute_name(self):
        for rec in self:
            if rec.provider_id and rec.selected_model:
                rec.name = "%s (%s)" % (rec.provider_id.name, rec.selected_model)
            elif rec.provider_id:
                rec.name = rec.provider_id.name
            else:
                rec.name = _("Config")

    @api.onchange("provider_id")
    def _onchange_provider_id(self):
        """Pre-fill selected_model with the provider's default."""
        if self.provider_id and self.provider_id.default_model:
            self.selected_model = self.provider_id.default_model

    @api.onchange("api_key", "selected_model", "provider_id")
    def _onchange_invalidate_test(self):
        """If credentials change, the previous test result no longer applies."""
        for rec in self:
            rec.last_test_state = "untested"
            rec.last_test_message = False
            rec.last_test_date = False

    # ── Write override: auto-deactivate siblings ──────────────────────────

    def write(self, vals):
        """When a config is activated, deactivate the user's other configs."""
        if vals.get("is_active"):
            for rec in self:
                siblings = self.search([
                    ("user_id", "=", rec.user_id.id),
                    ("id", "!=", rec.id),
                    ("is_active", "=", True),
                ])
                if siblings:
                    siblings.sudo().write({"is_active": False})
        return super().write(vals)

    # ── Form button actions ───────────────────────────────────────────────

    def action_test_connection(self):
        """Verify the API key + model with a lightweight provider call.

        Uses provider.ping() rather than full generate() — the Gemini ping is
        countTokens (separate quota from generateContent), OpenAI's is /models,
        and Claude's is a max_tokens=10 message. This keeps the test from
        eating into your free-tier generation quota.

        Stores the result on the record so the form can show it inline, and
        pops a transient notification with a friendly message.
        """
        self.ensure_one()

        if not self.api_key or not self.api_key.strip():
            raise UserError(_("Please save an API key first, then test the connection."))
        if not self.selected_model:
            raise UserError(_("Please choose a model first."))

        try:
            provider = get_provider(
                self.provider_id.code,
                self.api_key,
                self.selected_model,
                self.provider_id.api_base_url,
            )
            reply = provider.ping()

        except AIQuotaError as e:
            return self._record_failure(
                short=_("Quota or rate limit exceeded"),
                detail=_(
                    "The provider rejected the request because the free-tier "
                    "rate limit or daily quota is exhausted. Wait a minute and "
                    "retry, or switch to a lower-traffic model "
                    "(e.g. gemini-1.5-flash has the most generous free quota)."
                ),
                raw=str(e),
            )
        except AIAuthError as e:
            return self._record_failure(
                short=_("Invalid or unauthorised API key"),
                detail=_(
                    "The provider rejected your credentials. Double-check that "
                    "you copied the full key, and that it hasn't been revoked or "
                    "restricted (referrer / IP restrictions in Google AI Studio)."
                ),
                raw=str(e),
            )
        except AINotFoundError as e:
            return self._record_failure(
                short=_("Model not found"),
                detail=_(
                    "The selected model name is not recognised by the provider, "
                    "or is not available in your region. Try a different model "
                    "from the 'Available Models' list."
                ),
                raw=str(e),
            )
        except AINetworkError as e:
            return self._record_failure(
                short=_("Network error"),
                detail=_(
                    "Could not reach the provider. Check your Odoo server's "
                    "internet connection, proxy settings, and firewall rules."
                ),
                raw=str(e),
            )
        except AIProviderError as e:
            return self._record_failure(
                short=_("Connection failed"),
                detail=False,
                raw=str(e),
            )

        # Success
        preview = (reply or "").strip()[:120]
        self.write({
            "last_test_state":   "success",
            "last_test_message": _("Reply: %s") % preview,
            "last_test_date":    fields.Datetime.now(),
        })
        return self._notification(
            title=_("Connection OK"),
            message=_("Provider responded successfully. You can activate this config now."),
            ntype="success",
        )

    def _record_failure(self, short, detail, raw):
        """Persist a failure result and return a notification action.

        :param short:  one-line summary shown in the status bar and notification title
        :param detail: longer human guidance; shown in the banner (False to skip)
        :param raw:    raw provider error string for diagnostics (logged + stored)
        """
        self.ensure_one()
        _logger.warning(
            "Connection test failed [%s]: %s",
            self.provider_id.code, short,
        )
        # Store the human-friendly short message; raw goes in the message field
        # truncated for diagnostics but not blown up into the UI.
        msg = short
        if detail:
            msg = "%s — %s" % (short, detail)
        self.write({
            "last_test_state":   "failed",
            "last_test_message": msg[:500],
            "last_test_date":    fields.Datetime.now(),
        })
        return self._notification(
            title=short,
            message=detail or raw[:200],
            ntype="danger",
        )

    def action_activate(self):
        """Mark this config as the user's active one.

        Sibling deactivation is handled by write() override.
        """
        self.ensure_one()
        if self.is_active:
            return self._notification(
                title=_("Already Active"),
                message=_("This configuration is already active."),
                ntype="info",
            )
        self.write({"is_active": True})
        return self._notification(
            title=_("Activated"),
            message=_("%s is now your active provider.") % self.name,
            ntype="success",
        )

    def action_deactivate(self):
        """Deactivate this config (the user will have no active provider)."""
        self.ensure_one()
        self.write({"is_active": False})
        return self._notification(
            title=_("Deactivated"),
            message=_("Configuration deactivated."),
            ntype="info",
        )

    # ── Helpers ───────────────────────────────────────────────────────────

    def _notification(self, title, message, ntype="info"):
        """Build a transient client notification action for form buttons."""
        return {
            "type":   "ir.actions.client",
            "tag":    "display_notification",
            "params": {
                "title":   title,
                "message": message,
                "type":    ntype,   # success / warning / danger / info
                "sticky":  False,
            },
        }

    # ── Model-level API called from vibe.conversation and OWL frontend ────

    @api.model
    def get_active_config_for_user(self, user_id=None):
        """Return the single active config for the given (or current) user."""
        uid = user_id or self.env.uid
        return self.search(
            [("user_id", "=", uid), ("is_active", "=", True)],
            limit=1,
        )

    @api.model
    def get_active_provider_info(self):
        """Return minimal provider info for the UI provider badge."""
        config = self.search(
            [("user_id", "=", self.env.uid), ("is_active", "=", True)],
            limit=1,
        )
        if not config:
            return False
        return {
            "provider_name": config.provider_id.name,
            "provider_code": config.provider_id.code,
            "model":         config.selected_model,
        }
