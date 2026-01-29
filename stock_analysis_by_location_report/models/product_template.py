# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
from odoo import fields, models, _


class ProductTemplate(models.Model):
    """Inherited product template to add additional fields and compute methods
     for quantity computation"""
    _inherit = 'product.template'

    qty_incoming = fields.Float(string='Incoming Qty',
                                compute='_compute_quantities', store=True,
                                help='Incoming quantity of the product')
    qty_outgoing = fields.Float(string='Outgoing Qty',
                                compute='_compute_quantities', store=True,
                                help='Outgoing quantity of the product')
    qty_avail = fields.Float(string='Available Qty',
                             compute='_compute_quantities', store=True,
                             help='Available quantity of the product')
    qty_virtual = fields.Float(string='Virtual Qty',
                               compute='_compute_quantities', store=True,
                               help='Virtual quantity of the product')

    def _compute_quantities(self):
        """Function for computing the incoming, outgoing,available, and virtual
         quantities for the product template"""
        res = super()._compute_quantities()
        for template in self:
            template.qty_incoming = template.incoming_qty
            template.qty_outgoing = template.outgoing_qty
            template.qty_avail = template.qty_available
            template.qty_virtual = template.virtual_available
        return res


class ProductProduct(models.Model):
    """Inherited product template to add additional fields and compute methods
    for quantity computation"""
    _inherit = 'product.product'

    qty_incoming = fields.Float(string='Incoming Qty',
                                compute='_compute_quantities', store=True)
    qty_outgoing = fields.Float(string='Outgoing Qty',
                                compute='_compute_quantities', store=True)
    qty_avail = fields.Float(string='Available Qty',
                             compute='_compute_quantities', store=True)
    qty_virtual = fields.Float(string='Virtual Qty',
                               compute='_compute_quantities', store=True)

    def _compute_quantities_dict(self, lot_id, owner_id, package_id,
                                 from_date=False, to_date=False):
        """Function for computing the incoming, outgoing,available, and virtual
                 quantities for the product"""
        res = super()._compute_quantities_dict(lot_id, owner_id, package_id,
                                               from_date=False, to_date=False)
        for product in self.with_context(prefetch_fields=False):
            product_id = product.id
            product.qty_incoming = res[product_id]['incoming_qty']
            product.qty_outgoing = res[product_id]['outgoing_qty']
            product.qty_avail = res[product_id]['qty_available']
            product.qty_virtual = res[product_id]['virtual_available']
        return res
