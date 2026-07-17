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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class FoPropertyCounter(models.Model):
    """
    Manages the property brought into the office by employees.
    Tracks belongings taken in and out of the office premises.
    """
    _name = 'fo.property.counter'
    _inherit = 'mail.thread'
    _description = 'Property Counter'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  required=True,
                                  help="Select the owner of the property")
    date = fields.Date(string="Date", required=True,
                       help='The date in which property collected')
    belonging_ids = fields.One2many('fo.belongings',
                                    'property_counter_id',
                                    string="Personal Belongings", copy=False,
                                    help='Personal Belongings of visitor')
    state = fields.Selection([('draft', 'Draft'),
                              ('taken_in', 'Taken In'),
                              ('taken_out', 'Taken out'),
                              ('cancel', 'Cancelled')],
                             tracking=True, default='draft',
                             help='If the employee gives the belongings to the '
                                  'company change state to ""Taken In"" when '
                                  'he/she leave office change the state to '
                                  '""Taken out""')

    def action_cancel(self):
        """
        Cancel the property counter record.
        Changes the state to 'cancel'.
        """
        self.state = "cancel"

    def action_taken_in(self):
        """
        Action to take in the property.
        Validates that all belongings have a count and sets state to 'taken_in'.
        """
        count = 0
        number = 0
        for data in self.belonging_ids:
            if not data.property_count:
                raise UserError(_('Please Add the Count.'))
            if data.permission == '1':
                count += 1
            number = data.number
        if number == count:
            raise UserError(_('No property can be taken in.'))
        else:
            self.state = 'taken_in'

    def action_taken_out(self):
        """
        Action when taking out the property.
        Changes the state to 'taken_out'.
        """
        self.state = "taken_out"


class FoBelongings(models.Model):
    """
    Stores details of specific property/belonging items brought to the office.
    Linked to either a visit or a property counter record.
    """
    _name = 'fo.belongings'
    _description = 'Belongings'

    property_name = fields.Char(string="Property",
                                help='The name of the Property')
    property_count = fields.Char(string="Count", help='Count of property')
    number = fields.Integer(compute='_compute_number', store=True, string="Sl",
                            help='Serial number')
    visit_id = fields.Many2one('fo.visit', string="Belongings",
                               help='The Visitors to the Office')
    property_counter_id = fields.Many2one('fo.property.counter',
                                          string="Belongings")
    permission = fields.Selection([('0', 'Allowed'),
                                   ('1', 'Not Allowed'),
                                   ('2', 'Allowed With Permission'),
                                   ], string='Permission', required=True,
                                  index=True, default='0', tracking=True,
                                  help='The permissions for the belongings')

    @api.depends('visit_id', 'property_counter_id')
    def _compute_number(self):
        """
        Compute sequential line numbers for belongings within a visit or property counter.
        """
        for visit in self.mapped('visit_id'):
            number = 1
            for line in visit.belonging_ids:
                line.number = number
                number += 1
        for visit in self.mapped('property_counter_id'):
            number = 1
            for line in visit.belonging_ids:
                line.number = number
                number += 1
