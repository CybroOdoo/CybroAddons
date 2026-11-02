import { Plugin } from "@html_editor/plugin";
import { BuilderAction } from "@html_builder/core/builder_action";
import { registry } from "@web/core/registry";

const YOUTUBE_HOSTS = ["youtube.com", "www.youtube.com", "m.youtube.com"];
const VIDEO_ID_RE = /^[\w-]{6,20}$/;

/**
 * Return a link that is safe to use as the source of an iframe, or an empty
 * string. Only http(s) links are accepted and YouTube watch links are turned
 * into embed links.
 */
export function normalizeUrl(value) {
    let url;
    try {
        url = new URL((value || "").trim());
    } catch {
        return "";
    }
    if (!["http:", "https:"].includes(url.protocol)) {
        return "";
    }
    let videoId;
    if (url.hostname === "youtu.be") {
        videoId = url.pathname.replace(/^\/|\/$/g, "");
    } else if (YOUTUBE_HOSTS.includes(url.hostname) && url.pathname === "/watch") {
        videoId = url.searchParams.get("v") || "";
    } else {
        return url.href;
    }
    return VIDEO_ID_RE.test(videoId) ? `https://www.youtube.com/embed/${videoId}` : "";
}

export class DynamicLinkOptionPlugin extends Plugin {
    static id = "dynamicLinkOption";
    resources = {
        builder_actions: {
            DynamicLinkAction,
        },
    };
}

export class DynamicLinkAction extends BuilderAction {
    static id = "dynamicLink";

    getValue({ editingElement }) {
        return editingElement.dataset.linkUrl || "";
    }

    apply({ editingElement, value }) {
        const url = normalizeUrl(value);
        const frameEl = editingElement.querySelector(".s_dynamic_link_frame");
        if (!frameEl) {
            return;
        }
        frameEl.replaceChildren();
        if (!url) {
            delete editingElement.dataset.linkUrl;
            return;
        }
        editingElement.dataset.linkUrl = url;
        const iframeEl = editingElement.ownerDocument.createElement("iframe");
        iframeEl.src = url;
        iframeEl.loading = "lazy";
        iframeEl.allowFullscreen = true;
        iframeEl.classList.add("w-100", "h-100", "border-0");
        frameEl.appendChild(iframeEl);
    }
}

registry.category("website-plugins").add(DynamicLinkOptionPlugin.id, DynamicLinkOptionPlugin);
