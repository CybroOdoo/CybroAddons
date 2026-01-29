# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Subina P(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, SUPERUSER_ID
from odoo.addons.payment import reset_payment_acquirer
from . import controllers
from . import models


def post_init_hook(cr, registry):
    """Change the 'provider' field to 'myfatoorah' on installation of the
    provider"""
    env = api.Environment(cr, SUPERUSER_ID, {})
    acquirer_model = env['payment.acquirer']
    acquirer = acquirer_model.search([('provider', '=', 'myfatoorah')], limit=1)
    if not acquirer:
        acquirer_model.create({
            'name': 'MyFatoorah',
            'provider': 'myfatoorah',
        })


def uninstall_hook(cr, registry):
    """Unlinks the payment provider from model on uninstallation of the
    module"""
    reset_payment_acquirer(cr, registry, 'myfatoorah')
