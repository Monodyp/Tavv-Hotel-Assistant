import os
import subprocess
import venv

def setup_venv(venv_path="venv", requirements="req.txt", log_file=None):
    """
    Creates a virtual environment if it doesn't exist and installs dependencies.
    Suppresses verbose pip output or writes it to a log file.
    """
    if not os.path.exists(venv_path):
        print(f"Creating virtual environment '{venv_path}'...")
        venv.create(venv_path, with_pip=True)

        pip_path = os.path.join(venv_path, "Scripts", "python")
        install_cmd = [pip_path, "-m", "pip", "install", "-r", requirements]

        if log_file:
            with open(log_file, "w") as f:
                subprocess.run(install_cmd, stdout=f, stderr=f)
        else:
            # Suppress output entirely
            subprocess.run(install_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("")
    else:
        print(f"")
