import sys
import smaract.ctl as ctl
import numpy as np
import time



class ChannelError(Exception):
    """Custom exception for channel errors."""
    pass

# set all of the properties we want for motor movement such as 
def set_scan_properties(d_handle, move_velocity =  int(2e9), hold_time = 0, num_channels = 2):
    # d_handle of motor for interacting in the Smaract API
    # move_velocity of a motor axis
    # hold_time to wait after moving to a position
    # num_channels number of channels, or axes, for the motor with d_handle 
    for channel in range(num_channels):
        ctl.SetProperty_i32(d_handle, channel, ctl.Property.MOVE_MODE, ctl.MoveMode.CL_ABSOLUTE)
        ctl.SetProperty_i64(d_handle, channel, ctl.Property.MOVE_VELOCITY, move_velocity)

# reference the motor to ensure it doesn't drift
def reference_motor(d_handle, move_velocity =  int(2e9),num_channels=2):
    # d_handle of motor for interacting in the Smaract API
    # move_velocity of a motor axis
    # num_channels number of channels, or axes, for the motor with d_handle
    for channel in range(num_channels):
        try:
            print("referencing channel {}...".format(channel))
            ctl.SetProperty_i32(d_handle, channel, ctl.Property.REFERENCING_OPTIONS, 0)
            ctl.SetProperty_i64(d_handle, channel, ctl.Property.MOVE_VELOCITY, move_velocity)
            ctl.Reference(d_handle, channel)
            state = ctl.GetProperty_i32(
            d_handle, channel, ctl.Property.CHANNEL_STATE)
            if (state & ctl.ChannelState.IS_REFERENCED) > 0:
                print("referencing channel {} completed".format(channel))
        except ctl.Error as e:
            # Passing an error code to "GetResultInfo" returns a human readable string
            # specifying the error
            print("MCS2 {}: {}, error: {} (0x{:04X}) in line: {}.".format(e.func, ctl.GetResultInfo(e.code), ctl.ErrorCode(e.code).name, e.code, (sys.exc_info()[-1].tb_lineno)))


# wait for movement to settle before attempting to move the motor again
def wait_for_movement_settled(d_handle, channel):
    # d_handle of motor for interacting in the Smaract API
    # channel of axis we're waiting for
    try:
        while (True):
            state = ctl.GetProperty_i32(d_handle, channel, ctl.Property.CHANNEL_STATE)
            mask = ctl.ChannelState.ACTIVELY_MOVING
            if (state & mask) == 0:
                return
            if (state & ctl.ChannelState.MOVEMENT_FAILED) != 0:
                # The channel error property may then be read to determine the reason of the error.
                error = ctl.GetProperty_i32(d_handle, channel, ctl.Property.CHANNEL_ERROR)
                print("MCS2 movement failed: {} (error: 0x{:04X}), abort.".format(ctl.GetResultInfo(error), error))
    except ctl.Error as e:
        # Passing an error code to "GetResultInfo" returns a human readable string
        # specifying the error.
        print("MCS2 {}: {}, error: {} (0x{:04X}) in line: {}.".format(e.func, ctl.GetResultInfo(e.code), ctl.ErrorCode(e.code).name, e.code, (sys.exc_info()[-1].tb_lineno)))



