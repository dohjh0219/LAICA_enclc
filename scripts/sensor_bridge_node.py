#!/usr/bin/env python3
"""
ROS node: sensor_bridge_node

Reads the $SENSORS stream from the Arduino Mega (USB serial) and publishes:
  /load_cell/data   enc_lc/LoadCellData
  /encoder/data     enc_lc/EncoderData

Parameters
----------
  ~port           : Arduino USB serial port  (default '/dev/ttyUSB0')
  ~baud           : Baud rate                (default 115200)
  ~publish_rate   : ROS publish rate [Hz]    (default 100.0)
  ~frame_id_lc    : TF frame for load cell   (default 'load_cell')
  ~frame_id_enc   : TF frame for encoder     (default 'encoder')

Force calibration (applied to voltage_mv → force_n):
  ~zero_offset_mv : ADC output at zero load [mV]  (default 0.0)
  ~scale_n_per_mv : [N / mV] calibration factor   (default 1.0)

  force_n = (voltage_mv - zero_offset_mv) * scale_n_per_mv

  To calibrate: measure lc_mv at zero load (→ zero_offset_mv), then hang a
  known weight and solve for scale_n_per_mv = known_N / (lc_mv - zero_offset_mv).
"""

import rospy
from enc_lc.arduino_bridge import ArduinoBridge
from enc_lc.msg import LoadCellData, EncoderData
from std_msgs.msg import Header


def make_header(frame_id: str) -> Header:
    h = Header()
    h.stamp = rospy.Time.now()
    h.frame_id = frame_id
    return h


def main():
    rospy.init_node('sensor_bridge_node')

    port          = rospy.get_param('~port',          '/dev/ttyUSB0')
    baud          = rospy.get_param('~baud',          115200)
    publish_rate  = rospy.get_param('~publish_rate',  100.0)
    frame_id_lc   = rospy.get_param('~frame_id_lc',  'load_cell')
    frame_id_enc  = rospy.get_param('~frame_id_enc', 'encoder')
    zero_offset   = rospy.get_param('~zero_offset_mv', 0.0)
    scale         = rospy.get_param('~scale_n_per_mv', 1.0)

    rospy.loginfo(f'Connecting to Arduino on {port} at {baud} baud')
    try:
        bridge = ArduinoBridge(port=port, baud=baud)
        bridge.start()
    except Exception as e:
        rospy.logfatal(f'Arduino bridge init failed: {e}')
        return

    pub_lc  = rospy.Publisher('/load_cell/data', LoadCellData, queue_size=10)
    pub_enc = rospy.Publisher('/encoder/data',   EncoderData,  queue_size=10)
    rate    = rospy.Rate(publish_rate)

    rospy.loginfo('sensor_bridge_node running')

    while not rospy.is_shutdown():
        frame = bridge.get_frame()

        # ── Load cell ────────────────────────────────────────────────── #
        lc_msg = LoadCellData()
        lc_msg.header    = make_header(frame_id_lc)
        lc_msg.raw_count = frame.lc_raw
        lc_msg.voltage_mv = frame.lc_mv
        lc_msg.force_n   = (frame.lc_mv - zero_offset) * scale
        pub_lc.publish(lc_msg)

        # ── Encoder ──────────────────────────────────────────────────── #
        enc_msg = EncoderData()
        enc_msg.header    = make_header(frame_id_enc)
        enc_msg.angle_deg = frame.enc_deg
        enc_msg.rev       = frame.enc_rev
        enc_msg.rpm       = frame.enc_rpm
        pub_enc.publish(enc_msg)

        if bridge.parse_errors:
            rospy.logwarn_throttle(10.0,
                f'Arduino parse errors: {bridge.parse_errors}')

        rate.sleep()

    bridge.stop()


if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass
