/**
 * A singleton instance of an `{@link Ext.data.Connection}`. This class is used to
 * communicate with your server side code. It can be used as follows:
 *
 *      Ext.Ajax.request({
 *          url: 'ajax_demo/sample.json',
 *
 *          success: function(response, opts) {
 *              var obj = Ext.decode(response.responseText);
 *              console.dir(obj);
 *          },
 *
 *          failure: function(response, opts) {
 *              console.log('server-side failure with status code ' + response.status);
 *          }
 *      });
 *
 * Default options for all requests can be set by changing a property on the Ext.Ajax class:
 *
 *      Ext.Ajax.setTimeout(60000); // 60 seconds
 *
 * Any options specified in the request method for the Ajax request will override any
 * defaults set on the `Ext.Ajax` singleton. In the code sample below, the timeout for the
 * request will be 60 seconds.
 *
 *      Ext.Ajax.setTimeout(120000); // 120 seconds
 *
 *      Ext.Ajax.request({
 *          url: 'page.aspx',
 *          timeout: 60000
 *      });
 *
 * In general, this class will be used for all Ajax requests in your application. The main
 * reason for creating a separate `{@link Ext.data.Connection}` is for a series of
 * requests that share common settings that are different to all other requests in the
 * application.
 */
Ext.define("Ext.Ajax", {
  extend: "Ext.data.Connection",
  singleton: true,

  /**
   * @cfg {Object} extraParams
   * @hide
   */

  /**
   * @cfg {Object} defaultHeaders
   * @hide
   */

  /**
   * @cfg {String} method
   * @hide
   */

  /**
   * @cfg {Number} timeout
   * @hide
   */

  /**
   * @cfg {Boolean} autoAbort
   * @hide
   */

  /**
   * @cfg {Boolean} disableCaching
   * @hide
   */

  /**
   * @property {Boolean} disableCaching
   * True to add a unique cache-buster param to GET requests. Defaults to true.
   */

  /**
   * @property {String} url
   * The default URL to be used for requests to the server.
   * If the server receives all requests through one URL, setting this once is easier than
   * entering it on every request.
   */

  /**
   * @property {Object} extraParams
   * An object containing properties which are used as extra parameters to each request made
   * by this object. Session information and other data that you need
   * to pass with each request are commonly put here.
   */

  /**
   * @property {Object} defaultHeaders
   * An object containing request headers which are added to each request made by this object.
   */

  /**
   * @property {String} method
   * The default HTTP method to be used for requests. Note that this is case-sensitive and
   * should be all caps (if not set but params are present will use `POST`, otherwise will
   * use `GET`.)
   */

  /**
   * @property {Number} timeout
   * The timeout in milliseconds to be used for requests. Defaults to 30000.
   *
   * When a request fails due to timeout the XMLHttpRequest response object will
   * contain:
   *
   *     timedout: true
   */

  /**
   * @property {Boolean} autoAbort
   * Whether a new request should abort any pending requests.
   */
  autoAbort: false
});
