# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Maintainer: Cybrosys Technologies (<https://www.cybrosys.com>)
#
##############################################################################
import datetime
from odoo import models, fields, api


class LabRequest(models.Model):
    _name = 'lab.request'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _rec_name = 'lab_request_id'
    _description = 'Lab Request'

    name = fields.Char(string='Lab Test', size=16, readonly=True, required=True, help="Lab result ID", default=lambda *a: '#')
    lab_request_id = fields.Char(string='Appointment ID', help="Lab appointment ID")
    app_id = fields.Many2one('lab.appointment', string='Appointment')
    lab_requestor = fields.Many2one('lab.patient', string='Patient', required=True, select=True,
                                    help='Patient Name')
    test_request = fields.Many2one('lab.test', string='Test')
    lab_requesting_date = fields.Datetime(string='Requested Date')
    comment = fields.Text('Comment')
    request_line = fields.One2many('lab.test.attribute', 'test_request_reverse', string="Test Lines")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sample_collection', 'Sample Collected'),
        ('test_in_progress', 'Test In Progress'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled'),

    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('lab.request')
        vals['name'] = sequence or '/'
        return super(LabRequest, self).create(vals)

    @api.multi
    def set_to_sample_collection(self):
        return self.write({'state': 'sample_collection'})

    @api.multi
    def set_to_test_in_progress(self):
        return self.write({'state': 'test_in_progress'})

    @api.multi
    def cancel_lab_test(self):
        return self.write({'state': 'cancel'})

    @api.multi
    def set_to_test_completed(self):
        req_obj = self.env['lab.request'].search_count([('app_id', '=', self.app_id.id),
                                                        ('id', '!=', self.id)])
        req_obj_count = self.env['lab.request'].search_count([('app_id', '=', self.app_id.id),
                                                              ('id', '!=', self.id),
                                                              ('state', '=', 'completed')])
        if req_obj == req_obj_count:
            app_obj = self.env['lab.appointment'].search([('id', '=', self.app_id.id)])
            app_obj.write({'state': 'completed'})
        return self.write({'state': 'completed'})

    @api.multi
    def print_lab_test(self):
        return self.env['report'].get_action(self, 'medical_lab_management.report_patient_labtest')

    @api.multi
    def lab_invoice_create(self):
        invoice_obj = self.env["account.invoice"]
        invoice_line_obj = self.env["account.invoice.line"]
        for lab in self:
            if lab.lab_requestor:
                curr_invoice = {
                    'partner_id': lab.lab_requestor.patient.id,
                    'account_id': lab.lab_requestor.patient.property_account_receivable_id.id,
                    'state': 'draft',
                    'type': 'out_invoice',
                    'date_invoice': datetime.datetime.now(),
                    'origin': "Lab Test# : " + lab.name,
                    'target': 'new',
                    'lab_request': lab.id,
                    'is_lab_invoice': True
                }

                inv_ids = invoice_obj.create(curr_invoice)
                inv_id = inv_ids.id

                if inv_ids:
                    journal = self.env['account.journal'].search([('type', '=', 'sale')], limit=1)
                    prd_account_id = journal.default_credit_account_id.id
                    if lab.test_request:
                        curr_invoice_line = {
                            'name': "Charge for lab test",
                            'price_unit': lab.test_request.test_cost or 0,
                            'quantity': 1.0,
                            'account_id': prd_account_id,
                            'invoice_id': inv_id,
                        }

                        invoice_line_obj.create(curr_invoice_line)

                self.write({'state': 'invoiced'})
                form_view_ref = self.env.ref('account.invoice_form', False)
                tree_view_ref = self.env.ref('account.invoice_tree', False)

                return {
                    'domain': "[('id', '=', " + str(inv_id) + ")]",
                    'name': 'Lab Invoices',
                    'view_mode': 'form',
                    'res_model': 'account.invoice',
                    'type': 'ir.actions.act_window',
                    'views': [(tree_view_ref.id, 'tree'), (form_view_ref.id, 'form')],
                }
