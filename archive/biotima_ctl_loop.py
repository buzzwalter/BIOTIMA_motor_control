import sys
import smaract.ctl as ctl#
import numpy as np
#
move_velocity = 10000000000 # 10 mm/s to match rep rate of the laser and size of the beam
hold_time = 0 # ms
initial_pos_0  = -10000000000 # -1 cm we should knowdis
initial_pos_1  = 0 #we should knowdis
sequences = 15 # gives a total vertical movement of 1.5 cm if we move 1 mm every time...should be 15 sequences

try:
    buffer = ctl.FindDevices("")
    if len(buffer) == 0:       
        sys.exit(1)
    locators = buffer.split("\n")
    for locator in locators:
        print("MCS2 available devices: {}".format(locator))
       
            
except:
    print("MCS2 failed to find devices. Exit.")
    input()
    sys.exit(1)

try:
    # Open the first MCS2 device from the list
    d_handle = ctl.Open(locators[0])
    print("MCS2 opened {}.".format(locators[0]))
    
    channel = 0
    # Set move mode to relative movement.
    ctl.SetProperty_i32(d_handle, channel, ctl.Property.MOVE_MODE, ctl.MoveMode.CL_ABSOLUTE)
    # Set move velocity to move_velocity.
    ctl.SetProperty_i64(d_handle, channel, ctl.Property.MOVE_VELOCITY, move_velocity)
    # Set move acceleration to move_acceleration.
    ctl.SetProperty_i64(d_handle, channel, ctl.Property.MOVE_ACCELERATION, move_acceleration)
    # Enable the amplifier.
    ctl.SetProperty_i32(d_handle, channel, ctl.Property.AMPLIFIER_ENABLED, ctl.TRUE)
    # The hold time specifies how long the position is actively held after reaching the target.
    ctl.Move(d_handle,channel,initial_pos_0) # ensure initial position is set for vertical axis
    channel = 1
    ctl.SetProperty_i32(d_handle, channel, ctl.Property.MOVE_MODE, ctl.MoveMode.CL_ABSOLUTE)
    # Set move velocity to move_velocity.
    ctl.SetProperty_i64(d_handle, channel, ctl.Property.MOVE_VELOCITY, move_velocity)
    # Set move acceleration to move_acceleration.
    ctl.SetProperty_i64(d_handle, channel, ctl.Property.MOVE_ACCELERATION, move_acceleration)
    # Enable the amplifier.
    ctl.SetProperty_i32(d_handle, channel, ctl.Property.AMPLIFIER_ENABLED, ctl.TRUE)
    # The hold time specifies how long the position is actively held after reaching the target.
    ctl.Move(d_handle,channel,initial_pos_1) # ensure initial position is set for horizontal axis
    # compensation of drift effects, etc. set to value of hold_time
    position_1 = initial_pos_1 
    for s in range(sequences):
    # each seq approximately does
    # ---------------------------- 
    #                             | 
    # ----------------------------
    #|
    # so if we do them in succesion it should from an s pattern
        ctl.Move(d_handle,0,initial_pos_0 + 20000000000) # move positive direction horizontal 2cm
        position_1 = position_1 + 500000000
        ctl.Move(d_handle,1,position_1) # move negative direction vertical .5 mm
        ctl.Move(d_handle,0,initial_pos_0)
        position_1 = position_1 + 500000000
        ctl.Move(d_handle,1,position_1) # move negative direction vertical .5 mm
    

except ctl.Error as e:
    # Passing an error code to "GetResultInfo" returns a human readable string
    # specifying the error.
    print("MCS2 {}: {}, error: {} (0x{:04X}) in line: {}."
          .format(e.func, ctl.GetResultInfo(e.code), ctl.ErrorCode(e.code).name, e.code, (sys.exc_info()[-1].tb_lineno)))

except Exception as ex:
    print("Unexpected error: {}, {} in line: {}".format(ex, type(ex), (sys.exc_info()[-1].tb_lineno)))
    raise

finally:
    # Before closing the program the connection to the device must be closed by calling "Close". Also we want to set channel 1 back to its original value
    if d_handle != None:
        #ctl.Move(d_handle,1,position_1)
        print("channel 0/1 final position: ", ctl.GetProperty_i64(d_handle,0,ctl.Property.POSITION),ctl.GetProperty_i64(d_handle,0,ctl.Property.POSITION))
        ctl.Close(d_handle)
    print("MCS2 close.")
    print("*******************************************************")
    print("Done. Press return to exit.")
    input()
