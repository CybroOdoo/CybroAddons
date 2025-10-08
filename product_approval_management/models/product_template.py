# -*- coding: utf-8 -*-
#############################################################################

#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models


class ProductTemplate(models.Model):
    """The module is used to add the approval state in the product form page"""
    _inherit = 'product.template'

    approve_state = fields.Selection([('draft', 'Draft'),
                                      ('confirmed', 'Confirmed')],
                                     default='draft', string='State',
                                     help='State to approve')

    def action_confirm_product_approval(self):
        """Confirm button on the product form page"""
        for rec in self:
            rec.approve_state = 'confirmed'

    def action_reset_product_approval(self):
        """Reset to draft state button on the product form page"""
        for rec in self:
            rec.approve_state = 'draft'

    def action_confirm_products(self):
        """Bulk product approval button on the product form page"""
        active_ids = self.env.context.get('active_ids')
        products = self.env['product.template'].browse(active_ids)
        products.confirm_product_approval()
