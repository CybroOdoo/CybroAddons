# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import fields, models


class ProductChangeTracking(models.TransientModel):
    """
        Model for changing tracking method
    """
    _name = 'product.change.tracking'
    _description = 'Change Product Tracking Method'

    product_ids = fields.Many2many('product.template',
                                   string='Selected Products',
                                   readonly=True,
                                   help='Products that are selected to change '
                                        'the tracking')
    tracking = fields.Selection([
        ('serial', 'By Unique Serial Number'),
        ('lot', 'By Lots'),
        ('none', 'No Tracking')],
        string='Tracking',
        help='Select a tracking type to update for the selected products',
        default='none', required=True)

    def action_change_product_tracking(self):
        """
        Function for changing tracking method of selected products
        """
        for products in self.product_ids:
            products.write({'tracking': self.tracking})
