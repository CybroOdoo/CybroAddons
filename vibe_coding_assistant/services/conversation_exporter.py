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

"""Conversation export service.

Serialises a `vibe.conversation` record into a single JSON file containing
the whole chat history, every assistant response, and every generated
module (with full file contents inlined).

Export format is versioned via the `format_version` field so future imports
can read older exports cleanly. The current format is "1".

Design notes:
- API keys, internal record IDs of other models, and per-user fields are
  intentionally excluded. The export is meant to be shared.
- Generated-module file contents are inlined as strings, not refs — the
  export is fully self-contained.
- Token counts are included because they don't reveal anything sensitive
  and help the recipient understand the cost of regenerating the work.
"""

import json
import logging

from odoo import fields

_logger = logging.getLogger(__name__)

EXPORT_FORMAT_VERSION = "1"


def build_export(conversation):
    """Return (filename, json_bytes) for the given vibe.conversation record.

    :param conversation: a single vibe.conversation recordset (ensure_one)
    :returns: tuple (filename_str, bytes_to_send)
    """
    conversation.ensure_one()

    payload = {
        "format_version": EXPORT_FORMAT_VERSION,
        "exported_at": fields.Datetime.now().isoformat(),
        "exported_from": {
            "odoo_version": "19.0",
            "module": "vibe_coding_assistant",
        },
        "conversation": _conversation_dict(conversation),
        "messages": [_message_dict(m) for m in conversation.message_ids],
        "generated_modules": [
            _module_dict(mod) for mod in conversation.generated_module_ids
        ],
    }

    json_text = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False)
    json_bytes = json_text.encode("utf-8")

    filename = _build_filename(conversation)
    _logger.info(
        "Conversation export: id=%s, %d messages, %d modules, %d bytes",
        conversation.id,
        len(payload["messages"]),
        len(payload["generated_modules"]),
        len(json_bytes),
    )
    return filename, json_bytes


# ── Per-record serialisers ────────────────────────────────────────────────


def _conversation_dict(c):
    """Top-level conversation metadata. Excludes user IDs and other
    instance-specific references."""
    return {
        "name": c.name,
        "state": c.state,
        "last_activity": c.last_activity.isoformat() if c.last_activity else None,
        "tokens_input_total":  c.tokens_input_total,
        "tokens_output_total": c.tokens_output_total,
        "tokens_total":        c.tokens_total,
        "provider_name": c.provider_config_id.provider_id.name
                         if c.provider_config_id else None,
        "model": c.provider_config_id.selected_model
                 if c.provider_config_id else None,
    }


def _message_dict(m):
    """One chat message. Includes role, content, tokens, and the linked
    module's technical name (so the importer can match it up)."""
    return {
        "role": m.role,
        "content": m.content,
        "created_at": m.create_date.isoformat() if m.create_date else None,
        "tokens_input":  m.tokens_input or 0,
        "tokens_output": m.tokens_output or 0,
        "tokens_used":   m.tokens_used or 0,
        "generated_module_technical_name": (
            m.generated_module_id.technical_name if m.generated_module_id else None
        ),
    }


def _module_dict(mod):
    """A generated module with all files inlined.

    The manifest_data field is parsed back from JSON so the export contains
    real nested data, not a string blob.
    """
    try:
        manifest = json.loads(mod.manifest_data) if mod.manifest_data else {}
    except (json.JSONDecodeError, TypeError):
        manifest = {}

    try:
        validation_errors = (
            json.loads(mod.validation_errors) if mod.validation_errors else []
        )
    except (json.JSONDecodeError, TypeError):
        validation_errors = []

    return {
        "technical_name": mod.technical_name,
        "display_name":   mod.name,
        "manifest":       manifest,
        "validation_state":  mod.validation_state,
        "validation_errors": validation_errors,
        "download_count":    mod.download_count,
        "files": [
            {
                "path":     f.path,
                "language": f.language,
                "content":  f.content,
            }
            for f in mod.file_ids
        ],
    }


# ── Filename helper ───────────────────────────────────────────────────────


def _build_filename(conversation):
    """Produce a clean, dated filename for the JSON download.

    Format: vibe-{slug}-{YYYY-MM-DD}.json
    Where {slug} is the first generated module's technical name, or "chat-{id}"
    if no module was generated.
    """
    today = fields.Date.today().isoformat()
    slug = "chat-%d" % conversation.id
    mods = conversation.generated_module_ids
    if mods and mods[0].technical_name:
        slug = mods[0].technical_name
    return "vibe-%s-%s.json" % (slug, today)
