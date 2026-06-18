# -*- coding: utf-8 -*-
################################################################################
#
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    """Inherit the model hr.employee. for showing the employee id in the
    employee view """
    _inherit = 'hr.employee'

    device_id_no = fields.Char(string='Biometric Device ID',
                               help="Give the biometric device id")

    @api.constrains('device_id_no')
    def _check_device_id_no(self):
        """Validate that biometric device IDs are unique per employee."""
        for employee in self:
            if employee.device_id_no:
                duplicate = self.search([
                    ('device_id_no', '=', employee.device_id_no),
                    ('id', '!=', employee.id)
                ])
                if duplicate:
                    raise ValidationError(
                        _("%s has already been used by another user") % employee.device_id_no
                    )
