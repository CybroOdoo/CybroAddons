# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: odoo@cybrosys.com
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

from odoo import models


class MassConfirmPayslip(models.TransientModel):
    _name = 'payslip.confirm'
    _description = 'Mass Confirm Payslip'

    def confirm_payslip(self):
        """Mass Confirmation of Payslip"""
        context = self._context
        record_ids = context.get('active_ids', [])
        for each in record_ids:
            payslip_id = self.env['hr.payslip'].search([('id', '=', each),
                                                        ('state', 'not in', ['cancel', 'done'])])
            if payslip_id:
                payslip_id.action_payslip_done()
