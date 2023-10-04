import type { Components, JSX } from "../dist/types/components";

interface RevogrFocus extends Components.RevogrFocus, HTMLElement {}
export const RevogrFocus: {
  prototype: RevogrFocus;
  new (): RevogrFocus;
};
/**
 * Used to define this component and all nested components recursively.
 */
export const defineCustomElement: () => void;
