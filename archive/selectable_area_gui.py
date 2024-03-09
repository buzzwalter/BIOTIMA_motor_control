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