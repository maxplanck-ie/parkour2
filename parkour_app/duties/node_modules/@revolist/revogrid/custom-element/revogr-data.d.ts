import type { Components, JSX } from "../dist/types/components";

interface RevogrData extends Components.RevogrData, HTMLElement {}
export const RevogrData: {
  prototype: RevogrData;
  new (): RevogrData;
};
/**
 * Used to define this component and all nested components recursively.
 */
export const defineCustomElement: () => void;
