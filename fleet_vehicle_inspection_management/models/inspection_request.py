# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohamed Muzammil VP(odoo@cybrosys.com)
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
###############################################################################
from datetime import timedelta
from odoo import api, fields, models


class InspectionRequests(models.Model):
    """Create inspection requests"""
    _name = 'inspection.request'
    _description = 'Inspection Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        readonly=True, help='Inspection Request name',
        string='Inspection Request name')
    inspection_id = fields.Many2one(
        'vehicle.inspection', required=True, help='Select Vehicle Inspection',
        string='Select Vehicle Inspection')
    vehicle_id = fields.Many2one(
        'fleet.vehicle', string='Vehicle', required=True,
        help='Select Vehicle for inspection')
    vehicle_model_id = fields.Many2one(
        'fleet.vehicle.model', string='Model', related="vehicle_id.model_id",
        help='Vehicle model', store=True)
    license_plate = fields.Char(
        string='License Plate', readonly=False,
        related="vehicle_id.license_plate", help='vehicle license plate')
    date_create = fields.Date(
        default=lambda self: fields.Date.today(),
        string='Inspection Create Date', help='Inspection Create Date',)
    inspection_date = fields.Date(
        default=lambda self: fields.Date.today(), string='Inspection Date',
        help='Vehicle inspection date',)
    user_id = fields.Many2one(
        'res.users', string='Inspection Supervisor', readonly=False,
        related='inspection_id.user_id', help='Inspection supervisor')
    company_id = fields.Many2one(
        'res.company', string='Company', help='Company',
        default=lambda self: self.env.company)
    image_128 = fields.Image(
        related='vehicle_model_id.image_128', help='Vehicle Image',
        string='Image')
    inspection_result = fields.Char(
        string='Inspection Result', help='Vehicle inspection result')
    internal_note = fields.Html(string='Internal Note', help='Internal note')
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('new', 'New'),
                   ('inspection_started', 'Inspection Started'),
                   ('inspection_finished', 'Inspection Finished')],
        default='draft', copy=False, tracking=True,
        help='Status of Inspection', string='Status of Inspection')
    inspection_image_ids = fields.One2many(
        'inspection.image', 'inspection_req_id',
        help='Add Inspection Images', string='Add Inspection Images')
    inspection_line_reference_id = fields.Many2one(
        'inspection.request',
        string='Inspection Reference', help='Inspection Line')
    service_reference_id = fields.Many2one(
        'inspection.request', string='Service Reference',
        help='Service Reference')
    service_active = fields.Boolean(
        string='Service active', default=False,
        help='Active Service smart button', compute='_compute_service_active')
    fleet_active = fields.Boolean(
        string='Service active', default=False,
        help='Active Service smart button', compute='_compute_fleet_active')

    @api.model
    def create(self, vals):
        """Generate vehicle inspection sequence"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'inspection.request') or 'New'
        return super(InspectionRequests, self, ).create(vals)

    @api.depends('service_active')
    def _compute_service_active(self):
        """Checking if any service is created or not"""
        service_count = self.env['fleet.service.inspection'].search_count([
            ('inspection_reference_id', '=', self.id)])
        if service_count != 0:
            self.service_active = True
        else:
            self.service_active = False

    @api.depends('fleet_active')
    def _compute_fleet_active(self):
        """Checking that vehicle is chosen or not"""
        if self.vehicle_id:
            self.fleet_active = True
        else:
            self.fleet_active = False

    def action_confirm_inspection(self):
        """Button to confirm inspection request"""
        self.write({'state': 'new'})
        inspection_request_line = self.env['inspection.request.line'].search([
            ('inspection_request_reference_id', '=', self.id)
        ])
        if not inspection_request_line:
            self.env['inspection.request.line'].create({
                'fleet_vehicle_id': self.vehicle_id.id,
                'description': self.inspection_id.name,
                'inspection_id': self.inspection_id.id,
                'inspection_period': self.inspection_id.inspection_period,
                'reminder_notification':
                    self.inspection_id.reminder_notification_days,
                'user_id': self.user_id,
                'next_inspection_date': self.inspection_date,
            })

    def action_print_report(self):
        """ Print pdf report"""
        images = []
        for rec in self.inspection_image_ids:
            images.append(rec.image)
        data = {
            'logo': self.vehicle_id.model_id.image_128,
            'vehicle_model_id': self.vehicle_id.model_id.name,
            'records': self.read(),
            'license_plate': self.vehicle_id.license_plate,
            'user_id': self.user_id.name,
            'images': images}
        return self.env.ref(
            'fleet_vehicle_inspection_management.'
            'action_report_vehicle_inspection').report_action(self, data=data)

    def action_start_inspection(self):
        """Button to start vehicle inspection"""
        self.write({'state': 'inspection_started'})

    def action_finish_inspection(self):
        """Button to make inspection finished"""
        self.write({'state': 'inspection_finished'})

    def action_create_service(self):
        """Opens wizard to create service"""
        if not self.service_reference_id:
            service_id = self.env['fleet.service.inspection'].create({
                'inspection_reference_id': self.id,
                'vehicle_id': self.vehicle_id.id})
            self.service_reference_id = service_id.id
        return {
            'name': 'Create Service',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.service.inspection',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.service_reference_id.id}

    def action_create_inspection_request(self):
        """Automatically create inspection request and send reminder email"""
        for lines in self.env['inspection.request.line'].search([]):
            reminder_day = lines.next_inspection_date - timedelta(
                days=lines.reminder_notification)
            if reminder_day == fields.Date.today():
                self.write({'state': 'new'})
                lines.inspection_request_reference_id = self.inspection_line_reference_id.id
                next_inspection = lines.next_inspection_date + timedelta(
                    days=lines.inspection_period)
                lines.last_inspection_date = lines.next_inspection_date
                lines.next_inspection_date = next_inspection
                mail_template_id = self.env.ref(
                    'fleet_vehicle_inspection_management.'
                    'vehicle_inspection_reminder_email_template')
                mail_template_id.send_mail(
                    self.inspection_line_reference_id.id)

    def get_vehicle_service(self):
        """Vehicle service smart button"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vehicle Service log',
            'view_mode': 'tree,form',
            'context': {'create': False},
            'res_model': 'vehicle.service.log',
            'domain': [('service_reference_id', '=', self.env[
                'fleet.service.inspection'].search(
                [('inspection_reference_id', '=', self.id)]).id)]}

    def get_fleet_vehicle(self):
        """Fleet vehicle smart button"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fleet Vehicle',
            'view_mode': 'tree,form',
            'res_model': 'fleet.vehicle',
            'domain': [('id', '=', self.vehicle_id.id)]}
