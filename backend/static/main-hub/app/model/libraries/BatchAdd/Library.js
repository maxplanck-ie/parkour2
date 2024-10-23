Ext.define("validator.IndexI7", {
  extend: "Ext.data.validator.Validator",
  alias: "data.validator.indexI7",
  validate: function (value, record) {
    return (
      record.get("index_reads") === null ||
      record.get("index_reads") === 0 ||
      (record.get("index_reads") > 0 && value !== "") ||
      "Must be present"
    );
  }
});

Ext.define("validator.IndexI5", {
  extend: "Ext.data.validator.Validator",
  alias: "data.validator.indexI5",
  validate: function (value, record) {
    return (
      record.get("index_reads") === null ||
      record.get("index_reads") <= 1 ||
      (record.get("index_reads") > 1 && value !== "") ||
      "Must be present"
    );
  }
});

Ext.define("MainHub.model.libraries.BatchAdd.Library", {
  extend: "MainHub.model.libraries.BatchAdd.Common",

  fields: [
    {
      type: "int",
      name: "mean_fragment_size",
      defaultValue: null
    },
    {
      type: "int",
      name: "index_type",
      allowNull: true,
      defaultValue: null
    },
    {
      type: "int",
      name: "index_reads",
      allowNull: true,
      defaultValue: null
    },
    {
      type: "string",
      name: "index_i7"
    },
    {
      type: "string",
      name: "index_i5"
    }
  ],

  validators: {
    mean_fragment_size: "greaterthanzero",
    index_type: "presence",
    index_reads: "presence",
    index_i7: "indexI7",
    index_i5: "indexI5"
  }
});
