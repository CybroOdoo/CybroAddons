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


class Http(models.AbstractModel):
    """Class inherits Http to update user group values."""
    _inherit = 'ir.http'

    def session_info(self):
        """Overriding the function to update user group values in session."""
        res = super().session_info()
        res.update({
            'access_send_message_btn': self.env.user.has_group(
                'mail_message_access.group_allow_send_message_btn'
            ),
            'access_log_note_btn': self.env.user.has_group(
                'mail_message_access.group_allow_log_note_btn'
            ),
        })
        return res
