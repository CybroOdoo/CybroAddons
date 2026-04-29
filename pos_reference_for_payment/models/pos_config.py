# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class PosConfig(models.Model):
    """Inherited POS Configuration model.
        This class extends `pos.config` to control whether
        payment reference entry is allowed in the Point of Sale.
        The value is computed from a system configuration parameter."""
    _inherit = 'pos.config'

    is_allow_payment_ref = fields.Boolean(compute='_compute_allow_ref', string='Allow Payment Reference')

    @api.depends('is_allow_payment_ref')
    def _compute_allow_ref(self):
        """Compute method to determine if payment reference is allowed.
        The value is fetched from `ir.config_parameter`
        (`pos_reference_for_payment.is_allow_payment_ref`)
        and converted to a boolean before being assigned
        to the POS configuration record."""
        for config in self:
            config.is_allow_payment_ref = self.env['ir.config_parameter'].sudo().get_param('pos_reference_for_payment.is_allow_payment_ref')