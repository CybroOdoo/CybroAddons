# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(<https://www.cybrosys.com>)
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
#
#############################################################################
"""Franchise Dealer Agreement Model"""
from odoo import fields, models


class FranchiseAgreement(models.Model):
    """Franchise Agreement Model."""
    _name = "franchise.agreement"
    _description = "Franchise Agreement Type."
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "agreement_type"

    agreement_type = fields.Selection(
        [('monthly', 'Monthly'), ('yearly', 'Yearly')],
        string='Agreement Type',
        help='Franchise Agreement type')
    agreement_body = fields.Html(string='Agreement Body', render_engine='qweb',
                                 translate=True,
                                 help='Franchise Agreement contents',
                                 prefetch=True, sanitize=False)
