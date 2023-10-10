import type { Components, JSX } from "../dist/types/components";

interface RevogrOverlaySelection extends Components.RevogrOverlaySelection, HTMLElement {}
export const RevogrOverlaySelection: {
  prototype: RevogrOverlaySelection;
  new (): RevogrOverlaySelection;
};
/**
 * Used to define this component and all nested components recursively.
 */
export const defineCustomElement: () => void;
