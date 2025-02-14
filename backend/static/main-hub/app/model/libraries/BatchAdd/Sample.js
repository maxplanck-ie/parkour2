Ext.define("validator.RNAQuality", {
  extend: "Ext.data.validator.Validator",
  alias: "data.validator.rnaquality",
  validate: function (value, record) {
    var store = Ext.getStore("rnaQualityStore"),
      isValid = true;

    var nat = Ext.getStore("nucleicAcidTypesStore").findRecord(
      "id",
      record.get("nucleic_acid_type")
    );

    if (nat && nat.get("type") === "RNA" && value === null) {
      isValid = false;
    }

    return isValid || "Must be present";
  }
});

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
      type: "float",
      name: "rna_quality",
      allowNull: true,
      defaultValue: null
    },
    {
      name: "biosafety_level",
      type: "string"
    },
    {
      name: "gmo",
      type: "bool"
    }
  ],

  validators: {
    nucleic_acid_type: "presence",
    // rna_quality: "rnaquality"
  }
});
