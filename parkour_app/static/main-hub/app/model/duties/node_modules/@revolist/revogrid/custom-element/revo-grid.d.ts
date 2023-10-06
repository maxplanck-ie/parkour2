import type { Components, JSX } from "../dist/types/components";

interface RevoGrid extends Components.RevoGrid, HTMLElement {}
export const RevoGrid: {
  prototype: RevoGrid;
  new (): RevoGrid;
};
/**
 * Used to define this component and all nested components recursively.
 */
export const defineCustomElement: () => void;
