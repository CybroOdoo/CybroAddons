"""Cybersource"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri V(<odoo@cybrosys.com>)
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
from . import controllers
from . import model

from odoo.addons.payment import setup_provider, reset_payment_provider


def post_init_hook(cr, registry):
    """ Create `account.payment.method` records for the installed payment providers. """
    setup_provider(cr, registry, 'cybersource')

def uninstall_hook(cr, registry):
    """ Delete `account.payment.method` records created for the installed payment providers. """
    reset_payment_provider(cr, registry, 'cybersource')
