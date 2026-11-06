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
# pylint: disable=missing-module-docstring,import-error,no-name-in-module,wrong-import-order
from . import controllers, models
from odoo.addons.payment import reset_payment_provider, setup_provider


def post_init_hook(env):
    """Post init hook to setup provider."""
    setup_provider(env, 'myfatoorah')


def uninstall_hook(env):
    """Uninstall hook to reset provider."""
    reset_payment_provider(env, 'myfatoorah')
