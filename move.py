import sys
import smaract.ctl as ctl
import numpy as np

should_continue = True  # Global flag to control the loop

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

# stop button for gui based interruption 
def stop_scanning(event):
    # event to handle button press from the GUI
    global should_continue
    should_continue = False
    print("Stopping scanning...")

# generate snake movement for motor in the selected area
def snake_scan(d_handle, boundaries_container, step_size=int(5e7),num_channels=2,restart_scan=True):
    # d_handle of motor for interacting in the Smaract API
    # boundaries_container with as many entries as channels, starting with channel 0 and containing the min max pairs (min_pos_i,max_pos_i)
    # step_size to move motor, set to 50 micron
    # num_channels set to 2 since the snake movement only makes sense for 2 channels
    # restart_scan to toggle the movement on or off
    try:
        if num_channels != 2: # would like to use get properties to retrieve number of channels property
            raise ChannelError("Number of channels must be 2.")
        channel_b = 0
        channel_a = 1
        b_boundaries, a_boundaries = boundaries_container
        N_points_b = int(np.ceil((b_boundaries[1] - b_boundaries[0])*1e9 / step_size)) 
        while restart_scan:
            for i in range(N_points_b // 2): # two movements in the b axis per loop so we int divide by 2
                print('loop number {} out of {}'.format(i,N_points_b//2) )
                for boundary in a_boundaries:
                    ctl.Move(d_handle,channel_a,int(boundary*1e9)) # convert mouse click to pm
                    wait_for_movement_settled(d_handle, channel_a)
                    ctl.Move(d_handle,channel_b,step_size*i)
                    wait_for_movement_settled(d_handle, channel_b)
            if N_points_b%2:
                ctl.Move(d_handle,channel_b,step_size*((N_points_b // 2)+1)) # ensure movement catches the odd parity mismatch from the for-loop

        ctl.Close()
    except ctl.Error as e:
        # Passing an error code to "GetResultInfo" returns a human readable string
        # specifying the error.
        print("MCS2 {}: {}, error: {} (0x{:04X}) in line: {}.".format(e.func, ctl.GetResultInfo(e.code), ctl.ErrorCode(e.code).name, e.code, (sys.exc_info()[-1].tb_lineno)))
    except ChannelError as ce:
        print(f"Channel Error: {ce}")
    finally:
        # Before closing the program the connection to the device must be closed by calling "Close". Also we want to set channel 1 back to its original value
        if d_handle != None:
            print("channel 0/1 final position: ", ctl.GetProperty_i64(d_handle,0,ctl.Property.POSITION),ctl.GetProperty_i64(d_handle,0,ctl.Property.POSITION))
            ctl.Close(d_handle)
            print("MCS2 close.")
            print("*******************************************************")
            print("Done. Press return to exit.")
            input()

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

 