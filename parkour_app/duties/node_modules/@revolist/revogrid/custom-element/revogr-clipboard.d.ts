import type { Components, JSX } from "../dist/types/components";

interface RevogrClipboard extends Components.RevogrClipboard, HTMLElement {}
export const RevogrClipboard: {
  prototype: RevogrClipboard;
  new (): RevogrClipboard;
};
/**
 * Used to define this component and all nested components recursively.
 */
export const defineCustomElement: () => void;
