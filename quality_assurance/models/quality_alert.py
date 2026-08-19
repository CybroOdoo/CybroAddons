# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models, _


class QualityAlert(models.Model):
    """Quality alert generated from stock operations."""
    _name = 'quality.alert'
    _description = 'Quality Alert'
    _inherit = ['mail.thread']
    _order = "date asc, id desc"

    name = fields.Char(
        string='Name',
        required=True,
        default=lambda self: _('New'),
        copy=False
    )
    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        tracking=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        index=True,
        ondelete='cascade'
    )
    picking_id = fields.Many2one(
        'stock.picking',
        string='Source Operation'
    )
    origin = fields.Char(
        string='Source Document',
        help="Reference of the document that produced this alert.",
        readonly=True
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.user.company_id.id,
        index=1
    )
    user_id = fields.Many2one(
        'res.users',
        string='Created by',
        default=lambda self: self.env.user.id
    )
    tests = fields.One2many(
        'quality.test',
        'alert_id',
        string="Tests"
    )
    final_status = fields.Selection(
        compute="_compute_final_status",
        selection=[
            ('wait', 'Waiting'),
            ('pass', 'Passed'),
            ('fail', 'Failed')
        ],
        store=True,
        string='Status',
        default='fail',
        tracking=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('quality.alert') or _('New')
        return super().create(vals_list)

    @api.depends('tests', 'tests.test_status')
    def _compute_final_status(self):
        """Compute final status from related test results."""
        for alert in self:
            failed_tests = [
                test for test in alert.tests
                if test.test_status == 'fail'
            ]
            if not alert.tests:
                alert.final_status = 'wait'
            elif failed_tests:
                alert.final_status = 'fail'
            else:
                alert.final_status = 'pass'


    def action_generate_tests(self):
        """Generate quality tests for the selected product and picking."""
        quality_measure = self.env['quality.measure']
        domain = [('product_id', '=', self.product_id.id)]
        if self.picking_id:
            domain.append(('picking_type_ids', 'in', self.picking_id.picking_type_id.id))
        measures = quality_measure.search(domain)
        for measure in measures:
            self.env['quality.test'].create({
                'quality_measure_id': measure.id,
                'alert_id': self.id,
            })
