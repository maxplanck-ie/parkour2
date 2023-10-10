import type { Components, JSX } from "../dist/types/components";

interface RevogrOrderEditor extends Components.RevogrOrderEditor, HTMLElement {}
export const RevogrOrderEditor: {
  prototype: RevogrOrderEditor;
  new (): RevogrOrderEditor;
};
/**
 * Used to define this component and all nested components recursively.
 */
export const defineCustomElement: () => void;
