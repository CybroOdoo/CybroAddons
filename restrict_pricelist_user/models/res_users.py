# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mehjabin Farsana (Contact : odoo@cybrosys.com)
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

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_restricted = fields.Boolean(string="Restrict Price List", help="Restrict Price List for users")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        is_restricted = params.get_param('restrict_pricelist_user.is_restricted')
        res.update(is_restricted=is_restricted,
                   )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            "restrict_pricelist_user.is_restricted",
            self.is_restricted)


class ResUsers(models.Model):
    _inherit = 'res.users'

    pricelist_ids = fields.Many2many('product.pricelist', 'rel_user_pricelist', string="Price Lists")
    is_restricted = fields.Boolean(string="Restricted", compute="_compute_is_pricelist_restricted")

    def _compute_is_pricelist_restricted(self):
        params = self.env['ir.config_parameter'].sudo()
        pricelist_restricted = params.get_param('restrict_pricelist_user.is_restricted')

        for rec in self:
            rec.is_restricted = True if pricelist_restricted else False
