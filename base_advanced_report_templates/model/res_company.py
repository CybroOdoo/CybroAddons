# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import models, fields


class ResCompany(models.Model):
    """This model extends the 'res.company' model to include additional fields
    related to document layouts for sales, purchases, accounts, and stock.
"""
    _inherit = 'res.company'

    sale_document_layout_id = fields.Many2one("doc.layout",
                                              string="Sale", help="This field "
                                              "specifies the document layout "
                                              "associated with sales for the "
                                                                  "company."
                                              )
    purchase_document_layout_id = fields.Many2one("doc.layout",
                                                  string="Purchase", help="This"
                                                  "field specifies the document"
                                                  "layout associated with "
                                                  "purchases for the company."
                                                  )
    account_document_layout_id = fields.Many2one("doc.layout",
                                                 string="Account",
                                                 help="Document layout "
                                                 "associated with accounting"
                                                      " for the company."
                                                 )
    stock_document_layout_id = fields.Many2one("doc.layout",
                                               string="Stock", help="Document "
                                               "layout associated with stock"
                                               )
