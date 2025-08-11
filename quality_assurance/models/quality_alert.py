# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Dhanya B(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models, _


class QualityAlert(models.Model):
    _name = 'quality.alert'
    _description = 'Quality Alert'
    _inherit = ['mail.thread']
    _order = "date asc, id desc"

    name = fields.Char('Name', required=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now(),
                           track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='Product',
                                 index=True, ondelete='cascade')
    picking_id = fields.Many2one('stock.picking', string='Source Operation')
    origin = fields.Char(string='Source Document',
                         help="Reference of the document that produced this alert.",
                         readonly=True)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda
                                     self: self.env.user.company_id.id, index=1)
    user_id = fields.Many2one('res.users', string='Created by',
                              default=lambda self: self.env.user.id)
    tests = fields.One2many('quality.test',
                            'alert_id', string="Tests")
    final_status = fields.Selection(compute="_compute_final_status",
                                    selection=[('wait', 'Waiting'),
                                               ('pass', 'Passed'),
                                               ('fail', 'Failed')],
                                    store=True, string='Status',
                                    default='fail', track_visibility='onchange')

    @api.depends('tests', 'tests.test_status')
    def _compute_final_status(self):
        """Computes the `final_status` field based on the related tests'
         statuses."""
        for alert in self:
            failed_tests = [test for test in alert.tests if
                            test.test_status == 'fail']
            if not alert.tests:
                alert.final_status = 'wait'
            elif failed_tests:
                alert.final_status = 'fail'
            else:
                alert.final_status = 'pass'

    def action_generate_tests(self):
        """Generates quality tests for the product associated
         with the current alert."""
        quality_measure = self.env['quality.measure']
        measures = quality_measure.search(
            [('product_id', '=', self.product_id.id),
             ('picking_type_ids', 'in', self.picking_id.picking_type_id.id)])
        for measure in measures:
            self.env['quality.test'].create([{
                'quality_measure_id': measure.id,
                'alert_id': self.id,
            }])
