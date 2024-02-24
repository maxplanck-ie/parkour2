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

    if (
      nat &&
      !nat.get("single_cell") &&
      nat.get("type") === "RNA" &&
      value === null
    ) {
      isValid = false;
    }

    return isValid || "Must be present";
  },
});

Ext.define("validator.SingleCellField", {
  extend: "Ext.data.validator.Validator",
  alias: "data.validator.singlecellfield",
  validate: function (value, record) {
    var isValid = true;

    var nat = Ext.getStore("nucleicAcidTypesStore").findRecord(
      "id",
      record.get("nucleic_acid_type")
    );

    if (nat && nat.get("single_cell") && value === null) {
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
      defaultValue: null,
    },
    {
      type: "int",
      name: "cell_density",
      allowNull: true,
      defaultValue: null,
    },
    {
      type: "int",
      name: "cell_viability",
      allowNull: true,
      defaultValue: null,
    },
    {
      type: "int",
      name: "starting_number_cells",
      allowNull: true,
      defaultValue: null,
    },
    {
      type: "int",
      name: "number_targeted_cells",
      allowNull: true,
      defaultValue: null,
    },
  ],

  validators: {
    nucleic_acid_type: "presence",
    rna_quality: "rnaquality",
    cell_density: "singlecellfield",
    cell_viability: "singlecellfield",
    starting_number_cells: "singlecellfield",
    concentration: "singlecellfield",
  },
});
