import os

def is_dev_server():
    if os.environ['SERVER_SOFTWARE'].find('Development') == 0:
        return True
    else:
        return False