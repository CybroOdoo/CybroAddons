# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ranjith R(<https://www.cybrosys.com>)
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
###########################################################################
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class LabourSupply(models.Model):
    """
    Class to create contract for labour supply
           """
    _name = "labour.supply"
    _description = "Contract creation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'sequence_number'

    sequence_number = fields.Char(string="Sequence Number", readonly=True,
                                  copy=False, default="New",
                                  help="Field to specify sequence number")
    customer_id = fields.Many2one('res.partner', string="Customer",
                                  help="Field to choose customer",
                                  required=True)
    skill_ids = fields.One2many('labour.on.skill',
                                'labour_supply_id',
                                string="Skills Required", required=True,
                                help="Field to choose skill and number "
                                     "required")
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True,
                                 default=lambda self: self.env.company)
    from_date = fields.Date(string="From date", tracking=True,
                            help="Field to choose from date")
    to_date = fields.Date(string="To date", tracking=True,
                          help="Field to choose to date")
    state = fields.Selection([('draft', 'Draft'), ('ready', 'Ready'),
                              ('confirmed', 'Confirmed'),
                              ('invoiced', 'Invoiced'),
                              ('canceled', 'Canceled'),
                              ('expired', 'Expired')],
                             string="State", default="draft", tracking=True,
                             help="Field to specify state")
    workers_ids = fields.Many2many('workers.details',
                                   string="Select workers",
                                   readonly=True,
                                   help="Field to choose workers")
    total_amount = fields.Monetary(tracking=True, readonly=True,
                                   string="Total Amount", help="Total amount")
    currency_id = fields.Many2one('res.currency',
                                  string='Currency', help="Currency",
                                  related='company_id.currency_id')
    period = fields.Integer(string="Period", help="The period of contract")
    invoice_id = fields.Many2one('account.move', string="Invoice",
                                 help="The invoice of contract")
    is_alert = fields.Boolean(string="Alert",
                              help="Boolean field to control the visibility "
                                   "of alert visibility")
    view_workers_page = fields.Boolean(default=False, string="View worker page",
                                       help="Field to control the"
                                            " visibility of workers page ")

    @api.model
    def create(self, vals):
        """
           Summary:
               function return sequence number for record
           Args:
               vals:To store the sequence created
           return:
                result:return sequence created
               """
        vals['sequence_number'] = self.env['ir.sequence'].next_by_code(
            'labour.supply') or 'New'
        return super(LabourSupply, self).create(vals)

    def cron_change_state(self):
        """
          Summary:
           function changes the state of worker
            when the worker have  ongoing work
           and also change the state when the contact expire
           """
        labour_supplies = self.env['labour.supply'].search(
            [('state', 'not in', ['draft', 'cancel'])])
        for labour_supply in labour_supplies:
            if labour_supply.to_date < fields.Date.today():
                labour_supply.write({'state': 'expired'})
                for worker in labour_supply.workers_ids:
                    worker.write({'state': 'available'})
        labours_supplies = self.env['labour.supply'].search(
            [('state', '=', 'invoiced')])
        for contract in labours_supplies:
            if contract.from_date == fields.Date.today():
                for labour in contract.workers_ids:
                    labour.write({'state': 'not_available'})

    def action_confirm(self):
        """
          Summary:
                function confirm the record state
                            """
        self.write({'state': 'confirmed'})

    def action_draft(self):
        """
        Summary:
                function change the record state to draft
                                    """
        self.total_amount = 0
        self.workers_ids = False
        self.view_workers_page = False
        self.is_alert = False
        self.state = 'draft'

    def action_cancel(self):
        """
        summary:
                function change the record state to cancelled
                                    """
        for worker in self.workers_ids:
            worker.write({'state': 'available'})
        self.write({'state': 'canceled'})

    def action_create_invoice(self):
        """
        summary:
            function change the record state to invoice,
            create invoice on the basis of total amount and
            return invoice
                            """
        if self.from_date == fields.Date.today():
            for worker in self.workers_ids:
                worker.write({'state': 'not_available'})
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer_id.id,
            'currency_id': self.currency_id.id,
            'invoice_date': self.to_date,
            'invoice_origin': self.sequence_number,
            'invoice_line_ids': [(0, 0, {
                'name': "contract cost",
                'quantity': 1,
                'price_unit': self.total_amount,
            })],
        })
        self.invoice_id = invoice.id
        self.write({'state': 'invoiced'})
        return {
            'name': 'create_invoice',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': invoice.id,
            'res_model': 'account.move',
            'target': 'current'
        }

    def action_labour_supply_invoices(self):
        """
        Summary:
           function returns invoice of current record
        return:
           returns invoices created
              """
        return {
            'name': 'Create Invoice',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('invoice_origin', '=', self.sequence_number)]
        }

    def action_fetch(self):
        """
        Summary:
           function change the record state to Ready,
           calculate total amount according workers assigned
           also calculate the total from date and to date """
        self.workers_ids = False
        self.total_amount = 0
        if self.skill_ids:
            date_list = []
            for skill in self.skill_ids:
                if skill.from_date < fields.Date.today() or \
                        skill.to_date < fields.Date.today():
                    raise ValidationError("Enter valid date ")
                if skill.to_date < skill.from_date:
                    raise ValidationError("Invalid start date and end date ")
            labour_not_available = self.env['labour.supply'].search(
                [('state', '=', "invoiced"),
                 ('from_date', '<', fields.Date.today())
                    , ('to_date', '>', fields.Date.today())]).mapped(
                'workers_ids.id')
            labours_selected = []
            for skill in self.skill_ids:
                count = 0
                date_list.append(skill.from_date)
                date_list.append(skill.to_date)
                worker_details = self.env['workers.details'].search([])
                labour_available = worker_details.search(
                    [('skill_ids', '=', skill.skill_id.id),
                     ('state', '=', 'available'),
                     ('id', 'not in', labours_selected),
                     ('id', 'not in', labour_not_available)]).mapped('id')
                labours_selected = labours_selected + labour_available
                if len(labour_available) < skill.number_of_labour_required:
                    self.is_alert = True
                for worker in worker_details:
                    if worker.id in labour_available:
                        if count < skill.number_of_labour_required:
                            count = count + 1
                            self.write({'workers_ids': [(4, worker.id,)]})
                            date_start = datetime.strptime(str(skill.from_date),
                                                           '%Y-%m-%d')
                            date_end = datetime.strptime(str(skill.to_date),
                                                         '%Y-%m-%d')
                            period = date_end - date_start
                            self.period = int(str(period.days))
                            self.total_amount = self.total_amount + (
                                    worker.rate * (self.period + 1))
            date_list = sorted(date_list)
            self.from_date = date_list[0]
            self.to_date = date_list[-1]
            self.view_workers_page = True
            self.state = 'ready'
        else:
            raise ValidationError("Enter Skill Required")
