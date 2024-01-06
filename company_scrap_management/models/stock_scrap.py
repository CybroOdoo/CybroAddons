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


class StockScrap(models.Model):
    """ Used to add fields to stock.scrap """
    _inherit = "stock.scrap"

    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template',related='product_id.product_tmpl_id',
        help="Corresponding product of the variant")
    bill_of_material_id = fields.Many2one(
        'mrp.bom',
        domain="[('product_tmpl_id', '=',product_tmpl_id)]",
        string="Bill of Material",
        help="Field to specify sequence bill of material")
    typ_of_reuse = fields.Selection(
        [('none', 'None'), ('dismantle', 'Dismantle')],
        default="none", help="Field to specify type of scrap",
        string="Type of Operation")
    state_management = fields.Selection(
        [('none', 'None'), ('dismantled', 'Dismantled')],
        string="State", default="none",
        help="Field to specify type of scrap management")
