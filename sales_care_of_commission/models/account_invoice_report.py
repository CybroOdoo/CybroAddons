# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akhilesh N S (odoo@cybrosys.com)
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

from odoo import models, fields


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    care_of_partner_id = fields.Many2one('res.partner', string='Care Of (C/O)', readonly=True)
    care_of_percentage = fields.Float(string='C/O Commission Percentage', readonly=True)
    care_of_commission = fields.Monetary(string='C/O Commission Amount', readonly=True)

    def _select(self):
        return super(AccountInvoiceReport, self)._select() +\
               ", sub.care_of_partner_id as care_of_partner_id" +\
               ", sub.care_of_percentage as care_of_percentage" + \
               ", sub.care_of_commission as care_of_commission"

    def _sub_select(self):
        return super(AccountInvoiceReport, self)._sub_select() +\
               ", ai.care_of_partner_id as care_of_partner_id" +\
               ", ai.care_of_percentage as care_of_percentage" + \
               ", ai.care_of_commission as care_of_commission"

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + \
               ", ai.care_of_partner_id" + ", ai.care_of_percentage" + \
               ", ai.care_of_commission"
