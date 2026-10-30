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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
import logging

from odoo.exceptions import AccessError, UserError
from odoo.http import request

from odoo.addons.web.controllers import home

_logger = logging.getLogger(__name__)


class PosScreen(home.Home):
    """Override Home controller to redirect user directly to POS."""

    def _login_redirect(self, uid, redirect=None):
        """Redirect to configured POS shop on login."""
        user = request.env['res.users'].sudo().browse(uid)
        if user.pos_conf_id and user.has_group('point_of_sale.group_pos_user'):
            pos_config = user.pos_conf_id
            if not pos_config.current_session_id:
                try:
                    pos_config.with_user(user).open_session_if_not_opened()
                except (UserError, AccessError) as err:
                    _logger.debug("Could not auto-open POS session: %s", err)
            return f'/pos/ui/{pos_config.id}'
        return super()._login_redirect(uid, redirect=redirect)
