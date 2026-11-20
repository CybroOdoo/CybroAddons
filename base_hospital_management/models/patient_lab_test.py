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


class PatientLabTest(models.Model):
    """Class holding Patient lab test details"""
    _name = 'patient.lab.test'
    _description = 'Patient Lab Test'
    _rec_name = 'test_id'

    test_id = fields.Many2one('lab.test.line',
                              help='Name of the test')
    patient_id = fields.Many2one('res.partner',
                                 domain=[('patient_seq', 'not in',
                                          ['New', 'Employee', 'User'])],
                                 required=True, help='Choose the patient')
    patient_type = fields.Selection(related='test_id.patient_type', string='Type',
                                    help='Choose the type of patient')
    test_ids = fields.Many2many('lab.test',
                                related='test_id.test_ids',
                                help='All the tests added for the patient')
    date = fields.Date(help='Date of test',
                       default=fields.Date.today)
    total_price = fields.Float(string='Price', help='Total price for the test')
    currency_id = fields.Many2one('res.currency',
                                  help='Currency in which lab test amount will'
                                       ' be calculated',
                                  default=lambda self: self.env.company
                                  .currency_id.id,
                                  required=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('test', 'Test In Progress'),
                              ('completed', 'Completed')],
                             readonly=True,
                             help='State of test',
                             default="draft")
    result_ids = fields.One2many('lab.test.result',
                                 'parent_id', help='Results of the test')
    medicine_ids = fields.One2many('lab.medicine.line',
                                   'lab_test_id',
                                   compute='_compute_medicine_ids',
                                   readonly=False,
                                   help='Medicines needed for the test')
    notes = fields.Text(help='Notes regarding the test')
    lab_id = fields.Many2one('hospital.laboratory',
                             help='Lab in which test is doing')
    invoice_id = fields.Many2one('account.move',
                                 help='Invoice for the test', copy=False)
    order = fields.Integer(string='Sale Order',
                           help='Number of sale orders for vaccines and '
                                'medicines',
                           copy=False)
    started = fields.Boolean(string='Test Started',
                             help='True if the test has been started',
                             copy=False)
    invoiced = fields.Boolean(help='True if the test has been invoiced',
                              copy=False)
    sold = fields.Boolean(help='If true, sale order smart button will be '
                               'visible ', copy=False)
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.company.id)
    invoice_count = fields.Integer(
                                   compute='_compute_invoice_count',
                                   help='Total number of invoices for this '
                                        'patient lab test.')
    sale_count = fields.Integer(
                                compute='_compute_sale_count',
                                help='Total number of sale orders for this '
                                     'patient lab test.')
    inpatient_id = fields.Many2one('hospital.inpatient',
                                   help='Choose the inpatient')

    @api.depends('test_id', 'test_id.test_ids.medicine_ids')
    def _compute_medicine_ids(self):
        """Method for computing medicine_ids"""
        for record in self:
            record.medicine_ids = record.test_ids.medicine_ids

    def _compute_invoice_count(self):
        """Method for computing invoice_count"""
        for record in self:
            record.invoice_count = self.env['account.move'].sudo().search_count(
                ['|', (
                    'ref', '=', record.test_id.name), ('payment_reference', '=',
                                                       record.test_id.name)])

    def _compute_sale_count(self):
        """Method for computing sale_count"""
        for record in self:
            record.sale_count = self.env['sale.order'].sudo().search_count([(
                'reference', '=', record.test_id.name)])

    @api.model
    def action_get_patient_data(self, rec_id):
        """Returns data to the lab dashboard"""
        data = self.sudo().browse(rec_id)
        if data:
            patient_data = {
                'id': rec_id,
                'sequence': data.test_id.name,
                'name': data.patient_id.name,
                'unique': data.patient_id.patient_seq,
                'email': data.patient_id.email,
                'phone': data.patient_id.phone,
                'dob': data.patient_id.date_of_birth,
                'image_1920': data.patient_id.image_1920,
                'gender': data.patient_id.gender,
                'status': data.patient_id.marital_status,
                'doctor': data.test_id.doctor_id.name,
                'patient_type': data.patient_type.capitalize(),
                'state': data.state,
                'invoiced': data.invoiced,
                'ticket': data.test_id.op_id.op_reference
                if data.patient_type == 'outpatient'
                else data.test_id.patient_id.patient_seq,
                'test_data': [],
                'medicine': [],
                'result_ids': [],
            }
            if data.patient_id.blood_group:
                blood_caps = data.patient_id.blood_group.capitalize()
                patient_data['blood_group'] = blood_caps + str(
                    data.patient_id.rh_type),
            for test in data.test_ids:
                patient_data['test_data'].append({
                    'id': test.id,
                    'name': test.name,
                    'patient_lead': test.patient_lead,
                    'price': test.price,
                })
            for medicine in data.medicine_ids:
                patient_data['medicine'].append({
                    'id': medicine.medicine_id.id,
                    'name': medicine.medicine_id.name,
                    'quantity': medicine.quantity
                })
            for result in data.result_ids:
                patient_data['result_ids'].append({
                    'id': result.id,
                    'name': result.test_id.name,
                    'result': result.result,
                    'normal': result.normal,
                    'uom_id': result.uom_id.name,
                    'attachment': result.attachment,
                    'cost': result.price,
                    'state': result.state
                })
            return patient_data

    @api.model
    def start_test(self, rec_id):
        """Method for creating lab tests from lab dashboard"""
        data = self.sudo().browse(rec_id)
        data.state = 'test'
        data.started = True
        med_list = data.medicine_ids.ids
        for rec in data.test_ids:
            medicine_ids = [item for item in rec.medicine_ids.ids]
            data.sudo().write({
                'result_ids': [(0, 0, {
                    'patient_id': data.patient_id.id,
                    'test_id': rec.id,
                    'tax_ids': rec.tax_ids.ids
                })]
            })
            [med_list.append(i) for i in medicine_ids]
        data.medicine_ids = med_list

    @api.model
    def test_end(self, rec_id):
        """Method for ending test from lab dashboard"""
        data = self.sudo().browse(rec_id)
        data.state = 'completed'

    @api.model
    def create_invoice(self, rec_id):
        """Method for creating invoice"""
        data = self.sudo().browse(rec_id)
        order_lines = []
        partner_id = data.patient_id.id
        if data.medicine_ids:
            for rec in data.medicine_ids:
                order_lines.append((0, 0, {
                    'product_id': self.env['product.product'].sudo().search([
                        ('product_tmpl_id', '=', rec.medicine_id.id)]).id,
                    'name': rec.medicine_id.name,
                    'price_unit': rec.price,
                    'product_uom_qty': rec.quantity,
                }))
            sale_order = self.env['sale.order'].sudo().create({
                'partner_id': partner_id,
                'date_order': fields.Date.today(),
                'reference': data.test_id.name,
                'order_line': order_lines
            })
            data.sold = True
            data.order = sale_order.id
        invoice_id = self.env['account.move'].sudo().search(
            [('ref', '=', data.test_id.name)
             ], limit=1)
        if not invoice_id:
            invoice_id = self.env['account.move'].sudo().create({
                'move_type': 'out_invoice',
                'partner_id': partner_id,
                'invoice_date': fields.Date.today(),
                'date': fields.Date.today(),
                'ref': data.test_id.name
            })
        for rec in data.result_ids:
            invoice_id.sudo().write({
                'invoice_line_ids': [(
                    0, 0, {
                        'quantity': 1,
                        'name': rec.test_id.name,
                        'price_unit': rec.price,
                        'tax_ids': rec.tax_ids.ids,
                        'price_subtotal': rec.price,
                    }
                )]
            })
        data.invoiced = True
        data.invoice_id = invoice_id.id

    def action_test_end(self):
        """Button action for test end"""
        self.state = 'completed'

    def action_start_test(self):
        """Button action for start test"""
        self.start_test(self.id)

    def action_create_invoice(self):
        """Button action for creating invoice"""
        self.create_invoice(self.id)

    def action_view_invoice(self):
        """Method for viewing invoice from the smart button"""
        return {
            'name': 'Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            "context": {"create": False, 'default_move_type': 'out_invoice'},
            'domain': [('id', '=', self.invoice_id.id)]
        }

    def action_view_sale_order(self):
        """Method for viewing sale order from the smart button"""
        sale_order = self.env['sale.order'].sudo().search(
            [('partner_id', '=', self.patient_id.id)], limit=1)
        return {
            'name': 'Sale order',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'type': 'ir.actions.act_window',
            'res_id': sale_order.id
        }

    def print_lab_tests(self):
        """Method for printing the lab test result"""
        test_list = []
        for rec in self.result_ids:
            datas = {
                'name': rec.test_id.name or '',
                'test': rec.test_id.name or '',
                'normal': rec.normal or '',
                'uom_id': rec.uom_id.name or '',
                'result': rec.result or '',
                'cost': rec.price,
                'currency': self.env.company.currency_id.symbol or ''
            }
            test_list.append(datas)
        doctor = self.sudo().test_id.doctor_id
        data = {
            'datas': test_list,
            'date': self.date,
            'patient_id': self.patient_id.name or '',
            'patient_name': self.patient_id.name or '',
            'doctor_name': doctor.name if doctor else '',
        }
        return self.env.ref(
            'base_hospital_management.action_report_patient_lab_tests').report_action(self, data=data)
