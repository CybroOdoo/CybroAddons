# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MaintenanceRequest(models.Model):
    """Model that handles the maintenance requests"""

    _inherit = ['maintenance.request', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'sequence'
    _description = "Maintenance Request"

    is_hotel = fields.Boolean(string="Is Hotel Maintenance", default=False)

    sequence = fields.Char(readonly=True, string="Sequence", copy=False,
                           default='New', help='Sequence number for'
                                               ' identifying maintenance'
                                               ' request')
    date = fields.Date(string="Date", help="Date of maintenance request",
                       default=fields.Date.today)
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('team_leader_approve',
                                         'Waiting For User Assign'),
                                        ('pending', 'Waiting For User To '
                                                    'Accept'),
                                        ('ongoing', 'Ongoing'),
                                        ('support', 'Waiting For Support'),
                                        ('done', 'Done'),
                                        ('verify', 'Pending For Verify'),
                                        ('cancel', 'Canceled')],
                             default='draft', string="State",
                             help="State of maintenance request",
                             tracking=True)
    team_id = fields.Many2one('maintenance.team',
                              string='Maintenance Team',
                              help="Team for which this request is assigned",
                              tracking=True)
    team_head_id = fields.Many2one('res.users',
                                   related='team_id.user_id',
                                   string='Team Leader',
                                   help="Head of the maintenance team")
    assigned_user_id = fields.Many2one('res.users',
                                       string='Assigned User',
                                       tracking=True,
                                       help="User to whom the request is "
                                            "assigned")
    type = fields.Selection(selection=[('room', 'Room'),
                                       ('vehicle', 'Vehicle'),
                                       ('hotel', 'Hotel'),
                                       ('cleaning', 'Cleaning')], string="Type",
                            help="The type for which the request is creating",
                            tracking=True)
    room_maintenance_ids = fields.Many2many('hotel.room',
                                            string="Room Maintenance",
                                            help="Choose Room Maintenance")
    hotel_maintenance = fields.Char(string='Hotel Maintenance',
                                    help="This is the Hotel Maintenance")
    cleaning_maintenance = fields.Char(string='Cleaning Maintenance',
                                       help="This is the Cleaning Maintenance")
    vehicle_maintenance_id = fields.Many2one('fleet.vehicle.model',
                                             string="Vehicle",
                                             help="Choose Vehicle")
    support_team_ids = fields.Many2many('res.users',
                                        relation='maintenance_request_support_team_rel',
                                        column1='request_id',
                                        column2='user_id',
                                        string="Support Team",
                                        help="Choose Support Team")
    support_reason = fields.Char(string='Support',
                                 help="Reason for adding Support")
    remarks = fields.Char(string='Remarks', help="Add Remarks")
    domain_partner_ids = fields.Many2many('res.users',
                                          string="Partner",
                                          compute='_compute_domain_partner_ids',
                                          help="For filtering Users")

    @api.model_create_multi
    def create(self, vals_list):
        """Sequence Generation"""
        for vals in vals_list:
            if vals.get('sequence', 'New') == 'New':
                vals['sequence'] = self.env['ir.sequence'].next_by_code(
                    'maintenance.request')
            if not vals.get('name'):
                vals['name'] = vals['sequence']
        return super().create(vals_list)

    @api.depends('team_id')
    def _compute_domain_partner_ids(self):
        """Function for filtering the maintenance team user"""
        for record in self:
            record.domain_partner_ids = record.team_id.member_ids

    def action_assign_team(self):
        """Button action for changing the state to team_leader_approve"""
        if self.team_id:
            self.state = 'team_leader_approve'
        else:
            raise ValidationError(
                ("Please assign a Team"))

    def action_assign_user(self):
        """Button action for changing the state to pending"""
        if self.assigned_user_id:
            self.state = 'pending'
        else:
            raise ValidationError(
                ("Please assign a User"))

    def action_start(self):
        """Button action for changing the state to ongoing"""
        self.state = 'ongoing'

    def action_support(self):
        """Button action for changing the state to support"""
        if self.support_reason:
            self.state = 'support'
        else:
            raise ValidationError('Please enter the reason')

    def action_complete(self):
        """Button action for changing the state to verify"""
        if self.remarks:
            self.state = 'verify'
        else:
            raise ValidationError('Please Add remark')

    def action_assign_support(self):
        """Button action for changing the state to ongoing"""
        if self.support_team_ids:
            self.state = 'ongoing'
        else:
            raise ValidationError('Please choose support')

    def action_verify(self):
        """Button action for changing the state to done"""
        self.state = 'done'
        if self.vehicle_maintenance_id:
            self.vehicle_maintenance_id.status = 'available'