import type { Components, JSX } from "../dist/types/components";

interface RevogrFilterPanel extends Components.RevogrFilterPanel, HTMLElement {}
export const RevogrFilterPanel: {
  prototype: RevogrFilterPanel;
  new (): RevogrFilterPanel;
};
/**
 * Used to define this component and all nested components recursively.
 */
export const defineCustomElement: () => void;
