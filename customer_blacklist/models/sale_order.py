# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_blacklist_warning = fields.Text(
        compute='_compute_partner_blacklist_warning', help="Warning message",
        string="warning"
    )

    @api.depends('partner_id')
    def _compute_partner_blacklist_warning(self):
        """Add warning message on sale order if the customer is blacklisted"""
        for rec in self:
            if rec.partner_id.blacklisted_partner:
                rec.partner_blacklist_warning = _(
                    'The %s is marked as blacklisted' % rec.partner_id.name
                )
            else:
                rec.partner_blacklist_warning = ''
