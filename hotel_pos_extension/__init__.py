# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from . import models
from . import wizard

def post_init_hook(env):
    """Ensure the payment method is active after installation."""
    payment_method = env.ref('hotel_pos_extension.pos_payment_method_pay_at_checkout', raise_if_not_found=False)
    if payment_method and not payment_method.active:
        payment_method.active = True

def uninstall_hook(env):
    """Archive or unlink the Pay at Checkout pos payment method on uninstallation."""
    payment_method = env.ref('hotel_pos_extension.pos_payment_method_pay_at_checkout', raise_if_not_found=False)
    if payment_method:
        try:
            with env.cr.savepoint():
                payment_method.unlink()
        except Exception:
            payment_method.write({'active': False})
