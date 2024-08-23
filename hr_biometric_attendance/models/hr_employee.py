# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import fields, models, _


class HrEmployee(models.Model):
    """Inherit the model to add field"""
    _inherit = 'hr.employee'

    device_id_num = fields.Char(string='Biometric Device ID',
                                help="Give the biometric device id", copy=False)
    device_id = fields.Many2one('biometric.device.details', copy=False,
                                readonly=True,
                                help='The biometric device details')
    fingerprint_ids = fields.One2many('fingerprint.templates', 'employee_id',
                                      help='Store finger print templates of '
                                           'an employee')

    def action_biometric_device(self):
        """Server Action for Biometric Device which open a wizard with
        several options"""
        return {
            'type': 'ir.actions.act_window',
            'target': 'new',
            'name': _('Biometric Management'),
            'view_mode': 'form',
            'res_model': 'employee.biometric',
            'context': {'default_employee_id': self.id},
        }
