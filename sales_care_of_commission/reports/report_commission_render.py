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

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class ReportCareOfCommission(models.AbstractModel):
    _name = 'report.sales_care_of_commission.report_commission'

    @api.model
    def _get_report_values(self, docids, data=None):
        filters = data['form']
        domain = [('care_of_partner_id', '!=', None), ('state', 'not in', ('draft', 'cancel')),
                  ('company_id', '=', filters['company_id'][0])]
        if filters['date_from']:
            domain.append(('date_invoice', '>=', filters['date_from']))
        if filters['date_to']:
            domain.append(('date_invoice', '<=', filters['date_to']))
        if filters['partner_id']:
            domain.append(('care_of_partner_id', '=', filters['partner_id'][0]))
        if filters['customer_id']:
            domain.append(('partner_id', '=', filters['customer_id'][0]))
        invoices = self.env['account.invoice'].search(domain)
        care_of_partner_ids = invoices.mapped('care_of_partner_id')
        docs = dict()
        for p in care_of_partner_ids:
            partner_invoices = invoices.filtered(lambda inv: inv.care_of_partner_id == p)
            docs[p.id] = {
                'name': p.name,
                'invoices': partner_invoices,
                'sum_untax': sum(a.amount_untaxed for a in partner_invoices),
                'sum_comm': sum(a.care_of_commission for a in partner_invoices)
            }
        if not invoices:
            raise ValidationError(_('No matching data fund. Please change filter parameters and try.'))
        return {
            'doc_ids': docids,
            'doc_model': data['model'],
            'data': data['form'],
            'docs': docs,
            'print_time': fields.Datetime.now(),
            }
