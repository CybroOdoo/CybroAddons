# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1) It is forbidden to publish, distribute, sublicense, or
#    sell copies of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
#    OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    """This class inherits model 'res.partner' and adds fields"""
    _inherit = 'res.partner'
    _order = 'sequence'
    _check_company_auto = True

    locations = fields.Many2one('route.line', string='Location',
                                help="Location of route.")
    sequence = fields.Integer(default=10)

    def get_all_dues(self):
        """This function gives all the dues and invoices details
        of selected customer"""
        query = """select name,invoice_date_due,amount_residual_signed from account_move where partner_id in
                (select id from res_partner where id =%s or parent_id=%s) and state != 'draft' and 
                amount_residual_signed != 0
                order by create_date"""
        self.env.cr.execute(query, [self.id, self.id])
        list = self.env.cr.dictfetchall()
        return list
