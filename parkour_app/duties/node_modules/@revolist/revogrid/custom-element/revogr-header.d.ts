import type { Components, JSX } from "../dist/types/components";

interface RevogrHeader extends Components.RevogrHeader, HTMLElement {}
export const RevogrHeader: {
  prototype: RevogrHeader;
  new (): RevogrHeader;
};
/**
 * Used to define this component and all nested components recursively.
 */
export const defineCustomElement: () => void;
