from matplotlib.widgets import RectangleSelector
from matplotlib.widgets import Button
import numpy as np
import sys
import matplotlib.pyplot as plt
from move import set_scan_properties
from move import reference_motor
from move import snake_scan
import smaract.ctl as ctl

a_max = []
b_max = []
a_min = []
b_min = []

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

# plots available space for the motor to move
def get_plot(N=1000, x_zero=14,y_zero=13):
    # N number of points to use
    # x_zero referenced zero for the laser alignment along axis a
    # y_zero referenced zero for the laser alignment along axis b

    fig, current_ax = plt.subplots()                 # make a new plotting range
    plt.subplots_adjust(bottom=0.2) # Adjust the bottom to make room for the button
    N = 1000                                       # If N is large one can see the axes
    plate_extent = 24
    x = -np.linspace(0.0, plate_extent, N)+x_zero               # improvement by use blitting!
    y = -x-y_zero+x_zero

    plt.scatter(0,0,marker='+',c='r') # plot where the zero is for the plate
    # plot zero for laser in blue
    plt.scatter(x, (plate_extent/2-y_zero)*np.ones(len(x)),c='b', marker='.', alpha=.02)  
    plt.scatter((-plate_extent/2+x_zero)*np.ones(len(x)), y,c='b', marker='.', alpha=.02)  
    plt.legend(['plate','laser'])
    plt.axis([max(x), min(x), min(y), max(y)])
    plt.xlabel('axis a')
    plt.ylabel('axis b')
    plt.title('Motor Scan Area')
    print("\n      click  -->  release")

    # would like to implement this section with the stop_scanning button rather than use ctl+D but would need to multi-thread
    #stop_button_ax = plt.axes([0.7, 0.05, 0.1, 0.075])  # [left, bottom, width, height]
    #stop_button = Button(stop_button_ax, 'Stop', color='red', hovercolor='salmon')
    #stop_button.on_clicked(stop_scanning)

    # drawtype is 'box' or 'line' or 'none'
    toggle_selector.RS = RectangleSelector(current_ax, line_select_callback,drawtype='box', useblit=True,button=[1, 3], minspanx=5, minspany=5,spancoords='pixels',interactive=True)
    plt.connect('key_press_event', toggle_selector)
    plt.show(block=True)

# main code block
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
    get_plot()
    d_handle = ctl.Open(locators[0])
    print("MCS2 opened {}.".format(locators[0]))
    reference_motor(d_handle)
    set_scan_properties(d_handle)
    boundaries_container = [[b_min[0],b_max[0]],[a_min[0],a_max[0]]]
    snake_scan(d_handle,boundaries_container)
except Exception as e:
    print("Main process failed")
    raise