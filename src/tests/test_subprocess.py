import subprocess

started = False

while True:
    if not started:
        subprocess.Popen(['python', 'test_child.py'])
        started = True
