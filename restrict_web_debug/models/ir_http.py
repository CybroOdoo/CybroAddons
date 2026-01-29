# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import models


class IrHttp(models.AbstractModel):
    """Inherits ir.http to add value in 'restrict_debug_mode' group of user
        into session"""
    _inherit = 'ir.http'

    def session_info(self):
        """Set a value(user_group) to session values to access from js to hide
           and show debug icon based on user enable or disable the group."""
        info = super().session_info()
        info["user_group"] = self.env.user.has_group('restrict_web_debug.'
                                                     'restrict_debug_mode')
        return info
