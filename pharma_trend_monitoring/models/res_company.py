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

# Fallbacks for unset values, read through _pharma_trend_settings().
TREND_DEFAULTS = {
    'pharma_trend_min_history': 2,
    'pharma_trend_range_sigma': 3.0,
}


class ResCompany(models.Model):
    """Per-site settings of out-of-trend monitoring."""
    _inherit = 'res.company'

    pharma_trend_min_history = fields.Integer(
        string='Results Before Trending Starts',
        default=2,
        help='Number of approved results a watched parameter needs before QA '
             'can approve its normal range. Until then nothing is flagged.',
    )
    pharma_trend_range_sigma = fields.Float(
        string='Normal Range Width (σ)',
        default=3.0,
        help='The normal range is the mean of the approved results plus or '
             'minus this many standard deviations.',
    )

    @api.constrains('pharma_trend_min_history', 'pharma_trend_range_sigma')
    def _check_pharma_trend_settings(self):
        """Keep the trend settings statistically meaningful."""
        for company in self:
            # The values as entered, not the fallbacks: a 0 must be refused
            # rather than silently read as the default.
            # A standard deviation needs two values; anything above is the site's call.
            if company.pharma_trend_min_history < 2:
                raise ValidationError(self.env._(
                    'At least 2 approved results are needed before a normal '
                    'range can be approved.'))
            if company.pharma_trend_range_sigma <= 0:
                raise ValidationError(self.env._('The normal range width must be greater than zero.'))

    def _pharma_trend_settings(self):
        """The trend settings of this company, with defaults for unset values."""
        self.ensure_one()
        return {key: self[key] or default for key, default in TREND_DEFAULTS.items()}
