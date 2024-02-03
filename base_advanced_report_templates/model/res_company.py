# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import fields, models


class ResCompany(models.Model):
    """Adding the layouts in company"""
    _inherit = 'res.company'

    sale_document_layout_id = fields.Many2one("doc.layout",
                                              string="Sale",
                                              help="Select the required layout "
                                                   "for Sales")
    purchase_document_layout_id = fields.Many2one("doc.layout",
                                                  string="Purchase",
                                                  help="Select the required "
                                                       "layout for Purchase")
    account_document_layout_id = fields.Many2one("doc.layout",
                                                 string="Account",
                                                 help="Select the required "
                                                      "layout for Invoice")
    stock_document_layout_id = fields.Many2one("doc.layout",
                                               string="Stock",
                                               help="Select the required "
                                                    "layout for Delivery")
