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
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MachineRepair(models.Model):
    """This model is used to manage machine repair requests."""
    _name = 'machine.repair'
    _inherit = ['portal.mixin']
    _description = "Machine Repair"
    _rec_name = "repair_seq"

    name = fields.Char(help="Name of the repair request.", required=True)
    repair_seq = fields.Char(string='Repair Sequence', copy=False,
                             help="Unique sequence number assigned to each repair request.",
                             readonly=True, index=True,
                             default=lambda self: 'New')
    customer_id = fields.Many2one('res.partner',
                                  help="The customer who requested the repair.",
                                  required=True)
    customer_email = fields.Char(string='Customer E-mail',
                                 related="customer_id.email",
                                 help="Email address of the customer.")
    phone = fields.Char(string='Phone', related="customer_id.phone",
                        help="Phone number of the customer.")
    repairing_reason = fields.Char(help="The reason why the repair is needed.")
    machine_brand = fields.Char(help="The brand of the machine being repaired.")
    machine_model = fields.Char(string="Model",
                                help="The specific model of the machine.")
    manufacturing_year = fields.Date(help="The year in which the machine was manufactured.")
    priority = fields.Selection([('high', 'High'), ('normal', 'Normal'), ('low', 'Low')],
                                help="Priority level of the repair request.",
                                required=True)
    repair_detail = fields.Text(string='Repair Reason in Detail',
                                help="Detailed description of the repair issue.",
                                required=True)
    technician_id = fields.Many2one('hr.employee',
                                    help="The technician assigned to perform the repair.")
    technician_member_ids = fields.Many2many('hr.employee',
                                             string="Technical Members",
                                             help="Additional technical members assisting in the repair.")
    email = fields.Char('Email', related='technician_id.work_email',
                        help="Email address of the assigned technician.")
    company_id = fields.Many2one('res.company',
                                 help="The company responsible for the repair.",
                                 default=lambda self: self.env.company)
    project_id = fields.Many2one('project.project',
                                 help="Project associated with this repair request.")
    department_id = fields.Many2one('hr.department',
                                    help="The department responsible for handling the repair.")
    repair_req_date = fields.Date(string='Repair Date',
                                  help="The date on which the repair was requested.")
    closing_date = fields.Date(help="The date when the repair was completed and closed.")
    repairing_duration = fields.Float(help="Total time taken for the repair process (in hours).")
    is_repaired = fields.Boolean(help="Indicates whether the repair request has been successfully completed.")
    machine_id = fields.Many2one('product.product',
                                 help="The machine that needs to be repaired.",
                                 domain=[('is_machine', '=', True)])
    machine_categ_id = fields.Many2one('product.category',
                                       string='Machine Category',
                                       help="The category to which the machine belongs.")
    color = fields.Char(help="The color of the machine.")
    damage = fields.Char(help="Description of the damage on the machine.")
    warranty = fields.Boolean(help="Indicates whether the machine is under warranty.")
    warranty_exp_date = fields.Date(string="Warranty Expiration Date",
                                    help="The date when the machine's warranty expires.")
    authority_name = fields.Char(help="Name of the authority responsible for approving the repair.")
    service_id = fields.Many2one('machine.service',
                                 help="The type of service required for the machine.")
    customer_rating = fields.Char(help="Customer's rating for the repair service.")
    customer_comments = fields.Char(help="Additional feedback or comments provided by the customer.")
    extra_info = fields.Html(string="Information",
                             help="Additional details or documentation related to the repair.")
    repair_team_id = fields.Many2one('repair.team',
                                     help="The team assigned to carry out the repair.")
    nature_of_service_id = fields.Many2one('machine.service',
                                           string="Nature of Service",
                                           help="Defines the type of service the machine requires.")
    repair_type_ids = fields.Many2many('machine.service.type',
                                      string="Repair Types",
                                      help="Different types of repairs applicable to this machine.")
    problem = fields.Char(help="A brief description of the issue faced by the machine.")
    note = fields.Html(help="Additional notes regarding the repair process.")
    state = fields.Selection(string='Status', required=True, readonly=True,
                             copy=False, selection=[('new', 'New'),
                                                    ('assigned', 'Assigned'),
                                                    ('closed', 'Closed'),
                                                    ('send', 'Mail Sent'),
                                                    ('reopen', 'Reopened'), ],
                             default='new',
                             help="Current status of the repair request.")
    image1 = fields.Binary(string='Image 1',
                           help="First image of the machine before or after repair.")
    image2 = fields.Binary(string='Image 2',
                           help="Second image of the machine before or after repair.")
    image3 = fields.Binary(string='Image 3',
                           help="Third image of the machine before or after repair.")
    image4 = fields.Binary(string='Image 4',
                           help="Fourth image of the machine before or after repair.")
    image5 = fields.Binary(string='Image 5',
                           help="Fifth image of the machine before or after repair.")
    timesheet_ids = fields.One2many('repair.timesheet', 'inverse_id',
                                    help="Records the working hours spent on this repair.")
    consume_part_ids = fields.One2many('machine.consume', 'consume_id',
                                       string="Consumed Parts",
                                       help="List of machine parts consumed during the repair.")
    is_team_assigned = fields.Boolean(help="Indicates whether a repair team has been assigned to this repair request.")
    diagnosis_ids = fields.One2many('machine.diagnosis','machine_repair_ref_id',
                                    help="List of diagnosis records related to this machine repair.")
    workorder_ids = fields.One2many('machine.workorder','repair_id',
                                    help="List of work orders related to this machine repair.")

    def _compute_access_url(self):
        """Set the portal URL of each repair request."""
        res = super()._compute_access_url()
        for repair in self:
            repair.access_url = '/my/repair/%s' % repair.id
        return res

    @api.constrains('repair_req_date', 'closing_date')
    def _check_date_order(self):
        """Ensure that 'closing_date' is not earlier than 'repair_req_date'.

        :raises ValidationError: if 'closing_date' is earlier than
            'repair_req_date'.
        """
        for record in self:
            if (record.repair_req_date and record.closing_date
                    and record.closing_date < record.repair_req_date):
                raise ValidationError(self.env._(
                    "Closing Date cannot be earlier than Repair Date."))

    @api.model_create_multi
    def create(self, vals_list):
        """Generate the repair sequence on create."""
        # Work on copies so the caller's dictionaries are never modified.
        vals_list = [dict(vals) for vals in vals_list]
        for vals in vals_list:
            if vals.get('repair_seq', 'New') in ('New', ''):
                vals['repair_seq'] = self.env['ir.sequence'].next_by_code(
                    'machine.repair') or 'New'
        return super().create(vals_list)

    @api.onchange('repair_team_id')
    def onchange_repair_team(self):
        """Fill the technical members from the members of the selected team."""
        val = self.env['repair.team'].search(
            [('id', '=', self.repair_team_id.id)]).mapped('member_ids').mapped('member_id').ids
        self.technician_member_ids = val

    def action_create_diagnosis(self):
        """Create a diagnosis from the repair request."""
        self.ensure_one()
        if not self.closing_date:
            raise ValidationError(self.env._("Closing Date cannot be empty."))
        diagnosis = self.env['machine.diagnosis'].create({
            'machine_repair_ref_id': self.id,
            'project_id': self.project_id.id,
            'customer_id': self.customer_id.id,
            'deadline': self.closing_date,
        })
        return {'res_model': 'machine.diagnosis',
                'type': 'ir.actions.act_window',
                'res_id': diagnosis.id,
                'view_mode': 'form',
                'target': 'current',
                'context': "{'create': False ,}"}

    def action_create_work_order(self):
        """Create a work order from the repair request."""
        self.ensure_one()
        work_order = self.env['machine.workorder'].create({
            'repair_id': self.id,
            'customer_id': self.customer_id.id,
            'date': self.repair_req_date,
            'priority': self.priority,
            'work_order_id':self.nature_of_service_id.id,
        })
        return {'res_model': 'machine.workorder',
                'type': 'ir.actions.act_window',
                'res_id': work_order.id,
                'view_mode': 'form',
                'target': 'current',
                'context': "{'create': False ,}"}

    def action_reopen(self):
        """Reopen the repair request."""
        self.ensure_one()
        self.state = 'reopen'

    def action_close_repairing(self):
        """Close the repair request."""
        self.ensure_one()
        self.state = 'closed'

    def action_assign_teams(self):
        """Assign the repair request to its repair team."""
        self.ensure_one()
        if self.repair_team_id:
            self.repair_team_id.write({'repair_work_ids': [(4, self.id)],})
            self.is_team_assigned = True
            self.state = 'assigned'
        else:
            self.state = 'new'
            raise ValidationError(
                self.env._("No repair team is specified."))

    def action_send_email(self):
        """Email the customer that the repair request is closed."""
        self.ensure_one()
        template_id = self.env.ref('base_machine_repair_management.repair_request_close_email_template').id
        self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)
        self.state = "send"

    def get_machine_diagnosis(self):
        """Opens a window action displaying all diagnosis records related to
        the current machine repair."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Machine Diagnosis'),
            'view_mode': 'list,form',
            'res_model': 'machine.diagnosis',
            'domain': [('machine_repair_ref_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def get_machine_workorder(self):
        """Opens a window action displaying all work order records related to
        the current machine repair."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Machine Work Orders'),
            'view_mode': 'list,form',
            'res_model': 'machine.workorder',
            'domain': [('repair_id', '=', self.id)],
            'context': "{'create': False}"
        }
