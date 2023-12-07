# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev K P (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class ResPartner(models.Model):
    """inheriting res_partner model to set return orders """
    _inherit = 'res.partner'

    return_order_count = fields.Integer(compute="_compute_returns",
                                        string='Return Orders',
                                        help="Number of return orders")

    def _compute_returns(self):
        """Function to calculate the return count"""
        all_partners = (self.with_context(active_test=False).sudo().
                        search([('id', 'child_of', self.ids)]))
        all_partners.read(['parent_id'])
        sale_return_groups = self.env['sale.return'].sudo().read_group(
            domain=[('partner_id', '=', all_partners.ids)],
            fields=['partner_id'], groupby=['partner_id'])
        partners = self.sudo().browse()
        for group in sale_return_groups:
            partner = self.browse(group['partner_id'][0])
            while partner:
                if partner in self:
                    partner.return_order_count += group['partner_id_count']
                    partners |= partner
                    partner = partner.parent_id
        (self - partners).return_order_count = 0

    def action_open_returns(self):
        """This function returns an action that displays the sale return orders
         from partner."""

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
