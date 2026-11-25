# -*- coding: utf-8 -*-
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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import logging
import secrets

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Generates a secure shared webhook secret on module install if not already present."""
    icp = env['ir.config_parameter'].sudo()
    secret = icp.get_str('ora_ai_base.vapi_webhook_secret')
    if not secret:
        new_secret = secrets.token_hex(24)
        icp.set_str('ora_ai_base.vapi_webhook_secret', new_secret)
        _logger.info("Generated initial secure Vapi webhook secret.")

