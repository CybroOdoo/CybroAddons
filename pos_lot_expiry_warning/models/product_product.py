# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
################################################################################
from odoo import fields, models, api


class ProductProduct(models.Model):
    """The ProductProduct class is inherit for adding a function."""
    _inherit = 'product.product'

    @api.model
    def lot_expiry_check(self, product, lot):
        """This function is used for finding the lot's expiration date"""
        lots = self.env['stock.lot'].search([('name', '=', lot),
                                             ('product_id', '=', product)], limit=1)
        if not lots:
            return 0

        now = fields.Datetime.now()

        if lots.expiration_date and lots.expiration_date <= now:
            return [2, lots.expiration_date]  # expired

        if lots.alert_date and lots.alert_date <= now:
            return [1, lots.expiration_date]  # alert
        return 1
