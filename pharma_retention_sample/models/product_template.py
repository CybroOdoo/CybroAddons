# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    """Adds the reserve (retention) sample rule to pharmaceutical products."""
    _inherit = 'product.template'

    retention_required = fields.Boolean(
        string='Reserve Sample Required',
        tracking=True,
        help='Released batches of this product without a confirmed reserve '
             'sample are listed under Missing Reserve Samples and get a daily '
             'reminder. Release itself is not held up.',
    )
    retention_period_months = fields.Integer(
        string='Held Beyond Expiry (Months)',
        default=12,
        tracking=True,
        help='How long the reserve sample is kept after the batch expiry '
             'date before it falls due for disposal.',
    )
    retention_container = fields.Char(
        string='Default Container',
        help='Container normally used for the reserve sample '
             '(e.g. "Amber glass bottle, 100 mL, in final pack").',
    )
    retention_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Default Retention Location',
        domain="[('usage', '=', 'internal'), ('pharma_is_retention_location', '=', True)]",
        help='Location normally used for this product\'s reserve samples. '
             'Leave empty to use the company default from Settings.',
    )
    retention_exam_interval_months = fields.Integer(
        string='Visual Examination Every (Months)',
        default=12,
        help='Interval between periodic visual examinations of the reserve '
             'sample. Zero disables the examination schedule.',
    )

    @api.constrains('retention_period_months', 'retention_exam_interval_months')
    def _check_retention_rule(self):
        """Keep the retention rule values in a usable range."""
        for rec in self:
            if rec.retention_period_months < 0 or rec.retention_exam_interval_months < 0:
                raise ValidationError(self.env._(
                    "Retention and examination periods cannot be negative."))
