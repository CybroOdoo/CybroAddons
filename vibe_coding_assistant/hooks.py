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

"""Post-init/upgrade hook for vibe_coding_assistant.

Refreshes the available_models field on each seeded provider so that
upgrading the module (-u) picks up new model IDs without requiring the
admin to manually edit the records.

Why this is needed: the seed records in data/ai_provider_data.xml use
noupdate="1" so they aren't overwritten on -u (which would clobber any
admin customisations). This hook fills the gap: it updates the model
catalogue but leaves all other fields (default_model, base URL, etc.)
untouched, AND skips records the admin has marked as customised by
manually editing them.
"""

# Latest known model IDs per provider. Update here when new models ship.
LATEST_MODELS = {
    "gemini": [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ],
    "claude": [
        "claude-opus-4-5",
        "claude-sonnet-4-5",
        "claude-haiku-4-5",
        "claude-opus-4-1",
        "claude-sonnet-4",
        "claude-3-7-sonnet-latest",
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
    ],
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4.1",
        "gpt-4.1-mini",
        "o1",
        "o1-mini",
        "o3-mini",
    ],
}


def refresh_provider_models(env):
    """Refresh available_models for each provider that still exists.

    Called from __manifest__.py's post_init_hook and post_update_hook.
    """
    Provider = env["ai.provider"]
    for code, models in LATEST_MODELS.items():
        provider = Provider.search([("code", "=", code)], limit=1)
        if provider:
            new_list = "\n".join(models)
            if provider.available_models != new_list:
                provider.write({"available_models": new_list})
