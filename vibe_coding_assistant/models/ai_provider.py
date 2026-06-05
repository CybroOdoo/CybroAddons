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

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from ..services.provider_base import (
    get_provider,
    AIProviderError,
    AIAuthError,
    AINotFoundError,
    AINetworkError,
)


class AIProvider(models.Model):
    _name = "ai.provider"
    _description = "AI Provider"
    _order = "name"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(
        string="Code",
        required=True,
        help="Internal identifier used by the service layer: gemini / claude / openai",
    )
    default_model = fields.Char(
        string="Default Model",
        required=True,
        help="Pre-filled when a user creates a new config for this provider.",
    )
    available_models = fields.Text(
        string="Available Models",
        required=True,
        help="One model ID per line. Shown as a hint in the user config form.",
    )
    api_base_url = fields.Char(string="API Base URL", required=True)
    is_default = fields.Boolean(
        string="Default Provider",
        default=False,
        help="The default provider pre-selected for new users.",
    )
    active = fields.Boolean(default=True)

    # ── Stats for the smart button ─────────────────────────────────────────
    conversation_count = fields.Integer(
        string="Conversations",
        compute="_compute_conversation_count",
    )
    tokens_used_total = fields.Integer(
        string="Total Tokens Used",
        compute="_compute_conversation_count",
        help="Sum of all input + output tokens across every conversation that "
             "used any user-config of this provider.",
    )

    _sql_constraints = [
        ("code_unique", "unique(code)", "Provider code must be unique."),
    ]

    def _compute_conversation_count(self):
        """Count conversations and aggregate token usage for each provider.

        Reads via sudo() so the admin sees the full picture regardless of
        per-user record rules on vibe.conversation. The smart button view
        also runs in admin context.
        """
        Conv = self.env["vibe.conversation"].sudo()
        for rec in self:
            convs = Conv.search([("provider_config_id.provider_id", "=", rec.id)])
            rec.conversation_count = len(convs)
            rec.tokens_used_total = sum(convs.mapped("tokens_total"))

    def action_view_conversations(self):
        """Smart-button action: open the dedicated history list of conversations
        that used any user-config of this provider.

        Uses the wide list view defined in views/ai_provider_views.xml which
        includes token totals and a "Group by User" search default.
        """
        self.ensure_one()
        list_view = self.env.ref(
            "vibe_coding_assistant.view_vibe_conversation_history_list",
            raise_if_not_found=False,
        )
        search_view = self.env.ref(
            "vibe_coding_assistant.view_vibe_conversation_history_search",
            raise_if_not_found=False,
        )
        action = {
            "type": "ir.actions.act_window",
            "name": _("Conversations — %s") % self.name,
            "res_model": "vibe.conversation",
            "view_mode": "list,form",
            "domain": [("provider_config_id.provider_id", "=", self.id)],
            "context": {
                "search_default_group_by_user": 1,
                "create": False,
            },
        }
        # Pin the specific list + search views so the smart button always
        # opens the history layout even when other list views exist.
        views = []
        if list_view:
            views.append((list_view.id, "list"))
        views.append((False, "form"))
        action["views"] = views
        if search_view:
            action["search_view_id"] = (search_view.id, search_view.name)
        return action

    def action_refresh_models(self):
        """Fetch the current model catalogue from the provider's /models
        endpoint and overwrite `available_models`.

        Uses the admin's own active config for this provider as the
        credential source. If the admin doesn't have one, fails with a
        clear UserError pointing them to create one.

        Preserves the existing default_model if it's still in the new list;
        otherwise picks the first model as the new default and warns about
        the change in the success notification.
        """
        self.ensure_one()

        # Find a config for this provider belonging to the current user
        # (we don't borrow other users' keys, even for admin work).
        config = self.env["ai.provider.user.config"].sudo().search([
            ("user_id", "=", self.env.uid),
            ("provider_id", "=", self.id),
        ], limit=1)
        if not config or not config.api_key:
            raise UserError(_(
                "To refresh the model list, you need a personal API key for "
                "%s in your own 'My AI Settings'. The refresh uses your key "
                "to query the provider's /models endpoint."
            ) % self.name)

        provider = get_provider(
            self.code, config.api_key, config.selected_model, self.api_base_url,
        )

        try:
            models_list = provider.list_models()
        except AIAuthError as e:
            raise UserError(_(
                "Authentication failed when querying %s. Check that your API "
                "key in My AI Settings is valid and not restricted.\n\n%s"
            ) % (self.name, str(e)[:300]))
        except AINotFoundError as e:
            raise UserError(_(
                "The /models endpoint was not found on %s. Either the API "
                "URL is wrong, or this provider doesn't expose model listing.\n\n%s"
            ) % (self.name, str(e)[:300]))
        except AINetworkError as e:
            raise UserError(_("Network error reaching %s: %s") % (self.name, e))
        except NotImplementedError:
            raise UserError(_(
                "This provider doesn't support model-list fetching."
            ))
        except AIProviderError as e:
            raise UserError(_("Could not fetch models from %s:\n\n%s") % (
                self.name, str(e)[:400]
            ))

        if not models_list:
            raise UserError(_(
                "The provider returned no usable models. The API may have "
                "responded with embedding/audio-only models that don't fit "
                "this assistant's generation requirements."
            ))

        # Preserve existing default_model if still available, else pick first
        old_default = self.default_model
        if old_default in models_list:
            new_default = old_default
            default_note = ""
        else:
            new_default = models_list[0]
            default_note = _("\n\nNote: previous default '%s' is no longer "
                             "available. Default changed to '%s'.") % (
                old_default, new_default,
            )

        self.write({
            "available_models": "\n".join(models_list),
            "default_model":    new_default,
        })

        return {
            "type": "ir.actions.client",
            "tag":  "display_notification",
            "params": {
                "title":   _("Models refreshed"),
                "message": _("Fetched %d models from %s.") % (
                    len(models_list), self.name,
                ) + default_note,
                "type":    "success",
                "sticky":  False,
            },
        }

    @api.constrains("is_default")
    def _check_default(self):
        """Ensure at most one provider is flagged as default."""
        for rec in self:
            if rec.is_default:
                others = self.search([("is_default", "=", True), ("id", "!=", rec.id)])
                if others:
                    raise ValidationError(_(
                        "Only one provider can be marked as the default. "
                        "Please unset the current default first."
                    ))
