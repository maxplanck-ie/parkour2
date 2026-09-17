// GoatCounter event tracking for modal/dialog opens and their save actions.
// Naming: "modal-<name>" on open, "save-<name>" on a successful save/submit.
// Guarded because count.js loads async and may not be ready on a fast click.
export function trackEvent(path, title) {
  if (typeof window === "undefined" || !window.goatcounter) return;
  window.goatcounter.count({ path, title, event: true });
}

export function trackModalOpen(name, title) {
  trackEvent(`modal-${name}`, title);
}

export function trackModalSave(name, title) {
  trackEvent(`save-${name}`, title);
}

// QC gate outcomes: fired whenever a library/sample status is set to a
// negative statusMap value (Quality Check Failed / Compromised), wherever
// that action lives in the app.
export function trackQcEvent(name, title) {
  trackEvent(`qc-${name}`, title);
}
