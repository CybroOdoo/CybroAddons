# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-August Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vyshnav AR (Contact : odoo@cybrosys.com)
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
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    response_ids = fields.One2many('response.data', 'des', String='Response')


class Response(models.Model):
    _name = "response.data"
    _order = "id"

    des = fields.Many2one('res.partner', readonly=1)
    arn = fields.Char(string='ARN Number', readonly=1)
    ret_prd = fields.Date(string='Tax Period', readonly=1)
    mof = fields.Char(string='Mode Of Filing', readonly=1)
    dof = fields.Char(string='Date of Filing', readonly=1)
    rtn_type = fields.Char(string='Return Type', readonly=1)
    status = fields.Char(string='Status', readonly=1)
    valid = fields.Selection([('Y', 'Yes'), ('N', 'No')], string='Valid',
                             readonly=1)
