from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main  # common set of parameters for all actuators
from pymodaq.utils.daq_utils import ThreadCommand # object used to send info back to the main thread
from pymodaq.utils.parameter import Parameter
from pylablib.devices import Newport



class DAQ_Move_Newport_Picomotor8742(DAQ_Move_base):
    """Plugin for the Template Instrument

    This object inherits all functionality to communicate with PyMoDAQ Module through inheritance via DAQ_Move_base
    It then implements the particular communication with the instrument

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library
    # TODO add your particular attributes here if any

    """
    _controller_units = 'step'  # TODO for your plugin: put the correct unit here
    is_multiaxes = True  # TODO for your plugin set to True if this plugin is controlled for a multiaxis controller
    axes_names = ['1', '2','3','4']  # TODO for your plugin: complete the list
    _epsilon = 0.1  # TODO replace this by a value that is correct depending on your controller

    params = [
              {'title': 'IP address:', 'name': 'IP', 'type': 'str','value': "192.168.0.107"},
              {'title': 'Velocity_axis1 (steps/s): ', 'name': 'speed_axis1','type': 'int','value':0 },
              {'title': 'Acceleration_axis1 (steps/s^2): ', 'name': 'acc_axis1', 'type': 'int','value':0},
              {'title': 'Velocity_axis2 (steps/s): ', 'name': 'speed_axis2', 'type': 'int','value':0 },
              {'title': 'Acceleration_axis2 (steps/s^2): ', 'name': 'acc_axis2', 'type': 'int','value':0},
              {'title': 'Velocity_axis3 (steps/s): ', 'name': 'speed_axis3', 'type': 'int','value':0 },
              {'title': 'Acceleration_axis3 (steps/s^2): ', 'name': 'acc_axis3', 'type': 'int','value':0},
              {'title': 'Velocity_axis4 (steps/s): ', 'name': 'speed_axis4', 'type': 'int','value':0 },
              {'title': 'Acceleration_axis4 (steps/s^2): ', 'name': 'acc_axis4', 'type': 'int','value':0},
              {'title': 'MOTOR Type: ', 'name': 'Motor-type', 'type': 'str','value':'None'}, ] + comon_parameters_fun(is_multiaxes, axes_names, epsilon=_epsilon)
    # _epsilon is the initial default value for the epsilon parameter allowing pymodaq to know if the controller reached
    # the target value. It is the developer responsibility to put here a meaningful value

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        ## TODO for your custom plugin
        axis = int(self.settings.child('multiaxes', 'axis').value())
        if axis == 1:
            pos = self.controller.get_position(axis=1)
        elif axis==2:
            pos = self.controller.get_position(axis=2)
        elif axis==3:
            pos = self.controller.get_position(axis=3)
        else:
            pos = self.controller.get_position(axis=4)
        return pos

    def close(self):
        """Terminate the communication protocol"""
        ## TODO for your custom plugin
       
        self.controller.close()  # when writing your own plugin replace this line

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        ## TODO for your custom plugin
        if param.name() == 'speed_axis1' or param.name() == 'acc_axis1':
           self.controller.setup_velocity(axis=1,speed = self.settings.child('speed_axis1').value(), accel= self.settings.child('acc_axis1').value() )
        if param.name() == 'speed_axis2' or param.name() == 'acc_axis2':
            self.controller.setup_velocity(axis=2,speed = self.settings.child('speed_axis2').value(), accel= self.settings.child('acc_axis2').value() )
        if param.name() == 'speed_axis3' or param.name() == 'acc_axis3':
            self.controller.setup_velocity(axis=3,speed = self.settings.child('speed_axis3').value(), accel= self.settings.child('acc_axis3').value() )
        if param.name() == 'speed_axis4' or param.name() == 'acc_axis4':
            self.controller.setup_velocity(axis=4,speed = self.settings.child('speed_axis4').value(), accel= self.settings.child('acc_axis4').value() )
        else:
            pass

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

       
        self.controller = self.ini_stage_init(old_controller=controller,
                                              new_controller= Newport.Picomotor8742(self.settings.child('IP').value()))

        info = self.controller.get_id()
        initialized = True  # todo
        if initialized:
            Motor_type = self.controller.autodetect_motors()
            #Motor_type =self.controller.get_motor_type(axis ='all')
            self.settings.child('Motor-type').setValue(Motor_type)
            axis = int(self.settings.child('multiaxes', 'axis').value())
            #print('axis is ',axis)
            #speed,acc= self.controller.get_velocity_parameters(axis=axis)
            #self.settings.child('speed_axis1').setValue(speed)
            #self.settings.child('acc_axis1').setValue(acc)
            parameters_velocity = self.controller.get_velocity_parameters()
            for k in [1,2,3,4]:
                for i in parameters_velocity:
                    self.settings.child('speed_axis{}'.format(k)).setValue(i[0])
                    self.settings.child('acc_axis{}'.format(k)).setValue(i[1])
        return info, initialized 

    def move_abs(self, value):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        value = self.check_bound(value)  #if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one
        axis = int(self.settings.child('multiaxes', 'axis').value())
        self.controller.move_to(axis,value)  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['The actuator is moved {} steps'.format(value)]))


    def move_rel(self, value):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        ## TODO for your custom plugin
        axis = int(self.settings.child('multiaxes', 'axis').value())
        self.controller.move_by(axis,steps=value)  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['The actuator is moved accoridng to its current position {} steps'.format(value)]))


    def move_home(self):
        """Call the reference method of the controller"""

        ## TODO for your custom plugin
        axis = int(self.settings.child('multiaxes', 'axis').value())
        self.controller.move_to(axis,0)  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['The actuator is move to its initial position which is zero']))
    
        
    def stop_motion(self):
      """Stop the actuator and emits move_done signal"""

      ## TODO for your custom plugin
      axis = int(self.settings.child('multiaxes', 'axis').value())
      self.controller.stop(axis=axis)  # when writing your own plugin replace this line
      self.emit_status(ThreadCommand('Update_Status', ['the motion of the actuator is stopped']))


if __name__ == '__main__':
    main(__file__)
