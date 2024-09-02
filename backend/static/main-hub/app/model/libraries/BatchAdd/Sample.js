Ext.define("MainHub.model.libraries.BatchAdd.Sample", {
  extend: "MainHub.model.libraries.BatchAdd.Common",

  fields: [
    {
      type: "int",
      name: "nucleic_acid_type",
      allowNull: true,
      defaultValue: null
    },
    {
      name: "biosafety_level",
      type: "string",
    },
    {
      name: "gmo",
      type: "bool",
    },
  ],

  validators: {
    nucleic_acid_type: "presence",
    biosafety_level: "presence",
    gmo: "presence"
  }
});
