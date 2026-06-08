# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from datetime import datetime


class LabourSupply(models.Model):
    """
    Labour Supply Contract

    This model manages labour supply contracts created for customers.
    It handles skill-based labour allocation, worker assignment,
    contract period calculation, invoicing, and state transitions.
    """

    _name = "labour.supply"
    _description = "Labour Supply Contract"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'sequence_number'

    sequence_number = fields.Char(
        string="Reference",
        readonly=True,
        copy=False,
        default="New",
        help="Unique reference generated automatically for the labour "
             "supply contract."
    )

    customer_id = fields.Many2one(
        'res.partner',
        string="Customer",
        required=True,
        help="Customer for whom the labour supply contract is created."
    )

    skill_ids = fields.One2many(
        'labour.on.skill',
        'labour_supply_id',
        string="Skills Required",
        required=True,
        help="List of skills required along with the number of labourers "
             "and the respective date ranges."
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help="Company under which this labour supply contract is managed."
    )

    from_date = fields.Date(
        string="From Date",
        tracking=True,
        help="Contract start date, automatically computed from skill "
             "requirements."
    )

    to_date = fields.Date(
        string="To Date",
        tracking=True,
        help="Contract end date, automatically computed from skill "
             "requirements."
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('ready', 'Ready'),
            ('confirmed', 'Confirmed'),
            ('invoiced', 'Invoiced'),
            ('canceled', 'Canceled'),
            ('expired', 'Expired'),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current status of the labour supply contract."
    )

    workers_ids = fields.Many2many(
        'workers.details',
        string="Assigned Workers",
        readonly=True,
        help="Workers assigned to this labour supply contract based on "
             "required skills and availability."
    )

    total_amount = fields.Monetary(
        string="Total Amount",
        readonly=True,
        tracking=True,
        help="Total contract amount calculated based on worker rates "
             "and contract period."
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        help="Currency used for calculating the contract amount."
    )

    period = fields.Integer(
        string="Contract Period (Days)",
        help="Total duration of the contract in days."
    )

    invoice_id = fields.Many2one(
        'account.move',
        string="Invoice",
        help="Customer invoice generated for this labour supply contract."
    )

    is_alert = fields.Boolean(
        string="Availability Alert",
        help="Indicates whether the required number of workers is "
             "currently unavailable."
    )

    view_workers_page = fields.Boolean(
        string="Show Workers Page",
        default=False,
        help="Controls the visibility of the workers assignment page."
    )

    @api.model_create_multi
    def create(self, vals):
        """
        Create Labour Supply Contract

        Generates a unique sequence number for each labour supply contract
        during record creation.
        """
        vals[0]['sequence_number'] = self.env['ir.sequence'].next_by_code(
            'labour.supply'
        ) or 'New'
        return super().create(vals)

    def cron_change_state(self):
        """
        Scheduled State Update

        - Marks contracts as expired when the end date has passed
        - Frees workers when contracts expire
        - Marks workers as unavailable when an invoiced contract starts
        """
        labour_supplies = self.env['labour.supply'].search(
            [('state', 'not in', ['draft', 'canceled'])]
        )
        for contract in labour_supplies:
            if contract.to_date and contract.to_date < fields.Date.today():
                contract.write({'state': 'expired'})
                contract.workers_ids.write({'state': 'available'})

        invoiced_contracts = self.env['labour.supply'].search(
            [('state', '=', 'invoiced')]
        )
        for contract in invoiced_contracts:
            if contract.from_date == fields.Date.today():
                contract.workers_ids.write({'state': 'not_available'})

    def action_confirm(self):
        """
        Confirm Contract

        Changes the contract state to Confirmed.
        """
        self.write({'state': 'confirmed'})

    def action_draft(self):
        """
        Reset to Draft

        Clears assigned workers, amounts, alerts, and resets
        the contract to Draft state.
        """
        self.write({
            'total_amount': 0,
            'workers_ids': False,
            'view_workers_page': False,
            'is_alert': False,
            'state': 'draft'
        })

    def action_cancel(self):
        """
        Cancel Contract

        Cancels the labour supply contract and releases all
        assigned workers back to available status.
        """
        self.workers_ids.write({'state': 'available'})
        self.write({'state': 'canceled'})

    def action_create_invoice(self):
        """
        Create Invoice

        Generates a customer invoice based on the total contract amount
        and updates worker availability accordingly.
        """
        if self.from_date == fields.Date.today():
            self.workers_ids.write({'state': 'not_available'})

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer_id.id,
            'currency_id': self.currency_id.id,
            'invoice_date': self.to_date,
            'invoice_origin': self.sequence_number,
            'invoice_line_ids': [(0, 0, {
                'name': "Labour Supply Contract Cost",
                'quantity': 1,
                'price_unit': self.total_amount,
            })],
        })

        self.write({
            'invoice_id': invoice.id,
            'state': 'invoiced'
        })

        return {
            'name': 'Invoice',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': invoice.id,
            'res_model': 'account.move',
            'target': 'current'
        }

    def action_labour_supply_invoices(self):
        """
        View Invoices

        Returns all invoices related to this labour supply contract.
        """
        return {
            'name': 'Invoices',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'account.move',
            'domain': [('invoice_origin', '=', self.sequence_number)]
        }

    def action_fetch(self):
        """
        Fetch Available Workers

        - Validates skill date ranges
        - Assigns available workers based on skill requirements
        - Calculates contract period and total amount
        - Updates contract dates and status
        """
        self.workers_ids = False
        self.total_amount = 0

        if not self.skill_ids:
            raise ValidationError("Please add at least one required skill.")

        date_list = []
        labours_selected = []

        for skill in self.skill_ids:
            if skill.from_date < fields.Date.today() or \
                    skill.to_date < fields.Date.today():
                raise ValidationError("Please enter valid future dates.")

            if skill.to_date < skill.from_date:
                raise ValidationError("End date cannot be earlier than start date.")

            date_list.extend([skill.from_date, skill.to_date])

            unavailable_labours = self.env['labour.supply'].search([
                ('state', '=', 'invoiced'),
                ('from_date', '<', fields.Date.today()),
                ('to_date', '>', fields.Date.today())
            ]).mapped('workers_ids.id')

            available_workers = self.env['workers.details'].search([
                ('skill_ids', '=', skill.skill_id.id),
                ('state', '=', 'available'),
                ('id', 'not in', labours_selected + unavailable_labours)
            ])

            if len(available_workers) < skill.number_of_labour_required:
                self.is_alert = True

            for worker in available_workers[:skill.number_of_labour_required]:
                self.workers_ids = [(4, worker.id)]
                labours_selected.append(worker.id)

                date_start = datetime.strptime(str(skill.from_date), '%Y-%m-%d')
                date_end = datetime.strptime(str(skill.to_date), '%Y-%m-%d')
                period = (date_end - date_start).days
                self.period = period
                self.total_amount += worker.rate * (period + 1)

        self.from_date = min(date_list)
        self.to_date = max(date_list)
        self.view_workers_page = True
        self.state = 'ready'

