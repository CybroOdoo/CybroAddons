# -*- coding: utf-8 -*-
#############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class OilInspectionPoint(models.Model):
    """
    Inspection Point — a reusable template that defines what checklist criteria
    should be evaluated for a given product or product category.

    When an MO is marked Done and the user clicks 'Inspect', the system looks
    up matching Inspection Points for the MO's product and builds the
    Inspection Order lines from these criteria.
    """
    _name = 'oil.inspection.point'
    _description = 'Oil Inspection Point'
    _order = 'sequence, id'

    name = fields.Char(
        string='Inspection Point',
        required=True,
        help='Name of this inspection point / checklist template.',
    )
    sequence = fields.Integer(default=10, help="Order in which this item appears.")
    active = fields.Boolean(default=True,
                            help="Uncheck to archive without deleting.")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        help="Select the company.")

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help='Restrict to a specific product. Leave empty to match all products.')
    product_category_id = fields.Many2one(
        'product.category',
        string='Product Category',
        help='Restrict to a product category. Leave empty to match all categories.')
    responsible_id = fields.Many2one(
        'res.users',
        string='Default Inspector',
        help='Default inspector assigned when an Inspection Order is created from this point.')
    note = fields.Html(
        string='Instructions',
        help='General instructions shown to the inspector.')
    criteria_ids = fields.One2many(
        'oil.inspection.point.criteria',
        'point_id',
        string='Checklist Criteria',
        help="Lists the checklist Criteria.")

    def matches_product(self, product):
        """
        Determines if this inspection point template applies to the given product 
        based on product-specific or category-specific rules.
        """
        self.ensure_one()
        if not self.product_id and not self.product_category_id:
            return True
        if self.product_id and self.product_id == product:
            return True
        if self.product_category_id and self.product_category_id == product.categ_id:
            return True
        return False


class OilInspectionPointCriteria(models.Model):
    """A single checklist item belonging to an Inspection Point."""
    _name = 'oil.inspection.point.criteria'
    _description = 'Oil Inspection Point Criteria'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10, help="Enter the sequence.")
    point_id = fields.Many2one(
        'oil.inspection.point',
        string='Inspection Point',
        required=True,
        ondelete='cascade',
        help="Select the inspection Point.")
    name = fields.Char(
        string='Check Item',
        required=True,
        help='The specific item or control point to be inspected.',)
    guideline = fields.Text(
        string='Guideline',
        help='Guidance to help the inspector evaluate this item.',)
    is_critical = fields.Boolean(
        string='Critical',
        default=False,
        help='A Fail on a critical item automatically fails the entire inspection.')
    evaluation_type = fields.Selection(
        [('manual', 'Pass/Fail'), ('percentage', 'Percentage')],
        string='Evaluation Type',
        default='manual',
        required=True,
        help="Whether this criterion is evaluated manually (pass/fail) or by percentage threshold.")
    target_value = fields.Float(
        string='Target Value (%)',
        default=0.5,
        help='The required percentage to pass (e.g. 0.5 for 50%).')

    @api.constrains('name')
    def _check_name(self):
        """
        Ensure the check item name is not empty or whitespace.
        """
        for rec in self:
            if not rec.name or not rec.name.strip():
                raise ValidationError(_('Check item name cannot be empty.'))
