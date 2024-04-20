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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Challenge(models.Model):
    """
    Extends the base 'gamification.challenge' model to include an additional
    field 'incentive_calculation' that allows specifying whether the challenge
    should be used in incentive calculations.
    """
    _inherit = 'gamification.challenge'

    incentive_calculation = fields.Boolean(
        string='Use in incentive calculation', copy=False)

    @api.onchange('incentive_calculation')
    def _onchange_incentive_calculation(self):
        """
            Checks if any gamification_challenge is
            active for incentive_calculation
        """
        if self.search([('incentive_calculation', '=', True)]):
            if self.incentive_calculation:
                raise UserError(
                    _('Another goal already active for incentive calculation'))
