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

from . import models, controllers, services
from .hooks import refresh_provider_models


def _refresh_provider_models_hook(env):
    """Post-init hook: refresh available_models on seeded providers.

    Note: Odoo 17+ post-init hooks receive `env` directly. Older versions
    received (cr, registry) — the try/except below makes the hook compatible
    across Odoo versions for graceful upgrades.
    """
    # Odoo 17+ signature: env is passed directly
    if hasattr(env, "cr"):
        refresh_provider_models(env)
        return

    # Legacy fallback (Odoo 16 and earlier): env is actually (cr, registry)
    from odoo import api, SUPERUSER_ID
    cr = env
    real_env = api.Environment(cr, SUPERUSER_ID, {})
    refresh_provider_models(real_env)
