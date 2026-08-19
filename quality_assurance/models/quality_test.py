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

from odoo import api, fields, models


class QualityTest(models.Model):
    """Quality test generated from quality measures."""
    _name = 'quality.test'
    _description = 'Quality Test'
    _inherit = ['mail.thread']
    _order = "id desc"

    quality_measure_id = fields.Many2one(
        'quality.measure',
        string='Measure',
        index=True,
        ondelete='cascade',
        tracking=True
    )
    alert_id = fields.Many2one(
        'quality.alert',
        string="Quality Alert",
        tracking=True
    )
    name = fields.Char(
        'Name',
        related="quality_measure_id.name",
        required=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        related='alert_id.product_id'
    )
    test_type = fields.Selection(
        related='quality_measure_id.type',
        string='Test Type',
        required=True,
        readonly=True
    )
    quantity_min = fields.Float(
        related='quality_measure_id.quantity_min',
        string='Min-Value',
        store=True,
        readonly=True
    )
    quantity_max = fields.Float(
        related='quality_measure_id.quantity_max',
        string='Max-Value',
        store=True,
        readonly=True
    )
    test_user_id = fields.Many2one(
        'res.users',
        string='Assigned to',
        tracking=True
    )
    test_result = fields.Float(
        string='Result',
        tracking=True
    )
    test_result2 = fields.Selection(
        [('satisfied', 'Satisfied'),
         ('unsatisfied', 'Unsatisfied')],
        string='Result',
        tracking=True
    )
    test_status = fields.Selection(
        compute="_compute_quality_test_status",
        selection=[('pass', 'Passed'),
                   ('fail', 'Failed')],
        store=True,
        string='Status',
        tracking=True
    )

    @api.depends('test_result', 'test_result2')
    def _compute_quality_test_status(self):
        """Compute test status from test results."""
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
