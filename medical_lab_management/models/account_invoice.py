# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anusha P P @ cybrosys and Niyas Raphy @ cybrosys(odoo@cybrosys.com)
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

from odoo import models, fields, api


class LabRequestInvoices(models.Model):
    _inherit = 'account.move'

    is_lab_invoice = fields.Boolean(string="Is Lab Invoice")
    lab_request = fields.Many2one('lab.appointment', string="Lab Appointment", help="Source Document")

    def action_invoice_paid(self):
        res = super(LabRequestInvoices, self).action_invoice_paid()
        lab_app_obj = self.env['lab.appointment'].search([('id', '=', self.lab_request.id)])
        for obj in lab_app_obj:
            obj.write({'state': 'invoiced'})
        return res
