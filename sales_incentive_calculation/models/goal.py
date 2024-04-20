# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: ASWIN A K (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from odoo import fields, models


class Goals(models.Model):
    """
    Extends the base 'gamification.goal' model to include additional fields
    'target_achievement_percentage' and 'incentive'.
    The 'target_achievement_percentage' field is computed based on the current
    and target goals, and 'incentive' represents the calculated incentive for
    the goal.
    """
    _inherit = 'gamification.goal'

    target_achievement_percentage = fields.Float(
        string='percentage',
        compute='_compute_target_achievement_percentage',
        help='Target Achievement Percentage')
    incentive = fields.Float(string='Incentive')

    def _compute_target_achievement_percentage(self):
        """
            Calculates target_achievement_percentage
        """
        for rec in self:
            rec.target_achievement_percentage = False
            if rec.target_goal != 0:
                rec.target_achievement_percentage = (
                        rec.current/rec.target_goal)*100
