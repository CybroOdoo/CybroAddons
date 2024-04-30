# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj (odoo@cybrosys.com)
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


class ProductTransferHistory(models.TransientModel):
    """This class represents a wizard to display the history of product
       transfers.It provides a simple way to view information about product
       transfers, including dates, transfer identifiers, associated contacts,
       transferred quantities, and references to transfer product details
       wizards."""
    _name = 'product.transfer.history'
    _description = 'Product Transfer History Wizard'

    date_picking = fields.Datetime(string="Date",
                                   help="Date of the transfer.")
    picking = fields.Char(string="Transfer",
                          help="Identifier of the transfer.")
    partner_id = fields.Many2one('res.partner', string="Contact",
                                 help="Contact associated with the transfer.")
    qty = fields.Float(string="Quantity",
                       help="Quantity of the product transferred.")
    product_details_id = fields.Many2one('transfer.products.details',
                                         string="Products Details",
                                         help="Reference to the transfer "
                                              "product details wizard.")
