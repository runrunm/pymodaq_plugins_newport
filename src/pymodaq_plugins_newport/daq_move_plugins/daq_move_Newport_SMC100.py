from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuator
# common set of parameters for all actuators
from pymodaq.utils.daq_utils import ThreadCommand  # object used to send info back to the main thread
from pymodaq.utils.parameter import Parameter

from pymodaq_plugins_newport.hardware.smc100 import SMC100

import pyvisa

rm = pyvisa.ResourceManager()
infos = rm.list_resources_info()
port_nb = [infos[key].interface_board_number for key in infos.keys()][0]
dev_nb = 1
rm.close()

class DAQ_Move_Newport_SMC100(DAQ_Move_base):
    """ Instrument plugin class for an actuator.

    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Move module through inheritance via
    DAQ_Move_base. It makes a bridge between the DAQ_Move module and the Python wrapper of a particular instrument.

    TODO Complete the docstring of your plugin with:
        * The set of controllers and actuators that should be compatible with this instrument plugin.
        * With which instrument and controller it has been tested.
        * The version of PyMoDAQ during the test.
        * The version of the operating system.
        * Installation instructions: what manufacturer’s drivers should be installed to make it run?

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.

    # TODO add your particular attributes here if any
    """
    _controller_units = '°'  # DONE for your plugin: put the correct unit here
    is_multiaxes = False
    _axis_names = ['1']
    _epsilon = 0.0001

    params = [{'title': 'COM Port:', 'name': 'com_port', 'type': 'str', 'value': f'COM{port_nb}'}  # TODO for your custom plugin: elements to be added here as dicts in order to control your custom stage
             ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    # print(params[0]['title'])

    # _epsilon is the initial default value for the epsilon parameter allowing pymodaq to know if the controller reached
    # the target value. It is the developer responsibility to put here a meaningful value

    def ini_attributes(self):
        #  TODO declare the type of the wrapper (and assign it to self.controller) you're going to use for easy
        #  autocompletion
        self.controller: SMC100 = None

        # TODO declare here attributes you want/need to init with a default value
        pass

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        pos = DataActuator(data=self.controller.position)  # when writing your own plugin replace this line
        pos = self.get_position_with_scaling(pos)
        return pos

    def close(self):
        """Terminate the communication protocol"""
        self.controller.reset()
        self.controller.close()

    # def commit_settings(self, param: Parameter):
    #     """Apply the consequences of a change of value in the detector settings
    #
    #     Parameters
    #     ----------
    #     param: Parameter
    #         A given parameter (within detector_settings) whose value has been changed by the user
    #     """
    #     ## TODO for your custom plugin
    #     # if param.name() == "a_parameter_you've_added_in_self.params":
    #     #     self.controller.your_method_to_apply_this_param_change()
    #     # else:
    #     #     pass

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
                                              new_controller=SMC100(port=port_nb, dev_number=dev_nb))

        info = "Whatever info you want to log"
        self.controller.initialize()
        initialized = True
        return info, initialized

    # def move_abs(self, value: DataActuator):
    #     """ Move the actuator to the absolute target defined by value
    #
    #     Parameters
    #     ----------
    #     value: (float) value of the absolute target positioning
    #     """
    #
    #     value = self.check_bound(value)  # if user checked bounds, the defined bounds are applied here
    #     self.target_value = value
    #     value = self.set_position_with_scaling(value)  # apply scaling if the user specified one
    #     ## TODO for your custom plugin
    #     raise NotImplemented  # when writing your own plugin remove this line
    #     self.controller.your_method_to_set_an_absolute_value(
    #         value.value())  # when writing your own plugin replace this line
    #     self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))

    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        self.controller.move_rel(value)  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))

    def move_home(self):
        """Call the reference method of the controller"""

        ## TODO for your custom plugin
        self.controller.home()  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))

    # def stop_motion(self):
    #     """Stop the actuator and emits move_done signal"""
    #
    #     ## TODO for your custom plugin
    #     raise NotImplemented  # when writing your own plugin remove this line
    #     self.controller.your_method_to_stop_positioning()  # when writing your own plugin replace this line
    #     self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))


if __name__ == '__main__':
    main(__file__)