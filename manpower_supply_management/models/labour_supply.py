# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(Contact : odoo@cybrosys.com)
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
                                 help="The invoice of contract",
                                 )
    is_alert = fields.Boolean(string="Alert",
                              help="Boolean field to control the visibility "
                                   "of alert visibility")
    view_workers_page = fields.Boolean(default=False, string="View worker page",
                                       help="Field to control the"
                                            " visibility of workers page ")

    @api.model_create_multi
    def create(self, vals):
        """
           Summary:
               function return sequence number for record
           Args:
               vals:To store the sequence created
           return:
                result:return sequence created
               """
        vals[0]['sequence_number'] = self.env['ir.sequence'].next_by_code(
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
        if not self.workers_ids:
            raise ValidationError(
                "You cannot confirm the contract without assigning workers."
            )
        self.write({'state': 'confirmed'})

    def action_draft(self):
        if self.state == 'invoiced':
            raise ValidationError(
                "You cannot reset an invoiced contract to draft."
            )
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
        if not self.workers_ids:
            raise ValidationError(
                "You cannot create an invoice without assigned workers."
            )

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
        self.state = 'invoiced'

        return {
            'name': 'Invoice',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': invoice.id,
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
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('invoice_origin', '=', self.sequence_number)]
        }

    def action_fetch(self):
        """
        Summary:
           function change the record state to Ready,
           calculate total amount according workers assigned
           also calculate the total from date and to date """
        self.is_alert = False
        if self.skill_ids:
            date_list = []
            workers_to_assign = []
            worker_assignments = {} # dict mapping worker.id to list of (from_date, to_date)
            total_sum = 0
            
            for skill in self.skill_ids:
                if skill.from_date < fields.Date.today() or \
                        skill.to_date < fields.Date.today():
                    raise ValidationError("Enter valid date ")
                if skill.to_date < skill.from_date:
                    raise ValidationError("Invalid start date and end date ")

                date_list.append(skill.from_date)
                date_list.append(skill.to_date)

                # Check for overlapping contracts for the SPECIFIC dates of this skill
                overlapping_contracts = self.env['labour.supply'].search([
                    ('id', '!=', self.ids[0] if self.ids else False),
                    ('state', 'in', ['confirmed', 'invoiced']),
                    ('from_date', '<=', skill.to_date),
                    ('to_date', '>=', skill.from_date)
                ])
                busy_worker_ids = overlapping_contracts.mapped('workers_ids').ids

                # Find workers assigned previously in THIS draft fetch that overlap with this skill's dates
                current_draft_busy_ids = []
                for w_id, intervals in worker_assignments.items():
                    for interval_from, interval_to in intervals:
                        if interval_from <= skill.to_date and interval_to >= skill.from_date:
                            current_draft_busy_ids.append(w_id)
                            break
                            
                all_busy_worker_ids = list(set(busy_worker_ids + current_draft_busy_ids))

                import logging
                _logger = logging.getLogger(__name__)
                _logger.info(f"Skill: {skill.skill_id.name}, from: {skill.from_date}, to: {skill.to_date}")
                _logger.info(f"busy_worker_ids (other contracts): {busy_worker_ids}")
                _logger.info(f"current_draft_busy_ids (this draft): {current_draft_busy_ids}")
                _logger.info(f"all_busy_worker_ids: {all_busy_worker_ids}")

                # Fetch available workers for THIS skill and THIS period
                domain = [('skill_ids', '=', skill.skill_id.id), ('state', '=', 'available')]
                if all_busy_worker_ids:
                    domain.append(('id', 'not in', all_busy_worker_ids))
                    
                labour_available_records = self.env['workers.details'].search(domain)
                _logger.info(f"labour_available_records: {labour_available_records.ids}")

                if len(labour_available_records) < skill.number_of_labour_required:
                    raise ValidationError(
                        f"Insufficient workers available for skill '{skill.skill_id.name}' "
                        f"during the period {skill.from_date} to {skill.to_date}.\n"
                        f"Requested: {skill.number_of_labour_required}, Available: {len(labour_available_records)}."
                    )

                count = 0
                for worker in labour_available_records:
                    if count < skill.number_of_labour_required:
                        count = count + 1
                        workers_to_assign.append(worker.id)
                        
                        if worker.id not in worker_assignments:
                            worker_assignments[worker.id] = []
                        worker_assignments[worker.id].append((skill.from_date, skill.to_date))
                        
                        # Odoo 18 date objects support direct subtraction
                        period_days = (skill.to_date - skill.from_date).days
                        total_sum = total_sum + (worker.rate * (period_days + 1))

            self.write({
                'workers_ids': [(6, 0, list(set(workers_to_assign)))],
                'total_amount': total_sum,
                'view_workers_page': True,
                'state': 'ready',
                'from_date': min(date_list),
                'to_date': max(date_list),
            })
        else:
            raise ValidationError("Enter Skill Required")
