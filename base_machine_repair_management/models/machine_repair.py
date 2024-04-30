"""Machine Repair"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya B (odoo@cybrosys.com)
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


class MachineRepair(models.Model):
    """This is used for the machine repair management"""
    _name = 'machine.repair'
    _description = "Machine Repair"
    _rec_name = "repair_seq"

    name = fields.Char(string='Name', help="Name of the repair")
    repair_seq = fields.Char(string='Repair Sequence', required=True,
                             copy=False, help="Repair sequence",
                             readonly=True, index=True,
                             default=lambda self: 'New')
    customer_id = fields.Many2one('res.partner', string="Customer",
                                  help="Name of the customer", required=True)
    customer_email = fields.Char(string='Customer E-mail',
                                 related="customer_id.email",
                                 help="Email of the customer")
    phone = fields.Char(string='Phone', help="Customer phone number",
                        related="customer_id.phone")
    repairing_reason = fields.Char(string='Repairing Reason',
                                   help="Reason for the repairing")
    machine_brand = fields.Char(string='Machine brand',
                                help="Brand of the machine")
    machine_model = fields.Char(string="Model", help="Model of the Machine")
    manufacturing_year = fields.Date(string='Manufacturing Year',
                                     help="Manufacturing date of the machine")
    priority = fields.Selection(
        [('low', 'Low'), ('high', 'High'), ('middle', 'Middle')],
        string="Priority", help="Priority for repairing", required=True)
    repair_detail = fields.Text(string='Repair Reason In Detail',
                                help="Repairing Details", required=True)
    technician_id = fields.Many2one('hr.employee', string="Technician",
                                    help="The technician for the repair")
    technician_member_ids = fields.Many2many('hr.employee',
                                             string="Technical member")
    email = fields.Char('Email', related='technician_id.work_email',
                        help="Technician Email")
    company_id = fields.Many2one('res.company', string="Company",
                                 help="Company Of technician")
    project_id = fields.Many2one('project.project', string="Project",
                                 help="Project of that repairing")
    department_id = fields.Many2one('hr.department', string="Department",
                                    help="Department of the technician")
    repir_req_date = fields.Date(string='Repair Date',
                                 help="Repair requesting date")
    closing_date = fields.Date(string='Closing Date',
                               help="The repair closing date")
    repairing_duration = fields.Float(string="Repairing Duration",
                                      help="The duration of the repairing")
    is_repaired = fields.Boolean(string='Is Repaired',
                                 help="Which is used to identify the order is "
                                      "repaired or not")
    machine_id = fields.Many2one('product.product', string="Machine",
                                 help="Machine name",
                                 domain=[('is_machine', '=', True)])
    machine_categ_id = fields.Many2one('product.category',
                                       string='Machine Category',
                                       help="the category of the machine")
    color = fields.Char(string='Color', help="Color of the machine")
    damage = fields.Char(string='Damage', help="Damage of machine")
    warranty = fields.Boolean(string='Warranty', help="Warranty of the machine")
    Warranty_exp_date = fields.Date(string="Warranty Expiration Date",
                                    help="The Machine Warranty Expiration date")
    authority_name = fields.Char(string='Authority Name',
                                 help="The Authority of the technician")
    service_id = fields.Many2one('machine.service', string="Service",
                                 help="The service for the machine")
    customer_rating = fields.Char(string='Customer Rating',
                                  help="Customer Review")
    customer_comments = fields.Char(string='Customer Comments',
                                    help="Comments of the customer")
    extra_info = fields.Html(string="Information", help="Extra Information")
    repair_team_id = fields.Many2one('repair.team', string="Repair team",
                                     help="The team of repairing")
    nature_of_service_id = fields.Many2one('machine.service',
                                           string="Nature of Service",
                                           help="The nature of the machine service")
    repair_type_id = fields.Many2many('machine.service.type',
                                      string="Repair Types",
                                      help="The type of the repairs")
    problem = fields.Char(string='Problem', help="Problem of the machine")
    note = fields.Html(string='Note', help="Note for the repairing")
    state = fields.Selection(string='Status', required=True, readonly=True,
                             copy=False, selection=[('new', 'New'),
                                                    ('assigned', 'Assigned'),
                                                    ('closed', 'Closed'),
                                                    ('send', 'Mail Send'),
                                                    ('reopen', 'Re Opened'),
                                                    ], default='new',
                             help="stages of machine repair request")
    image1 = fields.Binary(string='Image 1', help="Machine images")
    image2 = fields.Binary(string='Image 2', help="Machine images")
    image3 = fields.Binary(string='Image 3', help="Machine images")
    image4 = fields.Binary(string='Image 4', help="Machine images")
    image5 = fields.Binary(string='Image 5', help="Machine images")
    timesheet_ids = fields.One2many('repair.timesheet', 'inverse_id',
                                    string="Timesheet",
                                    help="Timesheet for the machine repairing")
    consume_part_ids = fields.One2many('machine.consume', 'consume_id',
                                       string="Consumer Parts",
                                       help="Machine consumption")
    is_team_assigned = fields.Boolean(string='Is team assigned',
                                      help='To check whether the  repair team is assigned or not')

    @api.model
    def create(self, vals):
        """Sequence generator"""
        if vals.get('repair_seq', 'New') == 'New' or vals.get('repair_seq',
                                                              '') == '':
            vals['repair_seq'] = self.env['ir.sequence'].next_by_code(
                'machine.repair') or 'New'
        result = super().create(vals)
        return result

    @api.onchange('repair_team_id')
    def onchange_repair_team(self):
        val = self.env['repair.team'].search(
            [('id', '=', self.repair_team_id.id)]).mapped('member_ids').mapped(
            'member_id').ids
        self.technician_member_ids = val

    def action_create_diagnosis(self):
        """This is used to create the diagnosis"""
        self.env['machine.diagnosis'].create({
            'project_id': self.project_id.id,
            'customer_id': self.customer_id.id,
            'deadline': self.closing_date,
        })
        return {
            'res_model': 'machine.diagnosis',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': "{'create': False}"
        }

    def action_create_work_order(self):
        """Creating job order from repair request"""
        self.env['machine.workorder'].create({
            'customer_id': self.customer_id.id,
            'date': self.repir_req_date,
            'priority': self.priority,
        })
        return {
            'res_model': 'machine.workorder',
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': "{'create': False ,}"
        }

    def action_reopen(self):
        """Reopen the repair"""
        self.state = 'reopen'

    def action_close_repairing(self):
        """Repair closed"""
        self.state = 'closed'

    def action_assign_teams(self):
        """Assigning  repair to teams"""
        if self.repair_team_id:
            val = self.env['repair.team'].search(
                [('id', '=', self.repair_team_id.id)])
            val.write({
                'repair_work_ids': [(4, self.id)],
            })
            self.is_team_assigned = True
            self.state = 'assigned'
        else:
            self.state = 'new'
            raise ValidationError("There Is No Repair Team Is Specified")

    def action_send_email(self):
        """Sending mails to customers by informing closing the repair request"""
        template_id = self.env.ref(
            'base_machine_repair_management.repair_request_close_email_template').id
        self.env['mail.template'].browse(template_id).send_mail(self.id,
                                                                force_send=True)
        self.state = "send"

    def action_print_repair_request_report(self):
        """Which returns the report action"""
        return self.env.ref(
            "base_machine_repair_management.action_repair_report").report_action(
            self)


class RepairTimesheet(models.Model):
    """This is used for thr timesheet of repair management"""
    _name = 'repair.timesheet'
    _description = "Timesheet Of The Repair"
    _rec_name = 'user_id'

    inverse_id = fields.Many2one('machine.repair', string="Machine Repair",
                                 help="Inverse field of the models "
                                      "'machine.repair'")
    date = fields.Date(string='Date', help="Time sheet creation date")
    user_id = fields.Many2one('res.users', string="User",
                              help="Time sheet for the user")
    project_id = fields.Many2one('project.project', string="Project",
                                 help="Project for the user")
    description = fields.Char(string='Description',
                              help="Description for the user's timesheet")
    hours = fields.Float(string='Duration', help="Duration of the Work")
    diagnosis_id = fields.Many2one('machine.diagnosis',
                                   string="Diagnosis",
                                   help="Machine diagnosis")
