describe("Ext.data.validator.Exclusion", function () {
  var v;

  function validate(value, list) {
    v = new Ext.data.validator.Exclusion({
      list: list
    });
    return v.validate(value);
  }

  afterEach(function () {
    v = null;
  });

  it("should throw an error when configured without a list", function () {
    expect(function () {
      v = new Ext.data.validator.Exclusion();
    }).toThrow();
  });

  describe("invalid values", function () {
    it("should not validate if the value is in the list", function () {
      expect(validate(3, [1, 2, 3, 4])).toBe(v.getMessage());
    });
  });

  describe("valid values", function () {
    it("should validate if the value is not in the list", function () {
      expect(validate(5, [1, 2, 3, 4])).toBe(true);
    });

    it("should use strict type checking", function () {
      expect(validate("3", [1, 2, 3, 4])).toBe(true);
    });
  });

  describe("messages", function () {
    it("should accept a custom message", function () {
      v = new Ext.data.validator.Exclusion({
        message: "Foo",
        list: [1]
      });
      expect(v.validate(1)).toBe("Foo");
    });
  });

  describe("runtime changes", function () {
    it("should be able to have a new list applied", function () {
      v = new Ext.data.validator.Exclusion({
        list: [1, 2, 3]
      });
      expect(v.validate(5)).toBe(true);
      v.setList([3, 4, 5]);
      expect(v.validate(5)).toBe(v.getMessage());
    });
  });
});
