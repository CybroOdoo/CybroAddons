# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
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
from odoo import api, fields, models


class ResUsers(models.Model):
    """Add POS button restrictions to the user form."""
    _inherit = 'res.users'

    buttons_pos_ids = fields.Many2many(
        'pos.buttons',
        string="POS Buttons",
        help=(
            "Select the POS buttons that should be disabled for this user "
            "in the Point of Sale."
        ),
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Loading Fields"""
        result = super()._load_pos_data_fields(config_id)
        result += ['buttons_pos_ids']
        return result
