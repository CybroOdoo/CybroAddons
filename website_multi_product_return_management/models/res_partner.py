# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R (odoo@cybrosys.com)
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
from odoo import fields, models


class ResPartner(models.Model):
    """
       Extends the base 'res.partner' model to include additional fields
       and functionality.
    """
    _inherit = 'res.partner'

    return_order_count = fields.Integer(
        compute="_compute_return_order_count", string='Return Orders',
        help="Count of order returned by the customer")

    def _compute_return_order_count(self):
        """Function to calculate the return count"""
        all_partners = self.with_context(active_test=False).sudo().search(
            [('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])
        sale_return_groups = self.env['sale.return'].sudo().read_group(
            domain=[('partner_id', 'in', all_partners.ids)],
            fields=['partner_id'], groupby=['partner_id'])
        for partner in self:
            partner.return_order_count = int(
                sale_return_groups[0]['partner_id_count'])

    def action_open_returns(self):
        """This function returns an action that displays the sale return
        orders from partner."""
        action = self.env['ir.actions.act_window']._for_xml_id(
            'website_multi_product_return_management.sale_return_action')
        domain = []
        if self.is_company:
            domain.append(('partner_id.commercial_partner_id.id', '=', self.id))
        else:
            domain.append(('partner_id.id', '=', self.id))
        action['domain'] = domain
        action['context'] = {'search_default_customer': 1}
        return action
