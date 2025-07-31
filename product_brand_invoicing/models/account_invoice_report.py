# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    brand_id = fields.Many2one('product.brand', string='Brand',
                               help="Product Brand")

    def _select(self) -> SQL:
        return SQL("%s, template.brand_id as brand_id", super()._select())

    def _group_by(self):
        """
        This method adds 'template.brand_id' to the existing 'template.categ_id' in
        the SQL GROUP BY clause for the Account Invoice Report.
        :return: The extended SQL GROUP BY clause as a string.
        """
        res = super()._group_by()
        query = res.split('template.categ_id,', 1)
        res = query[0] + 'template.categ_id,template.brand_id,' + query[1]
        return res
