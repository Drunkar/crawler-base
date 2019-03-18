def get_executor_address(env_file):
    executor_address = None
    with open(env_file, "r") as f:
        for line in f:
            if line.startswith("EXECUTOR_ADDRESS"):
                index = line.find("=")
                if index > 0:
                    executor_address = line[index+1:].strip()
    return executor_address
