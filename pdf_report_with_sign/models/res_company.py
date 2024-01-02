# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
from odoo import api, fields, models


class ResCompany(models.Model):
    """Inherits res company for introduce signature in pdf reports"""
    _inherit = 'res.company'

    signature = fields.Binary(string='Signature',
                              help='Attach the signature here')
    signed_user_id = fields.Many2one('res.users', string='Signed By',
                                     help='Signed by whom')
    job_id = fields.Many2one('hr.job', string='Designation',
                             compute='_compute_job_id',
                             help='Designation of signed person')
    signed_time = fields.Datetime(string='Signed On', help='Signed date',
                                  default=fields.Datetime.now())

    @api.depends('signed_user_id')
    def _compute_job_id(self):
        """The job position of the signed person"""
        for company in self:
            company.job_id = False
            if company.signed_user_id:
                hr_employee = self.env['hr.employee'].search(
                    [('user_id', '=', company.signed_user_id.id)], limit=1)
                company.job_id = hr_employee.job_id.id
