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

from odoo import fields, models, api


class AccountPrintJournal(models.TransientModel):
    _name = "careof.print.commission"
    _description = "Account Print Care of Commission"

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    company_id = fields.Many2one('res.company', string='Company', required=True, default=_get_company,
                                 help='The company this user is currently working for.',
                                 context={'user_preference': True})
    partner_id = fields.Many2one('res.partner', string='Partner', required=False)
    customer_id = fields.Many2one('res.partner', string='Invoice Customer', required=False)
    date_from = fields.Date(string='Start Date', default=fields.Date().today().replace(day=1))
    date_to = fields.Date(string='End Date')

    @api.onchange('company_id')
    def onchange_company_id(self):
        return {'domain': {'partner_id': [('company_id', '=', self.company_id.id)]}}

    @api.multi
    def print_report(self):
        active_ids = self.env.context.get('active_ids', [])
        datas = {
            'ids': active_ids,
            'model': 'account.invoice',
            'form': self.read()[0]
        }
        return self.env.ref('sales_care_of_commission.action_report_commission').report_action([], data=datas)
