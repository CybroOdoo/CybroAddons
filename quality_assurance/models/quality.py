# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models


class QualityMeasure(models.Model):
    _name = 'quality.measure'
    _inherit = ['mail.thread']
    _order = "id desc"

    name = fields.Char('Name', required=True)
    product_id = fields.Many2one('product.product', string='Product', index=True, ondelete='cascade', track_visibility='onchange')
    product_template_id = fields.Many2one('product.template', string='Product Template', related='product_id.product_tmpl_id')
    type = fields.Selection(
        [('quantity', 'Quantitative'),
         ('quality', 'Qualitative')],
        string='Test Type', default='quantity', required=True, track_visibility='onchange')
    quantity_min = fields.Float('Min-Value', track_visibility='onchange')
    quantity_max = fields.Float('Max-Value', track_visibility='onchange')
    trigger_time = fields.Many2many('stock.picking.type', string='Trigger On')
    active = fields.Boolean('Active', default=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.user.company_id.id, index=1)

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'quality':
            self.quantity_min = 0.0
            self.quantity_max = 0.0


class QualityAlert(models.Model):
    _name = 'quality.alert'
    _inherit = ['mail.thread']
    _order = "date asc, id desc"

    name = fields.Char('Name', required=True)
    date = fields.Datetime(string='Date', default=datetime.now(), track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='Product', index=True, ondelete='cascade')
    picking_id = fields.Many2one('stock.picking', string='Source Operation')
    origin = fields.Char(string='Source Document',
                         help="Reference of the document that produced this alert.",
                         readonly=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.user.company_id.id, index=1)
    user_id = fields.Many2one('res.users', string='Created by', default=lambda self: self.env.user.id)
    tests = fields.One2many('quality.test', 'alert_id', string="Tests")
    final_status = fields.Selection(compute="_compute_status",
                                    selection=[('wait', 'Waiting'),
                                               ('pass', 'Passed'),
                                               ('fail', 'Failed')],
                                    store=True, string='Status',
                                    default='fail', track_visibility='onchange')

    def generate_tests(self):
        quality_measure = self.env['quality.measure']
        measures = quality_measure.search([('product_id', '=', self.product_id.id),
                                           ('trigger_time', 'in', self.picking_id.picking_type_id.id)])
        for measure in measures:
            self.env['quality.test'].create({
                'quality_measure': measure.id,
                'alert_id': self.id,
            })

    @api.depends('tests', 'tests.test_status')
    def _compute_status(self):
        for alert in self:
            failed_tests = [test for test in alert.tests if test.test_status == 'fail']
            if not alert.tests:
                alert.final_status = 'wait'
            elif failed_tests:
                alert.final_status = 'fail'
            else:
                alert.final_status = 'pass'


class QualityTest(models.Model):
    _name = 'quality.test'
    _inherit = ['mail.thread']
    _order = "id desc"

    quality_measure = fields.Many2one('quality.measure', string='Measure', index=True, ondelete='cascade',track_visibility='onchange')
    alert_id = fields.Many2one('quality.alert', string="Quality Alert",track_visibility='onchange')
    name = fields.Char('Name', related="quality_measure.name", required=True)
    product_id = fields.Many2one('product.product', string='Product', related='alert_id.product_id')
    test_type = fields.Selection(related='quality_measure.type', string='Test Type', required=True, readonly=True)
    quantity_min = fields.Float(related='quality_measure.quantity_min', string='Min-Value', store=True, readonly=True)
    quantity_max = fields.Float(related='quality_measure.quantity_max', string='Max-Value', store=True, readonly=True)
    test_user_id = fields.Many2one('res.users', string='Assigned to', track_visibility='onchange')
    test_result = fields.Float(string='Result', track_visibility='onchange')
    test_result2 = fields.Selection([
        ('satisfied', 'Satisfied'),
        ('unsatisfied', 'Unsatisfied')], string='Result', track_visibility='onchange')
    test_status = fields.Selection(compute="_compute_status",
                                   selection=[('pass', 'Passed'),
                                              ('fail', 'Failed')],
                                   store=True, string='Status', track_visibility='onchange')

    @api.depends('test_result', 'test_result2')
    def _compute_status(self):
        for test in self:
            if test.test_type == 'quantity':
                if test.quantity_min <= test.test_result <= test.quantity_max:
                    test.test_status = 'pass'
                else:
                    test.test_status = 'fail'
            else:
                if test.test_result2 == 'satisfied':
                    test.test_status = 'pass'
                else:
                    test.test_status = 'fail'
