from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main  # common set of parameters for all actuators
from pymodaq.utils.daq_utils import ThreadCommand # object used to send info back to the main thread
from pymodaq.utils.parameter import Parameter
from pylablib.devices import Newport



class DAQ_Move_Newport_Picomotor8742(DAQ_Move_base):
    """Plugin for the Picomotor 8742.

    Attributes:
    -----------
    controller: Newport.Picomotor8742
        The particular object that allow the communication with the hardware, from pylablib

    """
    _controller_units = 'step'  
    is_multiaxes = False  
    axes_names = [ ]  
    _epsilon = 0.1  

    params = [
              {'title': 'IP address:', 'name': 'ip', 'type': 'str','value': "192.168.0.107"},
              {'title': 'Axis number', 'name': 'axis_nb', 'type': 'int', 'value':1},
              {'title': 'Axis parameters: ', 'name': 'axis_p','type': 'group','children':[
                  {'title': 'Velocity (steps/s): ', 'name': 'speed_axis','type': 'int','value':0,'min':1,'max':2e3 },
                  {'title': 'Acceleration (steps/s^2): ', 'name': 'acc_axis', 'type': 'int','value':0,'min':1,'max':2e5},
                  {'title': 'Type: ', 'name': 'motor', 'type':'str','value':'None'},]}] + comon_parameters_fun(is_multiaxes, axes_names, epsilon=_epsilon)
    # _epsilon is the initial default value for the epsilon parameter allowing pymodaq to know if the controller reached
    # the target value. It is the developer responsibility to put here a meaningful value

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        axis = int(self.settings.child('axis_nb').value())
        pos = self.controller.get_position(axis=axis)
        return pos

    def close(self):
        """Terminate the communication """
        self.controller.close()  # when writing your own plugin replace this line

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() == 'speed_axis' or param.name() == 'acc_axis':
            axis = int(self.settings.child('axis_nb').value())
            self.controller.setup_velocity(axis=axis, speed=self.settings.child('axis_p','speed_axis').value(),
                                           accel=self.settings.child('axis_p','acc_axis').value() )
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
                                              new_controller= Newport.Picomotor8742(self.settings.child('ip').value()))

        try:
            info = self.controller.get_id()
            initialized = True
        except:
            info = ""
            initialized = False
            
        if initialized:
            motor_types = self.controller.autodetect_motors()
            axis = int(self.settings.child('axis_nb').value())
            self.settings.child('axis_p','motor').setValue(motor_type[axis-1])
           
            parameters_velocity = self.controller.get_velocity_parameters()
            self.settings.child('axis_p','speed_axis').setValue(parameters_velocity[axis][0])
            self.settings.child('axis_p','acc_axis').setValue(parameters_velocity[axis][1])
            
        return info, initialized 

    def move_abs(self, value):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        value = self.check_bound(value)  #if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one*
        
        axis = int(self.settings.child('axis_nb').value())
        self.controller.move_to(axis, value)  # when writing your own plugin replace this line
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

        axis = int(self.settings.child('axis_nb').value())
        self.controller.move_by(axis, steps=value)  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['The actuator is moved according to its current position of {} steps'.format(value)]))


    def move_home(self):
        """Do nothing"""
        pass
        
        
    def stop_motion(self):
      """Stop the actuator and emits move_done signal"""
      axis = int(self.settings.child('axis_nb').value())
      self.controller.stop(axis=axis)  # when writing your own plugin replace this line
      self.emit_status(ThreadCommand('Update_Status', ['the motion of the actuator is stopped']))


if __name__ == '__main__':
    main(__file__)
