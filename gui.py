from matplotlib.widgets import RectangleSelector
from matplotlib.widgets import Button
from matplotlib.animation import FuncAnimation
import numpy as np
import sys
import matplotlib.pyplot as plt
from move import *
import smaract.ctl as ctl

a_max = []
b_max = []
a_min = []
b_min = []

is_running = False  # Global flag to control the loop

# callback for handling events when rectangular area is selected
def line_select_callback(eclick, erelease, a_max=a_max, b_max=b_max, a_min=a_min, b_min=b_min):
    # elclick event associated with a mouse cllick
    # erelease event associated with a mouse release
    # a_max, b_max, a_min, b_min containers for pass by reference...python makes us do this
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

# enables/disables rectangle selector tool based on input from keyboard (q to toggle off and a to toggle on)
def toggle_selector(event):
    # event associated with keyboard input
    print(' Key pressed.')
    if event.key in ['Q', 'q'] and toggle_selector.RS.active:
        print(' RectangleSelector deactivated.')
        toggle_selector.RS.set_active(False)
    if event.key in ['A', 'a'] and not toggle_selector.RS.active:
        print(' RectangleSelector activated.')
        toggle_selector.RS.set_active(True)

# stop button for gui based interruption 
def stop_scanning(event):
    # event to handle button press from the GUI
    global is_running
    is_running = not is_running
    print("Stopping scanning...")


# plots available space for the motor to move
def get_plot():#(N=1000, x_zero=14,y_zero=13):
    # N number of points to use
    # x_zero referenced zero for the laser alignment along axis a
    # y_zero referenced zero for the laser alignment along axis b

    fig, current_ax = plt.subplots(figsize=(15, 12))                 # make a new plotting range
    plt.subplots_adjust(bottom=0.2) # Adjust the bottom to make room for the button


    stop_button_ax = plt.axes([0.7, 0.05, 1, 0.09])  # [left, bottom, width, height]
    stop_button = Button(stop_button_ax, 'Toggle Scanning', color='y', hovercolor='salmon')
    stop_button.on_clicked(stop_scanning)

    # drawtype is 'box' or 'line' or 'none'
    toggle_selector.RS = RectangleSelector(current_ax, line_select_callback,drawtype='box', useblit=True,button=[1, 3], minspanx=5, minspany=5,spancoords='pixels',interactive=True)
    plt.connect('key_press_event', toggle_selector)

    xdata, ydata = [0], [np.sin(0)]
    return plt.plot([], [], 'teal')



# Update function for FuncAnimation
def update(frame):
    global is_running
    global d_handle
    global loop_index
    num_channels = 2
    step_size=int(5e7)

    if is_running :

        # For demonstration, we'll just simulate adding a new point to the line
        xdata, ydata = line.get_data()
        xdata = list(xdata)
        ydata = list(ydata)
        line.set_data(xdata, ydata)

        boundaries_container = [[b_min[0],b_max[0]],[a_min[0],a_max[0]]]
    
        try:
            if num_channels != 2: # would like to use get properties to retrieve number of channels property
                raise ChannelError("Number of channels must be 2.")
            channel_b = 0
            channel_a = 1
            b_boundaries, a_boundaries = boundaries_container
            N_points_b = int(np.ceil((b_boundaries[1] - b_boundaries[0])*1e9 / step_size)) 

            if loop_index <(N_points_b // 2): # two movements in the b axis per loop so we int divide by 2
                print('loop number {} out of {}'.format(loop_index,N_points_b//2) )
                for boundary in a_boundaries:
                    ctl.Move(d_handle,channel_a,int(boundary*1e9)) # convert mouse click to pm
                    xdata.append( boundary)
                    wait_for_movement_settled(d_handle, channel_a)
                    ctl.Move(d_handle,channel_b,int(b_boundaries[0]*1e9)+step_size*loop_index)
                    wait_for_movement_settled(d_handle, channel_b)
                    ydata.append(-(int(b_boundaries[0])+step_size*loop_index*1e-9))
                loop_index=loop_index+1
            if (N_points_b%2) and (loop_index==N_points_b // 2):
                ctl.Move(d_handle,channel_b,int(b_boundaries[0])+step_size*((N_points_b // 2)+1)) # ensure movement catches the odd parity mismatch from the for-loop
                xdata.append(boundary)
                ydata.append(-(int(b_boundaries[0]*1e9)+step_size*((N_points_b // 2)+1)*1e-9))
        except ctl.Error as e:
            # Passing an error code to "GetResultInfo" returns a human readable string
            # specifying the error.
            print("MCS2 {}: {}, error: {} (0x{:04X}) in line: {}.".format(e.func, ctl.GetResultInfo(e.code), ctl.ErrorCode(e.code).name, e.code, (sys.exc_info()[-1].tb_lineno)))
        except ChannelError as ce:
            print(f"Channel Error: {ce}")
        return line,
    else:
        return line,



def init():
    x_zero=12  
    y_zero=12
    N = 1000                                       # If N is large one can see the axes
    plate_extent = 24
    x = -np.linspace(0.0, plate_extent, N)+x_zero              
    y = -x-y_zero+x_zero
    ax.set_xlim(xmax=max(x), xmin=min(x))
    ax.set_ylim(ymin=min(y), ymax=max(y))
    ax.set_xlabel('axis a')
    ax.set_ylabel('axis b')
    ax.set_title('Motor Scan Area')
    ax.scatter(0,0,marker='+',c='r') # plot where the zero is for the plate
    # plot zero for laser in blue
    ax.scatter(x, (plate_extent/2-y_zero)*np.ones(len(x)),c='b', marker='.',s=.1)  
    ax.scatter((-plate_extent/2+x_zero)*np.ones(len(x)), y,c='b', marker='.',s=.1) 
    line.set_data(xdata, ydata)
    return line,


# main execution blocks start here

# establish a connection with the controller
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
    # Initialize plot
    fig, ax = plt.subplots(figsize=(15, 12))
    xdata, ydata = [0], [np.sin(0)] # potentially rather start with 
    line, = plt.plot([], [], 'r',linestyle='-')
    # add widgets
    plt.subplots_adjust(bottom=0.2) # Adjust the bottom to make room for the button
    stop_button_ax = plt.axes([0.7, 0.05, 0.1, 0.075])  # [left, bottom, width, height]
    stop_button = Button(stop_button_ax, 'Toggle Scanning', color='red', hovercolor='salmon')
    stop_button.on_clicked(stop_scanning)
    toggle_selector.RS = RectangleSelector(ax, line_select_callback,drawtype='box', useblit=True,button=[1, 3], minspanx=5, minspany=5,spancoords='pixels',interactive=True)
    plt.connect('key_press_event', toggle_selector)

    d_handle = ctl.Open(locators[0])
    print("MCS2 opened {}.".format(locators[0]))
    reference_motor(d_handle)
    set_scan_properties(d_handle)
    loop_index = 0

    ani = FuncAnimation(fig, update, frames=np.linspace(0, 2 * np.pi, 128),
                    init_func=init, blit=True, repeat=True)

    plt.show()
    ctl.Close(d_handle)
    print("MCS2 close.")
    print("*******************************************************")

    
 
except Exception as e:
    print("Main process failed")
    raise




