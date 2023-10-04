/*!
 * Built by Revolist
 */
import { setMode } from '@stencil/core/internal/client';
export { setAssetPath, setPlatformOptions } from '@stencil/core/internal/client';
import { T as ThemeService } from './revo-grid.js';
export { RevoGrid, defineCustomElement as defineCustomElementRevoGrid } from './revo-grid.js';
export { RevogrClipboard, defineCustomElement as defineCustomElementRevogrClipboard } from './revogr-clipboard.js';
export { RevogrData, defineCustomElement as defineCustomElementRevogrData } from './revogr-data.js';
export { RevogrEdit, defineCustomElement as defineCustomElementRevogrEdit } from './revogr-edit.js';
export { RevogrFilterPanel, defineCustomElement as defineCustomElementRevogrFilterPanel } from './revogr-filter-panel.js';
export { RevogrFocus, defineCustomElement as defineCustomElementRevogrFocus } from './revogr-focus.js';
export { RevogrHeader, defineCustomElement as defineCustomElementRevogrHeader } from './revogr-header.js';
export { RevogrOrderEditor, defineCustomElement as defineCustomElementRevogrOrderEditor } from './revogr-order-editor.js';
export { RevogrOverlaySelection, defineCustomElement as defineCustomElementRevogrOverlaySelection } from './revogr-overlay-selection.js';
export { RevogrRowHeaders, defineCustomElement as defineCustomElementRevogrRowHeaders } from './revogr-row-headers.js';
export { RevogrScrollVirtual, defineCustomElement as defineCustomElementRevogrScrollVirtual } from './revogr-scroll-virtual.js';
export { RevogrTempRange, defineCustomElement as defineCustomElementRevogrTempRange } from './revogr-temp-range.js';
export { RevogrViewportScroll, defineCustomElement as defineCustomElementRevogrViewportScroll } from './revogr-viewport-scroll.js';

setMode(elm => {
  let theme = elm.theme || elm.getAttribute('theme');
  if (typeof theme === 'string') {
    theme = theme.trim();
  }
  const parsedTheme = ThemeService.getTheme(theme);
  if (parsedTheme !== theme) {
    elm.setAttribute('theme', parsedTheme);
  }
  return parsedTheme;
});
