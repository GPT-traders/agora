import os
import sys
import subprocess

def check_python_path():
    print(f"Current Python path: {sys.executable}")
    try:
        python_version = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
        print(f"Python version: {python_version.stdout.strip()}")
    except Exception as e:
        print(f"Failed to execute Python: {e}")

def check_module_build():
    try:
        import pyagora_receive_callback
        print("PyAgora module is correctly imported.")
    except ImportError as e:
        print(f"Failed to import PyAgora module: {e}")

def check_environment_variables():
    required_vars = ["PATH", "LD_LIBRARY_PATH"]  # Add other necessary variables here
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"{var}: {value}")
        else:
            print(f"{var} is not set.")

def check_file_permissions_and_path():
    paths = [sys.executable]  # Add paths to other necessary binaries here
    for path in paths:
        if os.path.exists(path):
            print(f"{path} exists.")
            if os.access(path, os.X_OK):
                print(f"{path} is executable.")
            else:
                print(f"{path} is not executable. Check permissions.")
        else:
            print(f"{path} does not exist. Check the path.")

def check_dependencies():
    binaries = ["python"]  # Add names of binaries or libraries your application uses
    missing_binaries = []
    for binary in binaries:
        result = subprocess.run(["which", binary], capture_output=True, text=True)
        if result.returncode != 0:
            missing_binaries.append(binary)
        else:
            print(f"{binary} is available at {result.stdout.strip()}")

    if missing_binaries:
        print("Missing binaries: " + ", ".join(missing_binaries))
        print("You need to install or correctly link the following binaries: " + ", ".join(missing_binaries))

if __name__ == "__main__":
    print("Starting environment test...")
    check_python_path()
    check_module_build()
    check_environment_variables()
    check_file_permissions_and_path()
    check_dependencies()
    print("Environment test completed.")
