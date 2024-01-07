import sys
import os
import platform
import socket
import ac_api.car_info as ci
import ac_api.input_info as ii
import ac_api.lap_info as li

# The name of the app (ACRL: Assetto Corsa Reinforcement Learning)
APP_NAME = 'ACRL'

# Add the third party libraries to the path
try:
    if platform.architecture()[0] == "64bit":
        sysdir = "stdlib64"
    else:
        sysdir = "stdlib"
    sys.path.insert(
        len(sys.path), 'apps/python/{}/third_party'.format(APP_NAME))
    os.environ['PATH'] += ";."
    sys.path.insert(len(sys.path), os.path.join(
        'apps/python/{}/third_party'.format(APP_NAME), sysdir))
    os.environ['PATH'] += ";."
except Exception as e:
    ac.log("[ACRL] Error importing libraries: %s" % e)

import ac  # noqa: E402
from IS_ACUtil import *  # noqa: E402

# Training enabled flag
training = False

# Socket variables
HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 65432  # The port used by the server
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False

# Label & button variables
label_model_info = None
btn_start = None
btn_stop = None


def acMain(ac_version):
    """
    The main function of the app, called on app start.
    :param ac_version: The version of Assetto Corsa as a string.
    """
    global label_model_info, btn_start, btn_stop
    ac.console("[ACRL] Initializing...")

    # Create the app window
    APP_WINDOW = ac.newApp(APP_NAME)
    ac.setSize(APP_WINDOW, 320, 150)
    ac.setTitle(APP_WINDOW, APP_NAME +
                ": Reinforcement Learning")

    # Background fully black
    ac.setBackgroundOpacity(APP_WINDOW, 1)

    # Info label
    label_model_info = ac.addLabel(
        APP_WINDOW, "Training: " + str(training) + "\nClick start to begin!")
    ac.setPosition(label_model_info, 320/2, 40)
    ac.setFontAlignment(label_model_info, "center")

    # Start button
    btn_start = ac.addButton(APP_WINDOW, "Start Model")
    ac.setPosition(btn_start, 20, 100)
    ac.setSize(btn_start, 120, 30)
    ac.addOnClickedListener(btn_start, start)
    ac.setVisible(btn_start, 1)

    # Stop button
    btn_stop = ac.addButton(APP_WINDOW, "Stop Model")
    ac.setPosition(btn_stop, 320/2 + 10, 100)
    ac.setSize(btn_stop, 120, 30)
    ac.addOnClickedListener(btn_stop, stop)
    ac.setVisible(btn_stop, 0)

    # Try to connect to socket
    connect()

    ac.console("[ACRL] Initialized")
    return APP_NAME


def acUpdate(deltaT):
    """
    The update function of the app, called every frame.
    Here we get the data from the game, and send it over the socket to the RL model.
    :param deltaT: The time since the last frame as a float.
    """
    global label_model_info, training

    # Update the model info label
    ac.setText(label_model_info, "Training: " + str(training))

    # If not training, don't do anything
    if not training:
        return

    # If the socket is not connected, try to connect
    if not connect():
        ac.console(
            "[ACRL] Socket could not connect to host in acUpdate, stopping training!")
        stop()
        return

    # Send the data to the model
    try:
        # Get the data from the game
        track_progress = ci.get_location()
        speed_kmh = ci.get_speed()
        world_loc = ci.get_world_location()
        throttle = ii.get_gas_input()
        brake = ii.get_brake_input()
        steer = ii.get_steer_input()
        lap_time = li.get_current_lap_time()
        lap_invalid = li.get_invalid()
        lap_count = li.get_lap_count()

        # Turn the data into a string
        data = "track_progress:" + str(track_progress) + "," + "speed_kmh:" + str(speed_kmh) + "," + "world_loc[0]:" + str(world_loc[0]) + "," + "world_loc[1]:" + str(world_loc[1]) + "," + "world_loc[2]:" + str(world_loc[2]) + "," + "throttle:" + str(
            throttle) + "," + "brake:" + str(brake) + "," + "steer:" + str(steer) + "," + "lap_time:" + str(lap_time) + "," + "lap_invalid:" + str(lap_invalid) + "," + "lap_count:" + str(lap_count)
        # Send the data in bytes
        sock.sendall(str.encode(data))
    except Exception as e:
        ac.console("[ACRL] EXCEPTION: could not send data!")
        ac.console(e)


def acShutdown():
    """
    The shutdown function of the app, called on app close.
    """
    global training
    training = False
    sock.close()
    ac.console("[ACRL] Shutting down...")


def start(*args):
    """
    The function called when the start button is pressed.
    :param args: The arguments passed to the function.
    """
    global btn_start, btn_stop, training
    if not connect():
        ac.console("[ACRL] Didn't start model, could not connect to socket!")
        stop()
        return

    ac.console("[ACRL] Starting model...")

    ac.setVisible(btn_start, 0)
    ac.setVisible(btn_stop, 1)
    training = True


def stop(*args):
    """
    The function called when the stop button is pressed.
    :param args: The arguments passed to the function.
    """
    global btn_start, btn_stop, training
    ac.console("[ACRL] Stopping model...")

    ac.setVisible(btn_start, 1)
    ac.setVisible(btn_stop, 0)
    training = False


def connect():
    """
    Attempts to connect to the socket server.
    """
    try:
        sock.connect((HOST, PORT))
        ac.console("[ACRL] Socket connection successful!")
        return True
    except:
        ac.console("[ACRL] Socket could not connect to host...")
        return False


def respawn():
    """
    Respawns the car at the finish line.
    """
    # TODO; make this a button listener so it can be called from the standalone app's controller
    ac.console("[ACRL] Respawning...")
    # Restart to session menu
    sendCMD(68)
    # Start the lap + driving
    sendCMD(69)
