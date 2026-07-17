# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
    """
    Manages the lifecycle of a visitor's visit to the office.
    Includes check-in, check-out, and purpose of visit.
    """
    _name = 'fo.visit'
    _inherit = 'mail.thread'
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
                                    help='Add the belongings details of '
                                         'employee here.')
    check_in_date = fields.Datetime(string="Check In", readonly=True,
                                    help='Visitor check in time automatically '
                                         'fills when he checked in to the '
                                         'office')
    check_out_date = fields.Datetime(string="Check Out", readonly=True,
                                     help='Visitor check out time automatically '
                                          'fills when he checked out from '
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
        """
        Generate a unique sequence number for each new visit record.
        """
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'fo.visit') or _('New')
        return super().create(vals_list)

    def action_cancel(self):
        """
        Cancel the visitor record.
        Sets the state to 'cancel'.
        """
        self.state = "cancel"

    def action_check_in(self):
        """
        Record visitor check-in.
        Sets state to 'check_in' and records current timestamp.
        """
        self.state = "check_in"
        self.check_in_date = datetime.datetime.now()

    def action_check_out(self):
        """
        Record visitor check-out.
        Sets state to 'check_out' and records current timestamp.
        """
        self.state = "check_out"
        self.check_out_date = datetime.datetime.now()

    @api.onchange('visitor_id')
    def _onchange_visitor_id(self):
        """
        Autofill phone and email fields when a visitor is selected.
        """
        if self.visitor_id:
            if self.visitor_id.phone:
                self.phone = self.visitor_id.phone
            if self.visitor_id.email:
                self.email = self.visitor_id.email

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """
        Autofill department field based on the selected employee.
        """
        if self.employee_id:
            self.department_id = self.employee_id.department_id


class FoPurpose(models.Model):
    """
    Defines the possible purposes or reasons for a visitor to visit the office.
    """
    _name = 'fo.purpose'
    _description = 'Visit Purpose'

    name = fields.Char(string='Purpose', required=True,
                       help='Meeting purpose in short term.eg:Meeting.')
    description = fields.Text(string='Description Of Purpose',
                              help='Description for the Purpose.')
