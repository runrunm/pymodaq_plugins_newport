from .XPS_Q8_drivers import XPS


class XPSPythonWrapper:
    """Simplified XPS wrapper, calls methods from the wrapper given by Newport. See XPS_Q8_drivers"""

    def __init__(
        self,
        ip: str = None,
        port: int = None,
        group: str = None,
        positionner: str = None,
        plugin=None,
    ):
        # init the wrapper given by Newport and some attributes
        self.myxps = XPS()  # Instanciate the driver from Newport

        # keep a ref of the plugin to emit (error) messages
        self._plugin = plugin

        # required to connect via TCP/IP
        self._ip = ip
        self._port = port
        self.socketId = -1

        # Definition of the stage
        self._group = group
        self._positioner = positionner
        self._full_positionner_name = f"{group}.{positionner}"

        # Some required initialisation steps
        self._initCommands()

    def _initCommands(self):
        """Runs some initial commands : connect to the XPS server, group kill, group intialize, move home.
        Some configs could be added here as well"""
        self.socketId = self.myxps.TCP_ConnectToServer(
            self._ip, self._port, 20
        )  # 20s timeout
        # Check connection passed
        if self.socketId == -1:
            self._plugin.emit_status(
                ThreadCommand(
                    "Update_Status", ["Connection to XPS failed, check IP & Port"]
                )
            )
        else:
            self._plugin.emit_status(
                ThreadCommand("Update_Status", ["Connected to XPS"])
            )

            # Group kill to be sure
            [errorCode, returnString] = self.myxps.GroupKill(self.socketId, self._group)
            if errorCode != 0:
                self.displayErrorAndClose(errorCode, "GroupKill")

            # Initialize
            [errorCode, returnString] = self.myxps.GroupInitialize(
                self.socketId, self._group
            )
            if errorCode != 0:
                self.displayErrorAndClose(errorCode, "GroupInitialize")

            # Home search
            self.moveHome()

            # Definition of the MotionDone trigger
            # [errorCode, returnString] = self.myxps.EventExtendedConfigurationTriggerSet(self.socketId, 'MotionDone',0,0,0,0)
            # if (errorCode != 0):
            #     self.displayErrorAndClose(errorCode, 'EventExtendedConfigurationTriggerSet')
            #     sys.exit()
            # [errorCode, returnString] = self.myxps.EventExtendedConfigurationActionSet(self.socketId, , 0, 0, 0, 0)
            # if (errorCode != 0):
            #     self.displayErrorAndClose(errorCode, 'EventExtendedConfigurationActionSet')
            #     sys.exit()

    def checkConnected(self):
        """Returns true if the connection was successful, else false."""
        return self.socketId != -1

    def displayErrorAndClose(self, errorCode, APIName):
        """Method to recover an error string based on an error code. Closes the TCPIP connection afterwards"""
        if (errorCode != -2) and (errorCode != -108):
            [errorCode2, errorString] = self.myxps.ErrorStringGet(
                self.socketId, errorCode
            )
            if errorCode2 != 0:
                self._plugin.emit_status(
                    ThreadCommand("Update_Status", [f"{APIName} : ERROR {errorCode}"])
                )
            else:
                self._plugin.emit_status(
                    ThreadCommand("Update_Status", [f"{APIName} : {errorString}"])
                )
        else:
            if errorCode == -2:
                self._plugin.emit_status(
                    ThreadCommand("Update_Status", [f"{APIName} : TCP timeout"])
                )
            if errorCode == -108:
                self._plugin.emit_status(
                    ThreadCommand(
                        "Update_Status",
                        [
                            f"{APIName} : The TCP/IP connection was closed by an administrator"
                        ],
                    )
                )
        self.closeTCPIP()

    def closeTCPIP(self):
        """Call the method to close the socket."""
        self.myxps.TCP_CloseSocket(self.socketId)

    def getPosition(self):
        """Returns current the position"""
        [errorCode, currentPosition] = self.myxps.GroupPositionCurrentGet(
            self.socketId, self._full_positionner_name, 1
        )
        if errorCode != 0:
            self.displayErrorAndClose(errorCode, "GroupPositionCurrentGet")
            sys.exit()
        else:
            return float(currentPosition)

    def moveAbsolute(self, value):
        """Moves the stage to the position value."""
        if self.socketId != -1:
            [errorCode, returnString] = self.myxps.GroupMoveAbsolute(
                self.socketId, self._full_positionner_name, [value]
            )
            if errorCode != 0:
                self.displayErrorAndClose(errorCode, "GroupMoveAbsolute")

    def moveRelative(self, value):
        """Moves the stage to value relative to it's current position."""
        if self.socketId != -1:
            [errorCode, returnString] = self.myxps.GroupMoveRelative(
                self.socketId, self._full_positionner_name, [value]
            )
            if errorCode != 0:
                self.displayErrorAndClose(errorCode, "GroupMoveRelative")

    def moveHome(self):
        """Moves the stage to it's home"""
        if self.socketId != -1:
            [errorCode, returnString] = self.myxps.GroupHomeSearch(
                self.socketId, self._group
            )
            if errorCode != 0:
                self.displayErrorAndClose(errorCode, "GroupHomeSearch")

    def setGroup(self, group: str):
        self._group = group
        self._full_positionner_name = f"{group}.{self._positionner}"

    def setPositionner(self, positionner: str):
        self._positionner = positionner
        self._full_positionner_name = f"{self._group}.{positionner}"

    def setIP(self, IP: str):
        """Sets a new IP address. Does not automatically try to connect with it, call retryConnection."""
        self._ip = IP

    def setPort(self, port: int):
        """Sets a new port. Does not automatically try to connect with it, call retryConnection."""
        self._port = port

    def retryConnection(self):
        """Closes the connection and runs the init sequence again.
        Called by the plugin after any change to the IP address or port parameters."""
        self.closeTCPIP()
        self._initCommands()
