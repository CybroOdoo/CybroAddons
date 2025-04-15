# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import fields, models


class InsurancePolicy(models.Model):
    """
    Model for managing insurance policies related to fleet rental contracts.
    """
    _name = 'insurance.policy'
    _description = 'Insurance Policy'

    policy_number = fields.Char(
        string='Policy Number',
        required=True,
        help='Unique identifier for the insurance policy.')
    name = fields.Char(
        string='Name',
        required=True,
        help='Name of the insurance policy.')
    description = fields.Char(
        string='Description',
        help='Brief description of the insurance policy.')
    document = fields.Binary(
        string='Document',
        help='Upload the document related to the insurance policy.')
    file_name = fields.Char(
        string="File Name",
        help='File Name of the Document')

    policy_amount = fields.Float(
        string='Policy Amount',
        help='Total amount covered by the insurance policy.')
    contract_id = fields.Many2one('fleet.rental.contract',
                                  string='Contract Rent',
                                  help='Reference to the vehicle rent.')
