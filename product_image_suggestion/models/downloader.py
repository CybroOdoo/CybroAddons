# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import logging
from pathlib import Path
import re
import shutil
from .bing import Bing

_logger = logging.getLogger(__name__)


def download(query, limit=100, output_dir=None, adult_filter_off=True,
             force_replace=False, timeout=60, filter="", verbose=True):
    """Download the images within the limit provided"""
    adult = 'off' if adult_filter_off else 'on'
    image_dir = None
    if output_dir:
        # Sanitize query to prevent path traversal outside output_dir
        safe_query = re.sub(r'[/\\.]+', '_', query).strip('_') or 'query'
        base_dir = Path(output_dir).resolve()
        image_dir = (base_dir / safe_query).resolve()
        if not image_dir.is_relative_to(base_dir):
            image_dir = (base_dir / 'query').resolve()

        if force_replace and image_dir.is_dir():
            shutil.rmtree(image_dir)
        try:
            if not image_dir.is_dir():
                image_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            _logger.exception("Failed to create image directory: %s", image_dir)
            return set()

    bing = Bing(query, limit, image_dir, adult, timeout, filter, verbose)
    return bing.run()
