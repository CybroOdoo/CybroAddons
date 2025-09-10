# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (odoo@cybrosys.com)
#    Modified by: Broigm - Improvements in API key management
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
import uuid
import secrets
import string
from datetime import datetime, timedelta
from odoo import fields, models, api


class ResUsers(models.Model):
    """Extensión del modelo de usuarios para gestión de API keys"""
    _inherit = 'res.users'

    api_key = fields.Char(
        string="API Key",
        readonly=True,
        help="Clave API para autenticación en REST API. Se genera automáticamente."
    )
    api_key_expiry = fields.Datetime(
        string="API Key Expiry",
        help="Fecha de expiración de la API key (opcional)"
    )
    api_key_created = fields.Datetime(
        string="API Key Created",
        help="Fecha de creación de la API key"
    )
    api_key_last_used = fields.Datetime(
        string="API Key Last Used",
        help="Última vez que se usó la API key"
    )
    api_requests_count = fields.Integer(
        string="API Requests Count",
        default=0,
        help="Contador de requests realizados con esta API key"
    )

    def generate_api_key(self, force_new=False):
        """
        Genera una nueva API key o devuelve la existente
        Args:
            force_new (bool): Fuerza la generación de una nueva key
        Returns:
            str: API key generada
        """
        if not self.api_key or force_new:
            # Generar una API key más segura
            alphabet = string.ascii_letters + string.digits
            api_key = ''.join(secrets.choice(alphabet) for _ in range(64))

            self.write({
                'api_key': api_key,
                'api_key_created': datetime.now(),
                'api_key_last_used': None,
                'api_requests_count': 0
            })

        return self.api_key

    def regenerate_api_key(self):
        """Regenera la API key (útil para botón en interfaz)"""
        return self.generate_api_key(force_new=True)

    def revoke_api_key(self):
        """Revoca la API key actual"""
        self.write({
            'api_key': False,
            'api_key_expiry': False,
            'api_key_created': False,
            'api_key_last_used': False
        })

    def set_api_key_expiry(self, days=None):
        """
        Establece fecha de expiración para la API key
        Args:
            days (int): Días hasta la expiración (default: sin expiración)
        """
        if days:
            expiry_date = datetime.now() + timedelta(days=days)
            self.api_key_expiry = expiry_date
        else:
            self.api_key_expiry = False

    def update_api_key_usage(self):
        """Actualiza estadísticas de uso de la API key"""
        self.write({
            'api_key_last_used': datetime.now(),
            'api_requests_count': self.api_requests_count + 1
        })

    @api.model
    def cleanup_expired_api_keys(self):
        """Limpia API keys expiradas (para ejecutar en cron)"""
        expired_users = self.search([
            ('api_key_expiry', '!=', False),
            ('api_key_expiry', '<', datetime.now())
        ])

        for user in expired_users:
            user.revoke_api_key()

        return len(expired_users)

    def is_api_key_valid(self):
        """Verifica si la API key es válida y no ha expirado"""
        if not self.api_key:
            return False

        if self.api_key_expiry and self.api_key_expiry < datetime.now():
            return False

        return True

    # Método legacy para compatibilidad con código anterior
    def generate_api(self, username):
        """Método de compatibilidad con la versión anterior"""
        return self.generate_api_key()
