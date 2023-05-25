# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
#    Version 3 (AGPL v3)
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
"""model for inspection requests """
from datetime import timedelta
from odoo import api, fields, models


class InspectionRequests(models.Model):
    """create inspection requests"""
    _name = 'inspection.request'
    _description = 'Inspection Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(readonly=True, store=True,
                       help='Inspection Request name',
                       string='Inspection Request name')
    inspection_id = fields.Many2one('vehicle.inspection', required=True,
                                    help='Select Vehicle Inspection',
                                    string='Select Vehicle Inspection')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle',
                                 help='Select Vehicle for inspection')
    vehicle_model_id = fields.Many2one('fleet.vehicle.model', string='Model',
                                       related="vehicle_id.model_id",
                                       readonly=False,
                                       store=True, help='Vehicle model')
    license_plate = fields.Char(string='License Plate',
                                related="vehicle_id.license_plate", store=True,
                                readonly=False, help='vehicle license plate')
    date_create = fields.Date(string='Inspection Create Date',
                              help='Inspection Create Date',
                              default=lambda self: fields.Date.today())
    inspection_date = fields.Date(string='Inspection Date',
                                  help='Vehicle inspection date',
                                  default=lambda self: fields.Date.today())
    user_id = fields.Many2one('res.users', string='Inspection Supervisor',
                              related='inspection_id.user_id', readonly=False,
                              store=True, help='Inspection supervisor')
    company_id = fields.Many2one('res.company', string='Company',
                                 help='Company',
                                 default=lambda self: self.env.company)
    image_128 = fields.Image(related='vehicle_model_id.image_128',
                             help='Vehicle Image', string='Image')
    inspection_result = fields.Char(string='Inspection Result',
                                    help='Vehicle inspection result')
    internal_note = fields.Html(string='Internal Note', help='Internal note')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('new', 'New'),
         ('inspection_started', 'Inspection Started'),
         ('inspection_finished', 'Inspection Finished'), ],
        default='draft', copy=False, required=True, tracking=True,
        help='Status of Inspection', string='Status of Inspection')
    inspection_image_ids = fields.One2many('inspection.images',
                                           'inspection_id',
                                           help='Add Inspection Images',
                                           string='Add Inspection Images')
    inspection_line_reference = fields.Integer(string='Inspection Reference',
                                               help='Inspection Line')
    service_reference = fields.Integer(string='Service Reference',
                                       help='Service Reference')
    service_active = fields.Boolean('Service active', default=False,
                                    help='Active Service smart button',
                                    compute='_compute_service_active')
    fleet_active = fields.Boolean('Service active', default=False,
                                  help='Active Service smart button',
                                  compute='_compute_fleet_active')

    @api.model
    def create(self, vals):
        """generate vehicle inspection sequence"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'inspection.request') or 'New'
        result = super(InspectionRequests, self, ).create(vals)
        return result

    @api.depends('service_active')
    def _compute_service_active(self):
        service_count = self.env['fleet.service.inspection'].search_count([
            ('inspection_reference', '=', self.id)])
        if service_count != 0:
            self.service_active = True
        else:
            self.service_active = False

    @api.depends('fleet_active')
    def _compute_fleet_active(self):
        if self.vehicle_id:
            self.fleet_active = True
        else:
            self.fleet_active = False

    def action_confirm_inspection(self):
        """button to confirm inspection request"""
        self.write({'state': 'new'})
        inspection_request_line = self.env['inspection.request.line'].search([
            ('inspection_request_reference', '=', self.id)
        ])
        if not inspection_request_line:
            self.env['inspection.request.line'].create({
                'fleet_vehicle_id': self.vehicle_id.id,
                'description': self.inspection_id.name,
                'inspection_id': self.inspection_id.id,
                'inspection_period': self.inspection_id.inspection_period,
                'reminder_notification': self.inspection_id.reminder_notification_days,
                'user_id': self.user_id,
                'next_inspection_date': self.inspection_date,
            })

    def action_print_report(self):
        """ print pdf report"""
        images = []
        for rec in self.inspection_image_ids:
            images.append(rec.image)
        inspection_request = self.env['inspection.request'].search([
            ('name', '=', self.name)
        ])
        data = {
            'logo': self.vehicle_id.model_id.image_128,
            'vehicle_model_id': self.vehicle_id.model_id.name,
            'records': self.read(),
            'license_plate': self.vehicle_id.license_plate,
            'user_id': inspection_request.user_id.name,
            'images': images,
        }
        return self.env.ref(
            'fleet_vehicle_inspection_management.action_report_vehicle_inspection').report_action(
            self, data=data)

    def action_start_inspection(self):
        """button to  start vehicle inspection"""
        self.write({'state': 'inspection_started'})

    def action_finish_inspection(self):
        """button to make inspection finished"""
        self.write({'state': 'inspection_finished'})

    def action_create_service(self):
        """opens wizard to create service"""
        if not self.service_reference:
            service_id = self.env['fleet.service.inspection'].create({
                'inspection_reference': self.id,
                'vehicle_id': self.vehicle_id.id,
            })
            self.service_reference = service_id
        return {
            'name': 'Create Service',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.service.inspection',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.service_reference,
        }

    def action_create_inspection_request(self):
        """automatically create inspection request and send reminder email"""

        vehicle_inspection_lines = self.env['inspection.request.line'].search(
            [])
        for lines in vehicle_inspection_lines:
            reminder_day = lines.next_inspection_date - timedelta(
                days=lines.reminder_notification)
            if reminder_day == fields.Date.today():
                inspection_line_id = self.env['inspection.request'].search([
                    ('inspection_line_reference', '=', lines.id)])
                if not inspection_line_id:
                    create_id = self.env['inspection.request'].create({
                        'inspection_id': lines.inspection_id.id,
                        'inspection_line_reference': lines.id,
                        'vehicle_id': lines.fleet_vehicle_id.id,
                        'vehicle_model_id': lines.fleet_vehicle_id.model_id.id,
                        'license_plate': lines.fleet_vehicle_id.license_plate,
                        'date_create': lines.create_date,
                        'inspection_date': lines.next_inspection_date,
                        'user_id': lines.user_id.id,
                        'company_id': self.env.company.id,
                        'image_128': lines.fleet_vehicle_id.model_id.image_128,
                    })
                    create_id.write({'state': 'new'})
                    lines.inspection_request_reference = create_id.id
                    next_inspection = lines.next_inspection_date + timedelta(
                        days=lines.inspection_period)
                    lines.last_inspection_date = lines.next_inspection_date
                    lines.next_inspection_date = next_inspection
                    mail_template_id = self.env.ref(
                        'fleet_vehicle_inspection_management.vehicle_inspection_reminder_email_template')
                    mail_template_id.send_mail(create_id.id)

    def get_vehicle_service(self):
        """vehicle service smart button"""
        service_id = self.env['fleet.service.inspection'].search([
            ('inspection_reference', '=', self.id)])
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vehicle Service log',
            'view_mode': 'tree,form',
            'context': {'create': False},
            'res_model': 'vehicle.service.log',
            'domain': [('service_reference', '=', service_id.id)],
        }

    def get_fleet_vehicle(self):
        """fleet vehicle smart button"""

        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fleet Vehicle',
            'view_mode': 'tree,form',
            'res_model': 'fleet.vehicle',
            'domain': [('id', '=', self.vehicle_id.id)],
        }
