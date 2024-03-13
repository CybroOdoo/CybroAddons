# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Jabin MP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models


class ResPartner(models.Model):
    """This class extends the 'res.partner' model to add the
    'action_open_whatsapp' method.It opens a WhatsApp Message Wizard for the
     partner."""
    _inherit = 'res.partner'

    def action_open_whatsapp(self):
        """This method opens a WhatsApp Message Wizard for the partner."""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Send WhatsApp Message to {self.name}',
            'res_model': 'whatsapp.message',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'infobip_whatsapp_integration.view_whatsapp_message_form').id,
            'target': 'new',
            'context': {
                'default_partner_name': self.name,
                'default_partner_mobile': self.mobile,
            },
        }
