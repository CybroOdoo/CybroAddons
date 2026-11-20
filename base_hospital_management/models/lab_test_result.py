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


class LabTestResult(models.Model):
    """Class holding lab test result"""
    _name = 'lab.test.result'
    _description = 'Lab Test Result'
    _rec_name = 'test_id'

    patient_id = fields.Many2one('res.partner',
                                 domain=[('patient_seq', 'not in',
                                          ['New', 'Employee', 'User'])],
                                 help='Patient for whom the test has been done')
    result = fields.Char(help='Result of the test')
    normal = fields.Char(help="The normal rate of the test")
    uom_id = fields.Many2one('uom.uom', string='Unit',
                             help='Unit of the normal and result value')
    parent_id = fields.Many2one('patient.lab.test', string='Tests',
                                help='The tests for which the result'
                                     ' corresponds to')
    test_id = fields.Many2one('lab.test', string="Test Name",
                              help='Name of the test')
    attachment = fields.Binary(string='Result Document', help='Result document')
    currency_id = fields.Many2one('res.currency',
                                  related='test_id.currency_id',
                                  help='Currency in which payments to be done')
    price = fields.Monetary(string='Cost', help='Cost for the test',
                            related='test_id.price')
    tax_ids = fields.Many2many('account.tax',
                               help='Tax for the test')
    state = fields.Selection(selection=[('processing', 'Processing'),
                                        ('published', 'Published')],
                             help='State of the result',
                             default='processing', compute='_compute_state')

    @api.depends('attachment')
    def _compute_state(self):
        """Method for computing the state of result based on attachment"""
        for rec in self:
            if rec.attachment:
                rec.state = 'published'
            else:
                rec.state = 'processing'

    @api.model
    def print_test_results(self):
        """Method for printing rest result"""
        data = self.sudo().search([], limit=100)
        context = []
        for rec in data:
            attachment = self.env['ir.attachment'].sudo().search([
                ('res_id', '=', rec.id),
                ('res_model', '=', 'lab.test.result'),
            ], limit=1)
            attachment_id = attachment.id if attachment else False
            access_token = ''
            if attachment:
                if not attachment.access_token:
                    attachment.generate_access_token()
                access_token = attachment.access_token or ''
            context.append({
                'id': rec.id,
                'parent_id': rec.parent_id.test_id.name,
                'patient_id': [rec.parent_id.patient_id.id,
                               rec.parent_id.patient_id.name],
                'test_id': rec.test_id.name,
                'attachment_id': attachment_id,
                'access_token': access_token,
                'normal': rec.normal,
                'result': rec.result,
                'unit': rec.uom_id.name if rec.uom_id else ''
            })
        return context
