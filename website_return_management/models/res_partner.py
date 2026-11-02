# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Abbas P (odoo@cybrosys.com)
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
from odoo import fields, models


class ResPartner(models.Model):
    """Inherited res partner for adding return order count"""
    _inherit = 'res.partner'

    return_order_count = fields.Integer(string='Return Orders',
                                        compute="_compute_returns",
                                        help="For getting the return order count")

    def _compute_returns(self):
        """Function to calculate the return count"""
        all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        all_partners.read(['parent_id'])
        sale_return_groups = self.env['sale.return'].sudo()._read_group(
            [('partner_id', 'in', all_partners.ids)],
            groupby=['partner_id'], aggregates=['__count'])
        partners = self.browse()
        for partner, count in sale_return_groups:
            while partner:
                if partner in self:
                    partner.return_order_count += count
                    partners |= partner
                partner = partner.parent_id
        (self - partners).return_order_count = 0

    def action_open_returns(self):
        """This function returns an action that displays the sale return orders
        from partner."""
        action = self.env['ir.actions.act_window']._for_xml_id('website_return_management.action_sale_return')
        action['domain'] = [('partner_id', 'child_of', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action
