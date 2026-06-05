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

import json
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

# Service imports at module level — these modules contain no odoo imports
# so there is no circular-import risk.
from ..services.prompt_builder import build as build_prompt, build_refinement
from ..services.provider_base import get_provider, AIProviderError
from ..services.response_parser import parse as parse_response, ResponseParseError
from ..services.module_validator import validate as validate_module
from ..services.template_merger import merge_templates
from ..services.intent_gate import check_intent

_logger = logging.getLogger(__name__)


class VibeConversation(models.Model):
    _name = "vibe.conversation"
    _description = "Vibe Conversation"
    _order = "last_activity desc, id desc"

    name = fields.Char(
        string="Name",
        required=True,
        default=lambda self: _("New Chat"),
    )
    user_id = fields.Many2one(
        "res.users",
        string="User",
        required=True,
        default=lambda self: self.env.user,
        ondelete="cascade",
    )
    provider_config_id = fields.Many2one(
        "ai.provider.user.config",
        string="Provider Config",
        help="Snapshot of the active config when this conversation started.",
        ondelete="set null",
    )
    message_ids = fields.One2many(
        "vibe.message", "conversation_id", string="Messages"
    )
    generated_module_ids = fields.One2many(
        "vibe.generated.module", "conversation_id", string="Generated Modules"
    )
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("archived", "Archived")],
        string="State",
        default="draft",
    )
    last_activity = fields.Datetime(string="Last Activity")

    # ── Aggregate token usage ──────────────────────────────────────────────
    tokens_input_total = fields.Integer(
        string="Input Tokens (Total)",
        compute="_compute_token_totals",
        store=True,
    )
    tokens_output_total = fields.Integer(
        string="Output Tokens (Total)",
        compute="_compute_token_totals",
        store=True,
    )
    tokens_total = fields.Integer(
        string="Tokens Used",
        compute="_compute_token_totals",
        store=True,
        help="Sum of input + output tokens across all messages in this conversation.",
    )

    @api.depends("message_ids.tokens_input", "message_ids.tokens_output", "message_ids.tokens_used")
    def _compute_token_totals(self):
        for conv in self:
            conv.tokens_input_total  = sum(conv.message_ids.mapped("tokens_input"))
            conv.tokens_output_total = sum(conv.message_ids.mapped("tokens_output"))
            conv.tokens_total        = sum(conv.message_ids.mapped("tokens_used"))

    # ── Public API (called from OWL frontend via orm.call) ────────────────

    def action_send_message(self, content):
        """Full generation pipeline: prompt → AI → parse → validate → persist.

        JS call:
            orm.call("vibe.conversation", "action_send_message", [[this.id], content])
        """
        self.ensure_one()
        if not content or not content.strip():
            raise UserError(_("Message cannot be empty."))

        config = self.env["ai.provider.user.config"].get_active_config_for_user()
        if not config:
            raise UserError(_(
                "No active AI provider found. "
                "Go to Vibe Coding → My AI Settings and activate a config."
            ))

        # 1. Persist user message
        self.env["vibe.message"].create({
            "conversation_id": self.id,
            "role": "user",
            "content": content,
        })
        if not self.name or self.name == _("New Chat"):
            self.name = (content[:60] + "…") if len(content) > 60 else content

        # 1b. Cheap local intent gate — skip the (token-expensive) provider
        # call entirely when the message clearly isn't a module-build request
        # (greeting, small talk, general question). Conservative: only a
        # confident "offtopic" verdict short-circuits; "build" and "unsure"
        # both fall through to generation (fail-open), so a real request is
        # never silently blocked. This avoids spending ~1k input tokens on
        # the full system prompt just to have the model refuse.
        gate = check_intent(content)
        if gate["verdict"] == "offtopic":
            _logger.info("Intent gate skipped generation (%s)", gate["reason"])
            self.env["vibe.message"].create({
                "conversation_id": self.id,
                "role": "assistant",
                "content": self._module_only_message(),
            })
            self.write({
                "last_activity": fields.Datetime.now(),
                "state": "active",
            })
            return self._payload()

        # 2. Call provider
        system_prompt, user_prompt = build_prompt(content)
        provider = get_provider(
            config.provider_id.code,
            config.api_key,
            config.selected_model,
            config.provider_id.api_base_url,
        )

        try:
            raw, usage = provider.generate(system_prompt, user_prompt)
        except AIProviderError as e:
            _logger.warning(
                "AI provider error [%s]: %s", config.provider_id.code, type(e).__name__
            )
            self.env["vibe.message"].create({
                "conversation_id": self.id,
                "role": "assistant",
                "content": _("Provider error: %s") % str(e),
            })
            return self._payload()

        # 3. Parse JSON envelope
        try:
            parsed = parse_response(raw)
        except ResponseParseError:
            _logger.warning("Response parse failed — raw length: %s", len(raw))
            # The provider call succeeded and consumed tokens even though the
            # output wasn't a usable module — record them so conversation and
            # dashboard totals stay accurate, and attribute the spend to the
            # provider config that was used.
            self.env["vibe.message"].create({
                "conversation_id": self.id,
                "role": "assistant",
                "content": self._module_only_message(),
                "tokens_input":  usage.get("input", 0),
                "tokens_output": usage.get("output", 0),
                "tokens_used":   usage.get("total", 0),
            })
            self.write({
                "last_activity":      fields.Datetime.now(),
                "provider_config_id": config.id,
            })
            return self._payload()

        # 3b. Merge in standard boilerplate (README, LICENSE, doc/, etc.)
        # Done BEFORE persistence and validation so the templates are part
        # of the canonical file list, get validated, and appear in the
        # downloaded ZIP and file-tree preview.
        try:
            merge_templates(parsed)
        except Exception as e:
            # Template merging is best-effort — failure shouldn't kill the
            # whole generation. Log and continue with what we have.
            _logger.warning("Template merge failed (continuing without): %s", e)

        # 4. Persist generated module + files
        mod = self.env["vibe.generated.module"].create({
            "conversation_id": self.id,
            "technical_name": parsed["module"]["technical_name"],
            "name": parsed["module"]["display_name"],
            "manifest_data": json.dumps(parsed["module"]),
        })
        self.env["vibe.generated.file"].create([
            {"module_id": mod.id, "path": f["path"], "content": f["content"]}
            for f in parsed["files"]
        ])

        # 5. Validate (manifest + structure)
        errors = validate_module(parsed)
        mod.write({
            "validation_state": "valid" if not errors else "invalid",
            "validation_errors": json.dumps(errors) if errors else False,
        })

        # 6. Persist assistant message linked to the module
        assistant_msg = self.env["vibe.message"].create({
            "conversation_id": self.id,
            "role": "assistant",
            "content": _("Generated module: %s") % mod.name,
            "generated_module_id": mod.id,
            "tokens_input":  usage.get("input", 0),
            "tokens_output": usage.get("output", 0),
            "tokens_used":   usage.get("total", 0),
        })
        mod.write({"message_id": assistant_msg.id})

        self.write({
            "last_activity": fields.Datetime.now(),
            "state": "active",
            "provider_config_id": config.id,
        })

        return self._payload()

    def action_refine_module(self, content):
        """Send a refinement prompt that builds on the conversation's most
        recent generated module.

        Wraps the AI call with the previous module's full state as context,
        creates a new vibe.generated.module record linked back to the
        previous one via parent_module_id, and increments revision_number.

        Differs from action_send_message in three ways:
          1. Resolves the previous module first (errors out if none exists)
          2. Uses build_refinement() to construct a prompt that includes the
             full previous module JSON
          3. Stamps parent_module_id + revision_number on the new record

        JS call:
            orm.call("vibe.conversation", "action_refine_module", [[id], content])
        """
        self.ensure_one()
        if not content or not content.strip():
            raise UserError(_("Refinement request cannot be empty."))

        # 0. Find the previous module to refine. We use the most recent
        # generated module in this conversation, regardless of whether it's
        # itself a refinement — refinements chain naturally (v1 -> v2 -> v3).
        previous = self.env["vibe.generated.module"].search(
            [("conversation_id", "=", self.id)],
            order="create_date desc, id desc",
            limit=1,
        )
        if not previous:
            raise UserError(_(
                "No previous module to refine in this conversation. "
                "Send a normal message first to generate the initial module."
            ))

        config = self.env["ai.provider.user.config"].get_active_config_for_user()
        if not config:
            raise UserError(_(
                "No active AI provider found. "
                "Go to Vibe Coding → My AI Settings and activate a config."
            ))

        # 1. Persist user message (tagged so the UI can distinguish refinements)
        self.env["vibe.message"].create({
            "conversation_id": self.id,
            "role": "user",
            "content": "🔄 Refine: " + content,
        })

        # 2. Build the refinement prompt
        try:
            previous_module_data = json.loads(previous.manifest_data or "{}")
        except (json.JSONDecodeError, TypeError):
            previous_module_data = {}
        previous_files = [
            {"path": f.path, "content": f.content}
            for f in previous.file_ids
        ]
        system_prompt, user_prompt = build_refinement(
            content, previous_module_data, previous_files,
        )

        provider = get_provider(
            config.provider_id.code,
            config.api_key,
            config.selected_model,
            config.provider_id.api_base_url,
        )

        # 3. Call provider — refinements use significantly more input tokens
        # than fresh generations (the previous module is embedded verbatim).
        try:
            raw, usage = provider.generate(system_prompt, user_prompt)
        except AIProviderError as e:
            _logger.warning(
                "AI provider error during refinement [%s]: %s",
                config.provider_id.code, type(e).__name__,
            )
            self.env["vibe.message"].create({
                "conversation_id": self.id,
                "role": "assistant",
                "content": _("Provider error: %s") % str(e),
            })
            return self._payload()

        # 4. Parse the response
        try:
            parsed = parse_response(raw)
        except ResponseParseError:
            _logger.warning("Refinement parse failed — raw length: %s", len(raw))
            # Record the tokens the failed call still consumed (see the
            # equivalent note in action_send_message).
            self.env["vibe.message"].create({
                "conversation_id": self.id,
                "role": "assistant",
                "content": _(
                    "The AI returned an invalid response to the refinement. "
                    "Please rephrase your request and try again."
                ),
                "tokens_input":  usage.get("input", 0),
                "tokens_output": usage.get("output", 0),
                "tokens_used":   usage.get("total", 0),
            })
            self.write({
                "last_activity":      fields.Datetime.now(),
                "provider_config_id": config.id,
            })
            return self._payload()

        # 4b. Merge in standard boilerplate (same as fresh generations)
        try:
            merge_templates(parsed)
        except Exception as e:
            _logger.warning("Template merge failed during refinement: %s", e)

        # 5. Persist as a new module record linked to the previous one
        new_revision = (previous.revision_number or 1) + 1
        mod = self.env["vibe.generated.module"].create({
            "conversation_id":  self.id,
            "technical_name":   parsed["module"]["technical_name"],
            "name":             parsed["module"]["display_name"],
            "manifest_data":    json.dumps(parsed["module"]),
            "parent_module_id": previous.id,
            "revision_number":  new_revision,
        })
        self.env["vibe.generated.file"].create([
            {"module_id": mod.id, "path": f["path"], "content": f["content"]}
            for f in parsed["files"]
        ])

        # 6. Validate the refined module
        errors = validate_module(parsed)
        mod.write({
            "validation_state":  "valid" if not errors else "invalid",
            "validation_errors": json.dumps(errors) if errors else False,
        })

        # 7. Assistant message linked to the new module
        assistant_msg = self.env["vibe.message"].create({
            "conversation_id":     self.id,
            "role":                "assistant",
            "content":             _("Refined module: %s (revision %d)") % (
                mod.name, new_revision,
            ),
            "generated_module_id": mod.id,
            "tokens_input":  usage.get("input", 0),
            "tokens_output": usage.get("output", 0),
            "tokens_used":   usage.get("total", 0),
        })
        mod.write({"message_id": assistant_msg.id})

        self.write({
            "last_activity":      fields.Datetime.now(),
            "state":              "active",
            "provider_config_id": config.id,
        })

        return self._payload()

    def load_messages(self):
        """Return the full payload for this conversation.

        JS call:
            orm.call("vibe.conversation", "load_messages", [[conv_id]])
        """
        self.ensure_one()
        return self._payload()

    def action_archive(self):
        """Mark conversation as archived so it no longer appears in the sidebar."""
        self.ensure_one()
        self.write({"state": "archived"})
        return True

    def action_export_json(self):
        """Form-button action: trigger a browser download of the JSON export.

        Returns an ir.actions.act_url action that the Odoo web client will
        open in the same tab — but since the controller responds with
        Content-Disposition: attachment, the browser prompts a download
        instead of navigating.
        """
        self.ensure_one()
        return {
            "type":   "ir.actions.act_url",
            "url":    "/vibe/conversation/%d/export" % self.id,
            "target": "self",
        }

    # ── Private helpers ───────────────────────────────────────────────────

    def _module_only_message(self):
        """The guidance shown when a message isn't a module-build request.

        Used by both the local intent gate (zero-cost short-circuit) and the
        response-parse-error branch (model refused / returned an error
        envelope). Kept in one place so the wording stays consistent and
        translatable.
        """
        return _(
            "I can only generate Odoo modules. "
            "Try a prompt like 'Create a module in odoo to manage.....'"
        )

    def _payload(self):
        """Serialise conversation state for the OWL frontend."""
        self.ensure_one()
        messages = []
        for m in self.message_ids:
            mod = m.generated_module_id
            messages.append({
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "generated_module_id": mod.id if mod else False,
                "generated_module_name": mod.name if mod else False,
                "generated_module_technical_name": mod.technical_name if mod else False,
                "generated_module_version": self._manifest_field(mod, "version") if mod else False,
                "generated_module_summary": self._manifest_field(mod, "summary") if mod else False,
                "generated_module_category": self._manifest_field(mod, "category") if mod else False,
                "generated_module_depends": self._manifest_field(mod, "depends") if mod else False,
                "generated_module_file_count": len(mod.file_ids) if mod else 0,
                "validation_state": mod.validation_state if mod else False,
                "validation_error_count": (
                    len(mod.get_validation_errors_list()) if mod else 0
                ),
                # Refinement metadata — None for fresh generations, integer
                # for refinement revisions; lets the UI show a "v2", "v3"
                # badge and a "based on previous" link.
                "generated_module_revision":      mod.revision_number if mod else 0,
                "generated_module_parent_id":     (
                    mod.parent_module_id.id if mod and mod.parent_module_id else False
                ),
                # Token usage per-message (assistant messages only)
                "tokens_input":  m.tokens_input,
                "tokens_output": m.tokens_output,
                "tokens_used":   m.tokens_used,
            })

        # The frontend's Refine button is enabled only when there's
        # something to refine. Find the most recent module in this
        # conversation if any exists.
        latest_module = self.env["vibe.generated.module"].search(
            [("conversation_id", "=", self.id)],
            order="create_date desc, id desc",
            limit=1,
        )

        return {
            "conversation": {
                "id": self.id,
                "name": self.name,
                "state": self.state,
                # Running totals for this conversation
                "tokens_input_total":  self.tokens_input_total,
                "tokens_output_total": self.tokens_output_total,
                "tokens_total":        self.tokens_total,
                # Refinement state — what the Refine button needs
                "can_refine": bool(latest_module),
                "latest_module_name":     latest_module.name if latest_module else False,
                "latest_module_revision": latest_module.revision_number if latest_module else 0,
            },
            "messages": messages,
        }

    def _manifest_field(self, mod, key):
        """Safely pull a single value out of vibe.generated.module.manifest_data."""
        if not mod or not mod.manifest_data:
            return False
        try:
            return json.loads(mod.manifest_data).get(key, False)
        except (json.JSONDecodeError, TypeError):
            return False
