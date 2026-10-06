/** @odoo-module **/

import { BoardController } from "@board/board_controller";
import { browser } from "@web/core/browser/browser";
import { patch } from "@web/core/utils/patch";

function getColumnTargets(actionCount, layout) {
    const weights = layout.split("-").map((value) => parseInt(value, 10));
    const totalWeight = weights.reduce((sum, value) => sum + value, 0);
    const quotas = weights.map((weight, index) => ({
        index,
        base: Math.floor((actionCount * weight) / totalWeight),
        remainder: ((actionCount * weight) / totalWeight) % 1,
    }));
    let assigned = quotas.reduce((sum, quota) => sum + quota.base, 0);
    quotas
        .slice()
        .sort((left, right) => {
            if (right.remainder !== left.remainder) {
                return right.remainder - left.remainder;
            }
            return left.index - right.index;
        })
        .forEach((quota) => {
            if (assigned >= actionCount) {
                return;
            }
            quotas[quota.index].base += 1;
            assigned += 1;
        });
    return quotas.sort((left, right) => left.index - right.index).map((quota) => quota.base);
}

patch(BoardController.prototype, {
    selectLayout(layout, save = true) {
        const currentColNbr = this.board.colNumber;
        const nextColNbr = layout.split("-").length;
        if (nextColNbr !== currentColNbr) {
            const actions = this.board.columns
                .slice(0, currentColNbr)
                .flatMap((column) => column.actions);
            const targets = getColumnTargets(actions.length, layout);
            this.board.columns.forEach((column) => {
                column.actions = [];
            });
            let offset = 0;
            targets.forEach((count, index) => {
                this.board.columns[index].actions = actions.slice(offset, offset + count);
                offset += count;
            });
        }
        this.board.layout = layout;
        this.board.colNumber = nextColNbr;
        if (save) {
            this.saveBoard();
        }
        if (document.querySelector("canvas")) {
            browser.requestAnimationFrame(() => this.render(true));
        }
    },
});
