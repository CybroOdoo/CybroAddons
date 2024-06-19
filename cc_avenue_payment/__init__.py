# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from . import controllers
from . import models
from odoo.addons.payment import setup_provider, reset_payment_provider


def post_init_hook(cr, registry):
    """Function to set up the payment provider 'CCAvenue' after
    module installation."""
    setup_provider(cr, registry, 'avenue')


def uninstall_hook(cr, registry):
    """Function to reset the payment provider 'CCAvenue' before module
    uninstallation."""
    reset_payment_provider(cr, registry, 'avenue')
