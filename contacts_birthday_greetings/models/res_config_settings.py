# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra K (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """ Inherit the base settings to add the greetings mail template. """
    _inherit = 'res.config.settings'

    greetings_mail_template_id = fields.Many2one(
        comodel_name='mail.template',
        string='Email Template',
        domain="[('model', '=', 'res.partner')]",
        help="Choose the email template to send greeting message to the customer.")

    def set_values(self):
        """
        Set values for the fields greetings_mail_template_id.
        """
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'contacts_birthday_greetings.greetings_mail_template_id',
            self.greetings_mail_template_id.id)

    @api.model
    def get_values(self):
        """
        Return values for the fields greetings_mail_template_id.
        """
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        greetings_mail_template_id = params.get_param(
            'contacts_birthday_greetings.greetings_mail_template_id')
        res.update(
            greetings_mail_template_id=int(greetings_mail_template_id),
        )
        return res
