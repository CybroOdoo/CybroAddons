# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ranjith R(<https://www.cybrosys.com>)
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
###########################################################################
from odoo import fields, models


class ScrapManagementLine(models.Model):
    """ Used to manage scrap components """
    _name = "scrap.management.line"
    _description = "Scrap Management Line"

    product_id = fields.Many2one('product.product',
                                 String="Product", readonly=True,
                                 help="Field to specify product")
    scrap_management_id = fields.Many2one('scrap.management',
                                          String="Product", readonly=True,
                                          help="Field to specify "
                                               "scrap management order")
    dismantle_qty = fields.Integer(String="Available quantity", readonly=True,
                                   help="Field to specify total quantity")
    useful_qty = fields.Integer(string="Useful Product Quantity",
                                help="Field to specify useful quantity")
