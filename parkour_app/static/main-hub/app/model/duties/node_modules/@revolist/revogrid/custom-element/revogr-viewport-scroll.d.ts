import type { Components, JSX } from "../dist/types/components";

interface RevogrViewportScroll extends Components.RevogrViewportScroll, HTMLElement {}
export const RevogrViewportScroll: {
  prototype: RevogrViewportScroll;
  new (): RevogrViewportScroll;
};
/**
 * Used to define this component and all nested components recursively.
 */
export const defineCustomElement: () => void;
