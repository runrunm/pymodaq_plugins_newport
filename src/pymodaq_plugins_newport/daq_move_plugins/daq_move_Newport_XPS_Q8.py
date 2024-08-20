from pymodaq.control_modules.move_utility_classes import (
    DAQ_Move_base,
    comon_parameters_fun,
    main,
    DataActuatorType,
    DataActuator,
)  # common set of parameters for all actuators
from pymodaq.utils.daq_utils import (
    ThreadCommand,
)  # object used to send info back to the main thread
from pymodaq.utils.parameter import Parameter
from pymodaq_plugins_newport.hardware.xps_q8_simplified import (
    XPSPythonWrapper,
    XPSError,
)


class DAQ_Move_Newport_XPS_Q8(DAQ_Move_base):
    """Instrument plugin class for Newport_XPS_Q8 Motion Controller.

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

    """

    _controller_units = "mm"
    is_multiaxes = False
    _axis_names = ["Axis1"]
    _epsilon = 600e-6
    data_actuator_type = DataActuatorType["DataActuator"]

    params = [
        {
            "title": "XPS IP address :",
            "name": "xps_ip_address",
            "type": "str",
            "value": "192.168.0.254",
        },  # IP address of my system
        {
            "title": "XPS Port :",
            "name": "xps_port",
            "type": "int",
            "value": 5001,
        },  # Port of my system, should be the same for others ?
        {
            "title": "Group :",
            "name": "group",
            "type": "str",
            "value": "Group2",
        },  # Group to be moved
        {
            "title": "Positionner :",
            "name": "positionner",
            "type": "str",
            "value": "Pos",
        },  # positionner to be moved
    ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller: XPSPythonWrapper = None

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        pos = DataActuator(data=self.controller.get_position())
        pos = self.get_position_with_scaling(pos)
        return pos

    def close(self):
        """Terminate the communication protocol"""
        self.controller.close_tcpip()

    def commit_settings(self, param: Parameter):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        if param.name() == "xps_ip_address":
            self.controller.set_ip(param.value())
            self.controller.retry_connection()
        elif param.name() == "xps_port":
            self.controller.set_port(param.value())
            self.controller.retry_connection()
        elif param.name() == "group":
            self.controller.set_group(param.value())
        elif param.name() == "positionner":
            self.controller.set_positionner(param.value())
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

        info = "XPS_Q8 initialization"
        try:
            new_controller = XPSPythonWrapper(
                ip=self.settings["xps_ip_address"],
                port=self.settings["xps_port"],
                group=self.settings["group"],
                positionner=self.settings["positionner"],
            )
        except XPSError as e:
            self.emit_status(ThreadCommand("Update_Status", [f"{e}"]))
            initialized = False
            return info, initialized
        else:
            self.controller = self.ini_stage_init(
                old_controller=controller,
                new_controller=new_controller,
            )

        initialized = self.controller.check_connected()
        if not initialized:
            self.emit_status(
                ThreadCommand(
                    "Update_Status",
                    ["XPS_Q8 connection failed. Check ip address and port."],
                )
            )
        return info, initialized

    def move_abs(self, value: DataActuator):
        """Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """
        value = self.check_bound(
            value
        )  # if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(
            value
        )  # apply scaling if the user specified one
        self.emit_status(ThreadCommand("Update_Status", ["move_absolute command sent"]))
        try:
            self.controller.move_absolute(value.value())
        except XPSError as e:
            self.emit_status(ThreadCommand("Update_Status", [f"{e}"]))

    def move_rel(self, value: DataActuator):
        """Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        self.emit_status(ThreadCommand("Update_Status", ["move_relative command sent"]))
        try:
            self.controller.move_relative(value.value())
        except XPSError as e:
            self.emit_status(ThreadCommand("Update_Status", [f"{e}"]))

    def move_home(self):
        """Call the reference method of the controller"""
        self.emit_status(ThreadCommand("Update_Status", ["moved_home command sent"]))
        try:
            self.controller.move_home()
        except XPSError as e:
            self.emit_status(ThreadCommand("Update_Status", [f"{e}"]))

    def stop_motion(self):
        """NOT IMPLEMENTED --- Stop the actuator and emits move_done signal"""

        ## Not possible to implement with this system as far as I'm aware.

        raise NotImplementedError  # when writing your own plugin remove this line
        self.controller.your_method_to_stop_positioning()  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand("Update_Status", ["Some info you want to log"]))


if __name__ == "__main__":
    main(__file__)
