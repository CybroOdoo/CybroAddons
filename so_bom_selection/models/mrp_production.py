# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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


class MrpProductionInherit(models.Model):
    _inherit = 'mrp.production'

    source = fields.Char(string='Source',
                         help='Sale Order from which this Manufacturing '
                              'Order created')
    qty_to_produce = fields.Float(string='Quantity to Produce',
                                  help='The number of products to be produced')

    def update_quantity(self):
        """ Method for changing the quantities of components according to
         product quantity """
        for rec in self.move_raw_ids:
            self.write({
                'move_raw_ids': [
                    (1, rec.id, {
                        'product_uom_qty': rec.product_uom_qty *
                                           self.qty_to_produce,
                    }),
                ]
            })
