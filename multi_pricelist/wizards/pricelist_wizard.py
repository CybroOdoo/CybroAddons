# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Raveena V (odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models


class PricelistWizard(models.TransientModel):
    """This class will create a new transient model for the price list wizard"""
    _name = 'pricelist.wizard'
    _rec_name = 'order_line_id'
    _description = 'Price list Wizard'

    order_line_id = fields.Many2one('sale.order.line',
                                    string="Order Line",
                                    help="Order line of the selected order")
    line_ids = fields.One2many('pricelist.wizard.line', 'wizard_id',
                               string="Price lists", help="Pricelist lines")


