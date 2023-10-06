import type { Components, JSX } from "../dist/types/components";

interface RevogrRowHeaders extends Components.RevogrRowHeaders, HTMLElement {}
export const RevogrRowHeaders: {
  prototype: RevogrRowHeaders;
  new (): RevogrRowHeaders;
};
/**
 * Used to define this component and all nested components recursively.
 */
export const defineCustomElement: () => void;
