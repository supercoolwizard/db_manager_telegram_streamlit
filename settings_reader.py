def read_settings(file_path):
    settings = {}
    with open(file_path, 'r') as file:
        current_key = None
        for line in file:
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # Ignore comments and empty lines

            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Handle regular key-value pairs
                if key == 'MONGOSH_ALLOWED_COMMANDS':
                    # Start collecting lines for this key
                    current_key = key
                    settings[current_key] = value
                else:
                    settings[key] = value
            elif current_key:
                # Collecting multi-line commands for MONGOSH_ALLOWED_COMMANDS
                if line == ']':
                    settings[current_key] += line
                    current_key = None  # Done collecting
                else:
                    settings[current_key] += f" {line}"  # Append current line

    # Evaluate MONGOSH_ALLOWED_COMMANDS as Python code
    if 'MONGOSH_ALLOWED_COMMANDS' in settings:
        settings['MONGOSH_ALLOWED_COMMANDS'] = eval(settings['MONGOSH_ALLOWED_COMMANDS'])

    return settings
