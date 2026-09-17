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
