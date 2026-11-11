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
from odoo import models
from odoo.exceptions import UserError


class PosSession(models.Model):
    """Inherits pos.session to enforce manager approval on session closing."""
    _inherit = 'pos.session'

    def close_session_from_ui(self, payment_method_closing=None):
        """Validates manager approval before closing POS session."""
        for session in self:
            config = session.config_id
            if config.pos_restaurant_restriction and config.pos_session_close:
                order_ref = session.name
                if not config.is_restriction_authorized('session_close', order_ref=order_ref):
                    raise UserError(self.env._(
                        "Manager approval is required to close the POS session."
                    ))
        if payment_method_closing is not None:
            return super().close_session_from_ui(payment_method_closing=payment_method_closing)
        return super().close_session_from_ui()

