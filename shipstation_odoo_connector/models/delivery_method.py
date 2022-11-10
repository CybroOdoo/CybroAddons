# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################

from odoo import fields, models, api, _


class DeliveryMethod(models.Model):
    _name = 'shipstation.delivery'
    _description = "Shipstation Delivery"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    account_number = fields.Char(string="Account Number")
    requires_funded_account = fields.Boolean(string="Requires Funded Account")
    balance = fields.Char(string="Balance")
    nick_name = fields.Char(string="Nickname")
    shipping_providerid = fields.Char(string="Shipping Provider")
    primary = fields.Boolean(default=False, string="Primary")
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company,string="Company id")
