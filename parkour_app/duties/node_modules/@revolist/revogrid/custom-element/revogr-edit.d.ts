import type { Components, JSX } from "../dist/types/components";

interface RevogrEdit extends Components.RevogrEdit, HTMLElement {}
export const RevogrEdit: {
  prototype: RevogrEdit;
  new (): RevogrEdit;
};
/**
 * Used to define this component and all nested components recursively.
 */
export const defineCustomElement: () => void;
