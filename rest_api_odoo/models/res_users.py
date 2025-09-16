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
import logging
from datetime import datetime, timedelta
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


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
        self.ensure_one()

        if not self.api_key or force_new:
            try:
                # Generar una API key más segura usando secrets si está disponible
                alphabet = string.ascii_letters + string.digits
                api_key = ''.join(secrets.choice(alphabet) for _ in range(64))
            except (ImportError, AttributeError):
                # Fallback usando uuid si secrets no está disponible
                api_key = str(uuid.uuid4()).replace('-', '') + str(uuid.uuid4()).replace('-', '')[:32]

            self.sudo().write({
                'api_key': api_key,
                'api_key_created': fields.Datetime.now(),
                'api_key_last_used': None,
                'api_requests_count': 0
            })

        return self.api_key

    def regenerate_api_key(self):
        """Regenera la API key (útil para botón en interfaz)"""
        self.ensure_one()
        return self.generate_api_key(force_new=True)

    def revoke_api_key(self):
        """Revoca la API key actual"""
        self.ensure_one()
        self.sudo().write({
            'api_key': False,
            'api_key_expiry': False,
            'api_key_created': False,
            'api_key_last_used': False
        })
        return True

    def set_api_key_expiry(self, days=None):
        """
        Establece fecha de expiración para la API key
        Args:
            days (int): Días hasta la expiración (default: sin expiración)
        """
        self.ensure_one()
        if days:
            expiry_date = fields.Datetime.now() + timedelta(days=days)
            self.sudo().write({'api_key_expiry': expiry_date})
        else:
            self.sudo().write({'api_key_expiry': False})

    def update_api_key_usage(self):
        """Actualiza estadísticas de uso de la API key"""
        self.ensure_one()
        try:
            self.sudo().write({
                'api_key_last_used': fields.Datetime.now(),
                'api_requests_count': self.api_requests_count + 1
            })
        except Exception as e:
            _logger.warning(f"Could not update API key usage for user {self.id}: {str(e)}")

    @api.model
    def cleanup_expired_api_keys(self):
        """Limpia API keys expiradas (para ejecutar en cron)"""
        try:
            expired_users = self.search([
                ('api_key_expiry', '!=', False),
                ('api_key_expiry', '<', fields.Datetime.now())
            ])

            for user in expired_users:
                try:
                    user.revoke_api_key()
                except Exception as e:
                    _logger.warning(f"Could not revoke API key for user {user.id}: {str(e)}")

            return len(expired_users)
        except Exception as e:
            _logger.error(f"Error in cleanup_expired_api_keys: {str(e)}")
            return 0

    def is_api_key_valid(self):
        """Verifica si la API key es válida y no ha expirado"""
        self.ensure_one()

        if not self.api_key:
            return False

        if self.api_key_expiry and self.api_key_expiry < fields.Datetime.now():
            return False

        return True

    def action_generate_api_key(self):
        """Acción para generar API key desde la interfaz"""
        self.ensure_one()
        try:
            api_key = self.generate_api_key()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'API Key generada exitosamente: {api_key}',
                    'type': 'success',
                    'sticky': True,
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Error generando API Key: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def action_regenerate_api_key(self):
        """Acción para regenerar API key desde la interfaz"""
        self.ensure_one()
        try:
            api_key = self.regenerate_api_key()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'API Key regenerada exitosamente: {api_key}',
                    'type': 'success',
                    'sticky': True,
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Error regenerando API Key: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def action_revoke_api_key(self):
        """Acción para revocar API key desde la interfaz"""
        self.ensure_one()
        try:
            self.revoke_api_key()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'API Key revocada exitosamente',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': f'Error revocando API Key: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }

    # Método legacy para compatibilidad con código anterior
    def generate_api(self, username):
        """Método de compatibilidad con la versión anterior"""
        return self.generate_api_key()

    @api.model
    def get_api_statistics(self):
        """Obtiene estadísticas de uso de API keys"""
        try:
            users_with_keys = self.search([('api_key', '!=', False)])
            active_keys = users_with_keys.filtered(lambda u: u.is_api_key_valid())
            expired_keys = users_with_keys.filtered(lambda u: not u.is_api_key_valid())

            total_requests = sum(users_with_keys.mapped('api_requests_count'))

            return {
                'total_users_with_keys': len(users_with_keys),
                'active_keys': len(active_keys),
                'expired_keys': len(expired_keys),
                'total_api_requests': total_requests,
                'average_requests_per_user': total_requests / len(users_with_keys) if users_with_keys else 0
            }
        except Exception as e:
            _logger.error(f"Error getting API statistics: {str(e)}")
            return {
                'total_users_with_keys': 0,
                'active_keys': 0,
                'expired_keys': 0,
                'total_api_requests': 0,
                'average_requests_per_user': 0
            }
