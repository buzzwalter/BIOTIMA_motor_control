## Smaract Snake Scan
This motor control code was written for a matrix assisted laser desorption (MALDI) setup with a ToF spectrometer.  The purpose was to take an MCS2 controller and 2 axis motor with a mounted 24 mm x 24 mm plate to scan multiple samples inside of our ToF chamber with a desorption laser. This improves efficiency up to four-fold because one can now scan 4 samples per evacuation period rather than just stick to one.  The ToF used in this setup required ~ $10^{-7}$ mbar, so it would often take almost a whole work day to exchange a sample.  The motor scans in snake pattern to maximize use of the sample. 

![ex_run](https://github.com/buzzwalter/BIOTIMA_motor_control/assets/38196547/9c8979a5-e597-40e8-a5fc-e7fe693cae8f)


### Dependencies
The gui uses the rectangle selector tool from matplotlib version 4.3.4 which is handled differently in modern versions.  In order to use 4.3.4 numpy version 1.6.1 is used.  For information on how to manage python environments, to setup these installations, see the [managing environments](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) page from conda.
