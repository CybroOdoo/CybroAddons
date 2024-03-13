# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
import datetime
from odoo import api, fields, models, _


class FoVisit(models.Model):
    """Manages the details of visitors to the Office"""
    _name = 'fo.visit'
    _inherit = ['mail.thread']
    _description = 'Visit'

    name = fields.Char(string="Sequence", default=lambda self: _('New'),
                       help='Sequence number for the visiting')
    visitor_id = fields.Many2one("fo.visitor", string='Visitor',
                                 help='Select the visitor')
    phone = fields.Char(string="Phone", required=True,
                        help='Phone number of the visitor')
    email = fields.Char(string="Email", required=True,
                        help='Email of the Visitor')
    reason_ids = fields.Many2many('fo.purpose', string='Purpose Of Visit',
                                  required=True,
                                  help='Enter the reason for visit')
    belonging_ids = fields.One2many('fo.belongings',
                                    'visit_id',
                                    string="Personal Belongings",
                                    help='Add the belongings details of'
                                         'employee here.')
    check_in_date = fields.Datetime(string="Check In Time", readonly=True,
                                    help='Visitor check in time automatically'
                                         'fills when he checked in to the'
                                         'office')
    check_out_date = fields.Datetime(string="Check Out Time", readonly=True,
                                     help='Visitor check out time automatically'
                                          'fills when he checked out from'
                                          'office')
    employee_id = fields.Many2one('hr.employee', string="Meeting With")
    department_id = fields.Many2one('hr.department', string="Department")
    state = fields.Selection([('draft', 'Draft'),
                              ('check_in', 'Checked In'),
                              ('check_out', 'Checked Out'),
                              ('cancel', 'Cancelled'),
                              ], tracking=True, default='draft',
                             help='Status of the visitor')

    @api.model_create_multi
    def create(self, vals_list):
        """Creating sequence"""
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'fo.visit') or _('New')
        return super().create(vals_list)

    def action_cancel(self):
        """Action for cancelling the visitor"""
        self.state = "cancel"

    def action_check_in(self):
        """Action for checking in the visitor"""
        self.state = "check_in"
        self.check_in_date = datetime.datetime.now()

    def action_check_out(self):
        """Action for checking out the visitor"""
        self.state = "check_out"
        self.check_out_date = datetime.datetime.now()

    @api.onchange('visitor_id')
    def _onchange_visitor_id(self):
        """Selecting the"""
        if self.visitor_id:
            if self.visitor_id.phone:
                self.phone = self.visitor_id.phone
            if self.visitor_id.email:
                self.email = self.visitor_id.email

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id


class VisitPurpose(models.Model):
    _name = 'fo.purpose'
    _description = 'Visit Purpose'

    name = fields.Char(string='Purpose', required=True,
                       help='Meeting purpose in short term.eg:Meeting.')
    description = fields.Text(string='Description Of Purpose',
                              help='Description for the Purpose.')
