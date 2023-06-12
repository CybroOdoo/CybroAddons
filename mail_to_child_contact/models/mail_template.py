# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Afra MP (odoo@cybrosys.com)
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
################################################################################
from odoo import models


class MailTemplate(models.Model):
    """Inherit the class to send mail to all customer contacts."""
    _inherit = "mail.template"

    def generate_recipients(self, results, res_ids):
        """Super the function to add all child contacts automatically fill in
         the field partner_ids"""
        res = super(MailTemplate, self).generate_recipients(results, res_ids)
        res_id = res_ids[0]
        partner_id = results[res_id]['partner_ids'][0]
        partner_ids = self.env['res.partner'].sudo(). \
            search([('commercial_partner_id', '=', partner_id)])
        if partner_ids:
            results[res_id]['partner_ids'] = partner_ids
        return res
