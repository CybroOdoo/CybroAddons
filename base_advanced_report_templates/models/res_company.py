# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
    """
    Extends the  res.company to add default report layout fields for different
    modules. These fields allow specifying the default report layout for
    sales, purchases, accounts, and stock related documents.
    """
    _inherit = 'res.company'

    sale_document_layout_id = fields.Many2one("doc.layout",
                                              string="Sale",
                                              help="Default report layout "
                                                   "for sales")
    purchase_document_layout_id = fields.Many2one("doc.layout",
                                                  string="Purchase",
                                                  help="Default report "
                                                       "layout for purchases")
    account_document_layout_id = fields.Many2one("doc.layout",
                                                 string="Account",
                                                 help="Default report layout"
                                                      "for accounts")
    stock_document_layout_id = fields.Many2one("doc.layout",
                                               string="Stock",
                                               help="Default report layout "
                                                    "for stock")
