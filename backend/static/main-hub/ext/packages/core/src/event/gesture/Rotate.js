/**
 * A simple event recognizer which knows when you rotate.
 */
Ext.define(
  "Ext.event.gesture.Rotate",
  {
    extend: "Ext.event.gesture.MultiTouch",

    priority: 800,

    handledEvents: ["rotatestart", "rotate", "rotateend", "rotatecancel"],

    /**
     * @member Ext.dom.Element
     * @event rotatestart
     * Fired once when a rotation has started.
     * @param {Ext.event.Event} event The {@link Ext.event.Event} event encapsulating the DOM event.
     * @param {HTMLElement} node The target of the event.
     * @param {Object} options The options object passed to Ext.mixin.Observable.addListener.
     */

    /**
     * @member Ext.dom.Element
     * @event rotate
     * Fires continuously when there is rotation (the touch must move for this to be fired).
     * When listening to this, ensure you know about the {@link Ext.event.Event#angle} and {@link Ext.event.Event#rotation}
     * properties in the `event` object.
     * @param {Ext.event.Event} event The {@link Ext.event.Event} event encapsulating the DOM event.
     * @param {HTMLElement} node The target of the event.
     * @param {Object} options The options object passed to Ext.mixin.Observable.addListener.
     */

    /**
     * @member Ext.dom.Element
     * @event rotateend
     * Fires when a rotation event has ended.
     * @param {Ext.event.Event} event The {@link Ext.event.Event} event encapsulating the DOM event.
     * @param {HTMLElement} node The target of the event.
     * @param {Object} options The options object passed to Ext.mixin.Observable.addListener.
     */

    /**
     * @property {Number} angle
     * The angle of the rotation.
     *
     * **This is only available when the event type is `rotate`**
     * @member Ext.event.Event
     */

    /**
     * @property {Number} rotation
     * A amount of rotation, since the start of the event.
     *
     * **This is only available when the event type is `rotate`**
     * @member Ext.event.Event
     */

    startAngle: 0,

    lastTouches: null,

    lastAngle: null,

    onTouchMove: function (e) {
      var me = this,
        touches,
        lastAngle,
        firstPoint,
        secondPoint,
        angle,
        nextAngle,
        previousAngle,
        diff;

      if (me.isTracking) {
        touches = e.touches;
        lastAngle = me.lastAngle;

        firstPoint = touches[0].point;
        secondPoint = touches[1].point;

        angle = firstPoint.getAngleTo(secondPoint);

        if (lastAngle !== null) {
          diff = Math.abs(lastAngle - angle);
          nextAngle = angle + 360;
          previousAngle = angle - 360;

          if (Math.abs(nextAngle - lastAngle) < diff) {
            angle = nextAngle;
          } else if (Math.abs(previousAngle - lastAngle) < diff) {
            angle = previousAngle;
          }
        }

        me.lastAngle = angle;

        if (!me.isStarted) {
          me.isStarted = true;

          me.startAngle = angle;

          me.fire("rotatestart", e, {
            touches: touches,
            angle: angle,
            rotation: 0
          });
        } else {
          me.fire("rotate", e, {
            touches: touches,
            angle: angle,
            rotation: angle - me.startAngle
          });
        }

        me.lastTouches = Ext.Array.clone(touches);
      }
    },

    onTouchEnd: function (e) {
      if (this.isStarted) {
        this.fire("rotateend", e);
      }

      return this.callParent([e]);
    },

    onCancel: function (e) {
      this.fire("rotatecancel", e, null, true);
    },

    reset: function () {
      var me = this;

      me.lastTouches = me.lastAngle = me.startAngle = null;

      return this.callParent();
    }
  },
  function (Rotate) {
    var gestures = Ext.manifest.gestures;
    Rotate.instance = new Rotate(gestures && gestures.rotate);
  }
);
