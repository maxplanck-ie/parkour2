/* RevoGrid custom elements */
export { RevoGridComponent as RevoGrid } from '../dist/types/components/revo-grid/revo-grid';
export { Clipboard as RevogrClipboard } from '../dist/types/components/clipboard/revogr-clipboard';
export { RevogrData as RevogrData } from '../dist/types/components/data/revogr-data';
export { Edit as RevogrEdit } from '../dist/types/components/overlay/revogr-edit';
export { FilterPanel as RevogrFilterPanel } from '../dist/types/plugins/filter/filter.pop';
export { RevogrFocus as RevogrFocus } from '../dist/types/components/selection-focus/revogr-focus';
export { RevogrHeaderComponent as RevogrHeader } from '../dist/types/components/header/revogr-header';
export { OrderEditor as RevogrOrderEditor } from '../dist/types/components/order/revogr-order-editor';
export { OverlaySelection as RevogrOverlaySelection } from '../dist/types/components/overlay/revogr-overlay-selection';
export { RevogrRowHeaders as RevogrRowHeaders } from '../dist/types/components/rowHeaders/revogr-row-headers';
export { RevogrScrollVirtual as RevogrScrollVirtual } from '../dist/types/components/scrollable/revogr-scroll-virtual';
export { RevogrFocus as RevogrTempRange } from '../dist/types/components/selection-temp-range/revogr-temp-range';
export { RevogrViewportScroll as RevogrViewportScroll } from '../dist/types/components/scroll/revogr-viewport-scroll';

/**
 * Used to manually set the base path where assets can be found.
 * If the script is used as "module", it's recommended to use "import.meta.url",
 * such as "setAssetPath(import.meta.url)". Other options include
 * "setAssetPath(document.currentScript.src)", or using a bundler's replace plugin to
 * dynamically set the path at build time, such as "setAssetPath(process.env.ASSET_PATH)".
 * But do note that this configuration depends on how your script is bundled, or lack of
 * bundling, and where your assets can be loaded from. Additionally custom bundling
 * will have to ensure the static assets are copied to its build directory.
 */
export declare const setAssetPath: (path: string) => void;

export interface SetPlatformOptions {
  raf?: (c: FrameRequestCallback) => number;
  ael?: (el: EventTarget, eventName: string, listener: EventListenerOrEventListenerObject, options: boolean | AddEventListenerOptions) => void;
  rel?: (el: EventTarget, eventName: string, listener: EventListenerOrEventListenerObject, options: boolean | AddEventListenerOptions) => void;
}
export declare const setPlatformOptions: (opts: SetPlatformOptions) => void;
export * from '../dist/types';
