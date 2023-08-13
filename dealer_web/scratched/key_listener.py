# key_listener.py
from pynput import keyboard

is_ctrl_pressed = False
is_ctrl_s_pressed = False


def on_key_press(key):
    global is_ctrl_pressed, is_ctrl_s_pressed

    try:
        if key == keyboard.Key.ctrl_l:  # Check for left Ctrl key
            is_ctrl_pressed = True
        elif key.char == 's' and is_ctrl_pressed:
            is_ctrl_s_pressed = True
    except AttributeError:
        pass


def on_key_release(key):
    global is_ctrl_pressed, is_ctrl_s_pressed

    try:
        if key == keyboard.Key.ctrl_l:  # Check for left Ctrl key
            is_ctrl_pressed = False
        elif key.char == 's':
            is_ctrl_s_pressed = False
    except AttributeError:
        pass


def start_key_listener():
    # Create a listener
    listener = keyboard.Listener(
        on_press=on_key_press, on_release=on_key_release)

    # Start listening for keypress events
    listener.start()
