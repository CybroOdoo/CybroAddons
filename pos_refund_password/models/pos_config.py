# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
###############################################################################
from odoo import api, fields, models


class PosConfig(models.Model):
    """This class used to inherit from pos.config in order to add fields such as
    refund_security."""
    _inherit = 'pos.config'

    refund_security = fields.Char(string='Refund Security',
                                  help='This filed  used to store password '
                                       'for refund ')

    @api.constrains('refund_security')
    def _check_refund_security(self):
        """The function has Checked the refund security"""
        for config in self:
            if config.refund_security and not config.refund_security.isdigit():
                raise models.ValidationError(
                    "Invalid password format. Password can only contain digits."
                )
