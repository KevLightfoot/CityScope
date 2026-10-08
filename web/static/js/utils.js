export function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

export function formatNumber(value) {
    if (value === null || value === undefined) {
        return "—";
    }

    const number = Number(value);

    return Number.isFinite(number)
        ? number.toLocaleString()
        : "—";
}

export function formatCurrency(value) {
    if (value === null || value === undefined) {
        return "—";
    }

    const number = Number(value);

    return Number.isFinite(number)
        ? `$${number.toLocaleString()}`
        : "—";
}

export function formatPercent(value) {
    if (value === null || value === undefined) {
        return "—";
    }

    const number = Number(value);

    return Number.isFinite(number)
        ? `${number.toFixed(1)}%`
        : "—";
}