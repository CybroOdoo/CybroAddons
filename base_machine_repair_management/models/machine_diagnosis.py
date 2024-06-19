"""Machine Diagnosis"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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


class MachineDiagnosis(models.Model):
    """The class is used for the machine diagnosis"""
    _name = 'machine.diagnosis'
    _description = "Machine Diagnosis"
    _rec_name = 'diagnosis_seq'

    project_id = fields.Many2one('project.project', string='Project',
                                 help="The project name")
    customer_id = fields.Many2one('res.partner', string="Customer",
                                  help="the customer for the project",
                                  required=True, )
    deadline = fields.Date(string='DeadLine', help="Deadline for the project",
                           required=True, )
    diagnosis_seq = fields.Char(string='Diagnosis Sequence', required=True,
                                copy=False,
                                help="Sequence number for diagnosis",
                                readonly=True, index=True,
                                default=lambda self: 'New')
    note = fields.Html(string="Note", help="Extra note for the project")
    notes = fields.Html(string="Notes", help="Notes for thr project")
    part_ids = fields.One2many('machine.consume',
                               'dia_estimate_id',
                               help="machine consumption", string="Parts")
    timesheet_ids = fields.One2many('repair.timesheet',
                                    'diagnosis_id',
                                    string="TimeSheet",
                                    help='Timesheet for the machine repair')
    seq = fields.Char(string='Sequence', help="Sequence")
    assigning_date = fields.Date(string="Date", help="Assigning Date")
    machine_repair_ref_id = fields.Many2one('machine.repair',
                                            string="Reference",
                                            help="Machine repair reference")

    @api.model
    def create(self, vals):
        """Sequence generator"""
        if vals.get('diagnosis_seq', 'New') == 'New':
            vals['diagnosis_seq'] = self.env['ir.sequence'].next_by_code(
                'machine.diagnosis') or 'New'
        result = super().create(vals)
        return result

    def create_quotation(self):
        """This function is used to create quotation from machine diagnosis"""
        quotation = self.env['sale.order'].create({
            'partner_id': self.customer_id.id,
            'date_order': self.deadline,
            'machine_diag_ref': self.diagnosis_seq,
        })
        quotation.order_line = [(5, 0, 0)]
        val = self.part_ids.mapped('machine_id')
        for rec in val:
            vals = {
                'product_id': rec.id,
                'name': rec.default_code,
                'price_unit': rec.list_price,
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
