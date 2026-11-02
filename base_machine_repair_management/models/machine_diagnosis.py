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


class MachineDiagnosis(models.Model):
    """This model is used to manage machine diagnoses."""
    _name = 'machine.diagnosis'
    _description = "Machine Diagnosis"
    _rec_name = 'diagnosis_seq'

    project_id = fields.Many2one('project.project',
                                 help="The project associated with this machine diagnosis or repair.")
    customer_id = fields.Many2one('res.partner',
                                  help="The customer for whom this diagnosis is carried out.",
                                  required=True)
    deadline = fields.Date(help="The final due date for completing the diagnosis.",
                           required=True)
    diagnosis_seq = fields.Char(string='Diagnosis Sequence', copy=False,
                                help="Unique sequence number assigned to each diagnosis record.",
                                readonly=True, index=True,
                                default=lambda self: 'New')
    note = fields.Html(help="Additional details or comments regarding the diagnosis.")
    notes = fields.Html(help="General notes related to the diagnosis.")
    part_ids = fields.One2many('machine.consume', 'dia_estimate_id',
                               string="Parts",
                               help="List of machine parts consumed during the repair or diagnosis process.")
    timesheet_ids = fields.One2many('repair.timesheet', 'diagnosis_id',
                                    help="Timesheet entries that log the time spent on machine repairs.")
    seq = fields.Char(string='Sequence',
                      help="Unique identifier for this record.")
    assigning_date = fields.Date(help="The date on which the diagnosis was assigned.")
    machine_repair_ref_id = fields.Many2one('machine.repair',
                                            string="Reference",
                                            help="Reference to the related machine repair record.")

    @api.model_create_multi
    def create(self, vals_list):
        """Generate the diagnosis sequence on create."""
        # Work on copies so the caller's dictionaries are never modified.
        vals_list = [dict(vals) for vals in vals_list]
        for vals in vals_list:
            if vals.get('diagnosis_seq', 'New') == 'New':
                vals['diagnosis_seq'] = self.env['ir.sequence'].next_by_code(
                    'machine.diagnosis') or 'New'
        return super().create(vals_list)

    def action_create_quotation(self):
        """Create a quotation from the machine diagnosis."""
        self.ensure_one()
        quotation = self.env['sale.order'].create({
            'partner_id': self.customer_id.id,
            'date_order': self.deadline,
            'machine_diagnosis_ref': self.diagnosis_seq,
        })
        quotation.order_line = [(5, 0, 0)]
        for rec in self.part_ids:
            vals = {
                'product_id': rec.machine_id.id,
                'name': rec.machine_id.default_code if rec.machine_id.default_code else '',
                'product_uom_qty': rec.qty,
                'price_unit': rec.machine_id.list_price,
            }
            quotation.order_line = [(0, 0, vals)]
        return {
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'res_id': quotation.id,
            'view_mode': 'form',
            'target': 'current',
            'context': "{'create': False ,}"
        }
