import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class DynamicLink extends Interaction {
    static selector = ".s_dynamic_link";

    start() {
        const url = this.el.dataset.linkUrl;
        const frameEl = this.el.querySelector(".s_dynamic_link_frame");
        if (!frameEl || !url || !/^https?:\/\//i.test(url)) {
            return;
        }
        if (frameEl.querySelector(`iframe[src="${CSS.escape(url)}"]`)) {
            return;
        }
        const iframeEl = document.createElement("iframe");
        iframeEl.src = url;
        iframeEl.loading = "lazy";
        iframeEl.allowFullscreen = true;
        iframeEl.classList.add("w-100", "h-100", "border-0");
        this.insert(iframeEl, frameEl);
    }
}

registry.category("public.interactions").add("dynamic_link_snippet.dynamic_link", DynamicLink);
