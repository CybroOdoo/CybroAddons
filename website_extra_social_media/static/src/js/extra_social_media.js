/** @odoo-module **/

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class ExtraSocialMedia extends Interaction {
    static selector = ".extra_social_media";

    async start() {
        // Keep every icon visible in the Website Builder for editing.
        if (document.body.classList.contains('editor_enable')) {
            this.el.querySelectorAll('a').forEach((link) => {
                link.classList.remove('d-none');
                link.style.display = '';
            });
            return;
        }

        try {
            const result = await rpc('/website/social_media/values', {});
            this.toggleSocialMediaIcons(result);
        } catch (err) {
            console.error("Error fetching extra social media settings:", err);
        }
    }

    toggleSocialMediaIcons(result) {
        if (!result) return;

        const socialMediaPlatforms = Object.keys(result);

        socialMediaPlatforms.forEach((platform) => {
            const val = result[platform];
            const els = this.el.querySelectorAll(`.extra_social_media_${platform}`);
            els.forEach((link) => {
                if (val) {
                    link.classList.remove('d-none');
                    link.style.display = '';
                    let href = val;
                    if (platform === 'whatsapp' && !val.startsWith('http')) {
                        href = 'https://api.whatsapp.com/send?phone=' + encodeURIComponent(val);
                    } else if (!val.startsWith('http')) {
                        href = 'https://' + val;
                    }
                    link.setAttribute('href', href);
                } else {
                    link.classList.add('d-none');
                    link.style.display = 'none';
                }
            });
        });

        // Always show the home link. Unconfigured social links remain hidden.
        this.el.querySelectorAll('.extra_social_media_home').forEach((link) => {
            link.classList.remove('d-none');
            link.style.display = '';
        });
    }
}

registry.category("public.interactions").add("website_extra_social_media.extra_social_media", ExtraSocialMedia);
