# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
import os
import io
import logging
import concurrent.futures
import html
import requests

try:
    import polib
except ImportError:
    polib = None

try:
    from deep_translator import GoogleTranslator
except ImportError:
    GoogleTranslator = None

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import trans_export
from odoo.modules import get_module_path

_logger = logging.getLogger(__name__)


class AutomaticTranslationWizard(models.TransientModel):
    """
    Wizard to automatically translate module terms.
    Extracts translatable terms from the selected custom module and
    translates them into the target language using deep_translator with
    robust fallback mechanisms.
    """
    _name = 'automatic.translation.wizard'
    _description = 'Automatic Translation Wizard'

    language_id = fields.Many2one(
        'res.lang',
        required=True,
        help="Select the language you want to translate the module into."
    )
    module_id = fields.Many2one(
        'ir.module.module',
        string='App To Translate',
        required=True,
        domain=[('state', '=', 'installed')],
        help="Select the installed module you want to translate."
    )
    overwrite_existing_terms = fields.Boolean(
        default=False,
        help="If checked, existing translations will be overwritten by the automatic translator."
    )

    def action_translate(self):
        """
        Translates translatable strings of the selected module to the selected language.
        Generates/Updates PO file in the module's i18n directory.
        Uses concurrent translation with robust fallback to avoid rate limits or timeouts.
        """
        if not GoogleTranslator:
            raise UserError(self.env._("Please install 'deep_translator' to use this feature: pip3 install deep_translator"))
        if not polib:
            raise UserError(self.env._("Please install 'polib' to use this feature: pip3 install polib"))

        self.ensure_one()
        module_name = self.module_id.name
        lang_code = self.language_id.code

        # Language code suitable for translators
        target_lang = lang_code.split('_')[0]
        target_lang_mymemory = lang_code.replace('_', '-').split('-')[0]

        try:
            GoogleTranslator(source='auto', target=target_lang)
        except Exception as err:
            raise UserError(self.env._("Invalid language code for translation: %s", target_lang)) from err

        # Quick probe to check if GoogleTranslator is responsive and not rate-limited
        use_google = True
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as probe_executor:
                probe_future = probe_executor.submit(
                    GoogleTranslator(source='auto', target=target_lang).translate, 'Hello'
                )
                if not probe_future.result(timeout=4):
                    _logger.info("GoogleTranslator probe returned empty, falling back to alternate translator.")
                    use_google = False
        except Exception as err:
            _logger.info("GoogleTranslator probe failed, falling back to alternate translator: %s", err)
            use_google = False

        # 1. Export current PO file content for the module in the target language
        buf = io.BytesIO()
        try:
            is_exported = trans_export(lang_code, [module_name], buf, 'po', self.env)
        except Exception as err:
            raise UserError(self.env._("Failed to export module translations: %s", err)) from err

        if not is_exported:
            raise UserError(self.env._("No translatable terms found for module: %s", module_name))

        po_content = buf.getvalue().decode('utf-8')

        # 2. Parse PO content using polib
        try:
            po = polib.pofile(po_content)
        except Exception as err:
            raise UserError(self.env._("Failed to parse PO content: %s", err)) from err

        mod_path = get_module_path(module_name)
        if not mod_path:
            raise UserError(self.env._("Module path not found for %s", module_name))

        i18n_dir = os.path.join(mod_path, 'i18n')
        po_file_path = os.path.join(i18n_dir, f"{lang_code}.po")

        # Load existing disk translations if available so non-empty terms aren't lost
        if not self.overwrite_existing_terms and os.path.exists(po_file_path):
            try:
                disk_po = polib.pofile(po_file_path)
                disk_translations = {item.msgid: item.msgstr for item in disk_po if item.msgid and item.msgstr}
                for entry in po:
                    if entry.msgid in disk_translations and not entry.msgstr:
                        entry.msgstr = disk_translations[entry.msgid]
            except Exception as err:
                _logger.warning("Could not read existing translations from disk: %s", err)

        # 3. Filter entries that need translation
        entries_to_translate = []
        for entry in po:
            if not entry.msgid or not entry.msgid.strip():
                continue

            # If there's an existing translation and we're not overwriting, skip
            if entry.msgstr and not self.overwrite_existing_terms:
                continue

            entries_to_translate.append(entry)

        if not entries_to_translate and not self.overwrite_existing_terms:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': self.env._('Info'),
                    'message': self.env._('No new terms to translate.'),
                    'type': 'info',
                    'sticky': False,
                }
            }

        user_email = self.env.user.email or self.env.company.email or 'admin@cybrosys.com'
        translated_count = 0
        session = requests.Session()
        session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        })

        if entries_to_translate:
            def _translate_entry(entry):
                nonlocal use_google
                text = entry.msgid
                stripped = text.strip()
                if not stripped or stripped.isdigit():
                    return entry, text

                leading = text[:len(text) - len(text.lstrip())]
                trailing = text[len(text.rstrip()):]

                # 1. Try GoogleTranslator if available
                if use_google:
                    try:
                        thread_translator = GoogleTranslator(source='auto', target=target_lang)
                        translated_text = thread_translator.translate(stripped)
                        if translated_text and translated_text.strip():
                            return entry, leading + translated_text.strip() + trailing
                    except Exception as err:
                        _logger.warning("Google translation failed for '%s': %s", stripped, err)
                        use_google = False

                # 2. Fallback to MyMemory translation
                try:
                    url = 'http://api.mymemory.translated.net/get'
                    params = {
                        'q': stripped,
                        'langpair': f'en|{target_lang_mymemory}',
                        'de': user_email,
                    }
                    r = session.get(url, params=params, timeout=8)
                    if r.status_code == 200:
                        data = r.json()
                        if data.get('responseStatus') == 200:
                            trans = data.get('responseData', {}).get('translatedText')
                            if trans and 'QUERY LENGTH LIMIT EXCEEDED' not in trans and 'MYMEMORY WARNING' not in trans:
                                return entry, leading + html.unescape(trans).strip() + trailing
                except Exception as err:
                    _logger.debug("Fallback translation failed for '%s': %s", stripped, err)

                return entry, None

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                for entry, translated_text in executor.map(_translate_entry, entries_to_translate):
                    if translated_text:
                        entry.msgstr = translated_text
                        translated_count += 1

        # Prevent overwriting PO files with blank translations if the service fails
        if entries_to_translate and translated_count == 0:
            raise UserError(self.env._(
                "Translation failed: The translation service was unable to translate terms (rate limit or connection error). "
                "Please check your internet connection or try again later."
            ))

        # 4. Save the generated PO file to the module's i18n directory
        if not os.path.exists(i18n_dir):
            try:
                os.makedirs(i18n_dir)
            except Exception as err:
                raise UserError(self.env._("Could not create i18n directory. Permission denied: %s", err)) from err

        try:
            po.save(po_file_path)
        except Exception as err:
            raise UserError(self.env._("Could not save the PO file. Permission denied: %s", err)) from err

        # Load the newly generated translations into the DB
        try:
            if hasattr(self.module_id, '_update_translations'):
                self.module_id._update_translations(filter_lang=lang_code, overwrite=True)
            elif hasattr(self.env['ir.module.module'], '_load_module_terms'):
                self.env['ir.module.module']._load_module_terms([module_name], [lang_code], overwrite=True)
        except Exception as err:
            _logger.warning("Failed to load newly generated translations into the database: %s", err)

        # Clear in-memory code translations for this module and language
        try:
            from odoo.tools.translate import code_translations
            code_translations.python_translations.pop((module_name, lang_code), None)
            code_translations.web_translations.pop((module_name, lang_code), None)
        except Exception as err:
            _logger.debug("Failed to clear in-memory code translations: %s", err)

        # Signal Odoo to reload the registry to apply field and view translation changes
        self.env.registry.clear_cache()
        if hasattr(self.env['ir.ui.view'], 'clear_caches'):
            self.env['ir.ui.view'].clear_caches()
        if hasattr(self.env.registry, 'registry_invalidated'):
            self.env.registry.registry_invalidated = True
        if hasattr(self.env.registry, 'signal_changes'):
            self.env.registry.signal_changes()

        # Reload the client browser to immediately show translated labels
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
