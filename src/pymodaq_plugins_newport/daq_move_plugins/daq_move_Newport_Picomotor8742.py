from typing import Union, List, Dict

from pymodaq.control_modules.move_utility_classes import DAQ_Move_base,\
    comon_parameters_fun, main, DataActuatorType, DataActuator  # common set of parameters for all actuators
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
    _controller_units: Union[str, List[str]] = ''
    is_multiaxes = True
    axes_names: Union[List[str], Dict[str, int]] = {'1': 1, '2': 2, '3': 3, '4': 4}
    _epsilon: Union[float, List[float]] = 10.0
    data_actuator_type = DataActuatorType.DataActuator
    
    params = [
              {'title': 'IP address:', 'name': 'ip', 'type': 'str','value': "192.168.0.109"},
              {'title': 'Axis parameters: ', 'name': 'axis_p','type': 'group','children':[
                  {'title': 'Velocity (steps/s): ', 'name': 'speed_axis','type': 'int',
                   'value':0,'min':1,'max':2e3},
                  {'title': 'Acceleration (steps/s^2): ', 'name': 'acc_axis', 'type': 'int',
                   'value':0,'min':1,'max':2e5},
                  {'title': 'Type: ', 'name': 'motor', 'type':'str','value':'None'},]}] + \
                  comon_parameters_fun(is_multiaxes, axes_names, epsilon=_epsilon)

    
    def ini_attributes(self):
        self.controller: Newport.Picomotor8742 = None

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        axis = self.axis_value
        pos = DataActuator(data=self.controller.get_position(axis=axis))
        pos = self.get_position_with_scaling(pos)
        return pos

    def close(self):
        """Terminate the communication """
        self.controller.close()  

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() == 'speed_axis' or param.name() == 'acc_axis':
            self.controller.setup_velocity(axis=self.axis_value,
                                           speed=self.settings['axis_p','speed_axis'],
                                           accel=self.settings['axis_p','acc_axis'])
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
        self.controller = self.ini_stage_init(slave_controller=controller)

        if self.is_master:
            self.controller = Newport.Picomotor8742(self.settings['ip'])

        try:
            info = self.controller.get_id()
            initialized = True
        except:
            info = ""
            initialized = False

        if initialized:
            motor_types = self.controller.autodetect_motors()
            axis = self.axis_value
            self.settings['axis_p','motor'] = motor_types[axis-1]
           
            parameters_velocity = self.controller.get_velocity_parameters()
            self.settings['axis_p','speed_axis'] = parameters_velocity[axis-1][0]
            self.settings['axis_p','acc_axis'] = parameters_velocity[axis-1][1]
            
        return info, initialized
    
    def move_abs(self, value: DataActuator):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        value = self.check_bound(value)  #if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one

        self.controller.move_to(self.axis_value, value.value())  
        self.emit_status(ThreadCommand('Update_Status',
                                       [f'The actuator is moved {value.value()} steps.']))

    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        self.controller.move_by(self.axis_value, steps=value.value()) 
        self.emit_status(ThreadCommand('Update_Status',
                    [f'The actuator is moved according to its current position of {value.value()} steps.']))

    def move_home(self):
        """Do nothing"""
        pass
        
    def stop_motion(self):
      """Stop the actuator and emits move_done signal"""
      self.controller.stop(axis=self.axis_value)
      self.emit_status(ThreadCommand('Update_Status', ['The motion of the actuator is stopped.']))


if __name__ == '__main__':
    main(__file__)
