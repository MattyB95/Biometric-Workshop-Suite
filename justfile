# Keystroke Dynamics Demo — task runner
# Install just: https://github.com/casey/just

# List available commands
default:
    @just --list

# Install dependencies
install:
    uv sync

# Run the development server (localhost only)
run:
    uv run python app.py

# Run the server accessible to other devices on the network (workshop mode)
run-network:
    uv run flask --app app run --host 0.0.0.0 --port 5000

# Delete all enrolled profiles (fresh start for a new session)
reset:
    rm -f profiles.json
    @echo "All profiles deleted."

# Show currently enrolled students
profiles:
    @python3 -c "
import json, os
if not os.path.exists('profiles.json'):
    print('No profiles found.')
else:
    data = json.load(open('profiles.json'))
    if not data:
        print('No profiles enrolled.')
    else:
        print(f'{len(data)} enrolled student(s):')
        for name, p in data.items():
            print(f'  - {name} ({p[\"num_samples\"]} samples)')
"
