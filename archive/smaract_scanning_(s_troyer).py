import smaract.ctl as ctl
import numpy as np
import time

# connection string of the device to connect to
from matplotlib.widgets import RectangleSelector
import numpy as np
import matplotlib.pyplot as plt
a_max = []
b_max = []
a_min = []
b_min = []
x_zero = 0 # 0 and 24 worked
y_zero = 24

def line_select_callback(eclick, erelease, a_max=a_max, b_max=b_max, a_min=a_min, b_min=b_min):
    'eclick and erelease are the press and release events'
    x1, y1 = eclick.xdata, eclick.ydata
    x2, y2 = erelease.xdata, erelease.ydata
    print("(%3.2f, %3.2f) --> (%3.2f, %3.2f)" % (x1, y1, x2, y2))
    print(" The button you used were: %s %s" % (eclick.button, erelease.button))
    # pass min and max values for scanned area from selection area
    a_max.append(x2) 
    b_max.append(y2)
    a_min.append(x1)
    b_min.append(y1)


def toggle_selector(event):
    print(' Key pressed.')
    if event.key in ['Q', 'q'] and toggle_selector.RS.active:
        print(' RectangleSelector deactivated.')
        toggle_selector.RS.set_active(False)
    if event.key in ['A', 'a'] and not toggle_selector.RS.active:
        print(' RectangleSelector activated.')
        toggle_selector.RS.set_active(True)


fig, current_ax = plt.subplots()                 # make a new plotting range
N = 1000                                       # If N is large one can see
x = -np.linspace(0.0, 24, N)+x_zero               # improvement by use blitting!
y = -x-y_zero+x_zero

plt.scatter(x, (12-y_zero)*np.ones(len(x)),c='b', marker='.', alpha=.02)  # plot something
plt.scatter((-12+x_zero)*np.ones(len(x)), y,c='b', marker='.', alpha=.02)  # plot something
plt.axis([max(x), min(x), min(y), max(y)])
print("\n      click  -->  release")

# drawtype is 'box' or 'line' or 'none'
toggle_selector.RS = RectangleSelector(current_ax, line_select_callback,
                                       drawtype='box', useblit=True,
                                       button=[1, 3],  # don't use middle button
                                       minspanx=5, minspany=5,
                                       spancoords='pixels',
                                       interactive=True)
plt.connect('key_press_event', toggle_selector)
plt.show(block=True)

device = "network:sn:MCS2-00005284"
reference_motor = True

scan_axis_a = 1  # primary scan axis channel
scan_axis_b = 0  # secondary scan axis channel

min_pos_a = a_min[-1]  # mm; minimum position of primary scan axis
max_pos_a = a_max[-1]  # mm; maximum position of primary scan axis
min_pos_b = b_min[-1]  # mm; minimum position of secondary scan axis
max_pos_b = b_max[-1]  # mm; maximum position of secondary scan axis

print("a min: " + str(min_pos_a) + " a max: " + str(max_pos_a))
print("b min: " + str(min_pos_b) + " b max: " + str(max_pos_b))

stepsize = 50  # µm; distance between two scan points
scan_velocity = 2000  # µm/s; velocity of the scan
wait_time = 0  # ms; time to wait after each scan point; if 0, motor moves from one end of the line to the other continuously

restart_scan = True  # if True, the scan will be restarted after it has finished
# if True, the scan will be done in a spiral pattern around the center of the scan area
spiral_mode = False


# print all available devices/connection strings
if device == "":
    buffer = ctl.FindDevices()
    if len(buffer) == 0:
        print("No devices found")
        exit(1)
    locators = buffer.split("\n")
    print("available devices:")
    for locator in locators:
        print(locator)
    exit(1)

d_handle = ctl.Open(device)

def ensure_channel_is_referenced(channel):
    state = ctl.GetProperty_i32(d_handle, channel, ctl.Property.CHANNEL_STATE)
    if (state & ctl.ChannelState.IS_REFERENCED) > 0:
        return
    print("referencing channel {}...".format(channel))
    ctl.SetProperty_i32(d_handle, channel, ctl.Property.REFERENCING_OPTIONS, 0)
    ctl.SetProperty_i64(d_handle, channel,
                        ctl.Property.MOVE_VELOCITY, 2000000000)
    ctl.Reference(d_handle, channel)
    while True:
        state = ctl.GetProperty_i32(
            d_handle, channel, ctl.Property.CHANNEL_STATE)
        if (state & ctl.ChannelState.IS_REFERENCED) > 0:
            print("referencing channel {} completed".format(channel))
            return
        if (state & ctl.ChannelState.REFERENCING) == 0:
            error = ctl.GetProperty_i32(
                d_handle, channel, ctl.Property.CHANNEL_ERROR)
            print(
                "MCS2 reference failed: {} (error: 0x{:04X}), abort.".format(
                    ctl.GetResultInfo(error), error
                )
            )
            ctl.Close(d_handle)
            exit(1)

if reference_motor:
    ensure_channel_is_referenced(scan_axis_a)
    ensure_channel_is_referenced(scan_axis_b)
    

# let's first convert all values to pm
min_pos_a *= 1e9
max_pos_a *= 1e9
min_pos_b *= 1e9
max_pos_b *= 1e9
stepsize *= 1e6
scan_velocity *= 1e6
#print((max_pos_a - min_pos_a)/stepsize)
#print(np.ceil((max_pos_b - min_pos_b)/stepsize))
N_points_a = int(np.ceil((max_pos_a - min_pos_a) / stepsize)) + 1
N_points_b = int(np.ceil((max_pos_b - min_pos_b) / stepsize)) + 1
a_positions = (
    np.array([min_pos_a, max_pos_a])
    if wait_time == 0
    else min_pos_a + np.arange(N_points_a) * stepsize
)
b_positions = min_pos_b + np.arange(N_points_b) * stepsize

# let's start
ctl.SetProperty_i32(
    d_handle, scan_axis_a, ctl.Property.MOVE_MODE, ctl.MoveMode.CL_ABSOLUTE
)
ctl.SetProperty_i32(
    d_handle, scan_axis_b, ctl.Property.MOVE_MODE, ctl.MoveMode.CL_ABSOLUTE
)
ctl.SetProperty_i32(d_handle, scan_axis_a, ctl.Property.HOLD_TIME, wait_time)
ctl.SetProperty_i32(d_handle, scan_axis_b, ctl.Property.HOLD_TIME, wait_time)
ctl.SetProperty_i64(
    d_handle, scan_axis_a, ctl.Property.MOVE_VELOCITY, int(scan_velocity)
)
ctl.SetProperty_i64(
    d_handle, scan_axis_b, ctl.Property.MOVE_VELOCITY, int(scan_velocity)
)


def wait_for_movement_settled(channel):
    state = ctl.GetProperty_i32(d_handle, channel, ctl.Property.CHANNEL_STATE)
    if (state & ctl.ChannelState.MOVEMENT_FAILED) != 0:
        error = ctl.GetProperty_i32(
            d_handle, channel, ctl.Property.CHANNEL_ERROR)
        print(
            "MCS2 movement failed: {} (error: 0x{:04X}), abort.".format(
                ctl.GetResultInfo(error), error
            )
        )
        ctl.Close(d_handle)
        exit(1)
    if (state & ctl.ChannelState.ACTIVELY_MOVING) == 0:
        return
    while True:
        event = ctl.WaitForEvent(d_handle, ctl.INFINITE)
        if event.idx == channel and event.type == ctl.EventType.MOVEMENT_FINISHED:
            if event.i32 == ctl.ErrorCode.NONE:
                return
            print(
                "MCS2 movement failed: {} (error: 0x{:04X}), abort.".format(
                    ctl.GetResultInfo(event.i32), event.i32
                )
            )
            ctl.Close(d_handle)
            exit(1)


def generate_spiral_positions(x_min, x_max, y_min, y_max, step):
    x_center = (x_max + x_min) / 2
    y_center = (y_max + y_min) / 2
    radius = 0
    theta = 0

    while True:
        x = x_center + radius * np.cos(theta)
        y = y_center + radius * np.sin(theta)

        if not (x_min <= x <= x_max and y_min <= y <= y_max):
            break

        yield (x, y)

        angle_increment = step / radius if radius > 0 else 0
        radius += step * angle_increment / \
            (2 * np.pi) if angle_increment > 0 else step
        theta += angle_increment


while restart_scan:
    if spiral_mode:
        for a, b in generate_spiral_positions(
            min_pos_a, max_pos_a, min_pos_b, max_pos_b, stepsize
        ):
            ctl.Move(d_handle, scan_axis_a, int(a))
            ctl.Move(d_handle, scan_axis_b, int(b))
            wait_for_movement_settled(scan_axis_a)
            wait_for_movement_settled(scan_axis_b)
            if wait_time > 0:
                time.sleep(wait_time / 1000)
    else:
        direction = +1
        for i, b in zip(range(N_points_b), b_positions):
            ctl.Move(d_handle, scan_axis_b, int(b))
            wait_for_movement_settled(scan_axis_b)
            #print(ctl.GetProperty_i64(d_handle,scan_axis_a,ctl.Property.POSITION),ctl.GetProperty_i64(d_handle,scan_axis_b,ctl.Property.POSITION))
            for a in a_positions[::direction]:
                ctl.Move(d_handle, scan_axis_a, int(a))
                wait_for_movement_settled(scan_axis_a)
                if wait_time > 0:
                    time.sleep(wait_time / 1000)
            direction *= -1
            print("line", i + 1, "of", N_points_b,
                  "done    ", end="\r", flush=True)        


ctl.Close(d_handle)
