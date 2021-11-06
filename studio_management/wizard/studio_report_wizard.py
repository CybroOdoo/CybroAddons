# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api


class ReportWizard(models.TransientModel):
    _name = 'studio.report.wizard'

    date_from = fields.Datetime(string='From')
    date_to = fields.Datetime(string='To')
    customer_id = fields.Many2one('res.partner', string='Customer')

    @api.multi
    def print_reports(self):
        if self._context is None:
            context = {}
        data = self.read()[0]
        datas = {
            'ids': self._context.get('active_ids', []),
            'model': 'studio.report.wizard',
            'form': data,
        }
        datas['form']['active_ids'] = self._context.get('active_ids', False)
        return self.env['report'].get_action(self, 'studio_management.report_digital_studio', data=datas)
