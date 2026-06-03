# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
################################################################################
from odoo import fields,models


class InsurancePolicySubCategory(models.Model):
    """
        This model represents the categories under which insurance policies are grouped.
        Each category has a unique name and code to identify it.
        """
    _name = 'insurance.policy.sub.category'
    _description = 'Insurance Policy Sub Category'

    name = fields.Char(
        string='Sub Category Name',
        required=True,
        help='Name of the insurance policy sub-category.'
    )
    category_id = fields.Many2one(
        comodel_name='insurance.policy.category',
        string='Category',
        required=True,
        help='The main category to which this sub-category belongs.'
    )
