import type { Components, JSX } from "../dist/types/components";

interface RevogrTempRange extends Components.RevogrTempRange, HTMLElement {}
export const RevogrTempRange: {
  prototype: RevogrTempRange;
  new (): RevogrTempRange;
};
/**
 * Used to define this component and all nested components recursively.
 */
export const defineCustomElement: () => void;
