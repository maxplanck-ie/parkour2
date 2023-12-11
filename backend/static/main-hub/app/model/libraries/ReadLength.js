Ext.define("MainHub.model.libraries.ReadLength", {
  extend: "MainHub.model.Base",

  fields: [
    { name: "name", type: "string" },
    { name: "id", type: "int" },
    { name: "archived", type: "bool" },
  ],
});
