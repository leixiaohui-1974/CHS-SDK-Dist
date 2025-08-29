import os
import json
from flask import Flask, jsonify, abort
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# The root directory where all example subdirectories are stored.
EXAMPLES_ROOT_DIR = 'examples'

@app.route('/api/examples', methods=['GET'])
def get_examples():
    """
    Scans the EXAMPLES_ROOT_DIR for subdirectories, each representing an example.
    It reads the metadata from the 'config.json' inside each subdirectory.
    """
    examples = []
    if not os.path.exists(EXAMPLES_ROOT_DIR):
        print(f"Warning: Examples root directory '{EXAMPLES_ROOT_DIR}' not found.")
        return jsonify([])

    for example_id in os.listdir(EXAMPLES_ROOT_DIR):
        example_dir = os.path.join(EXAMPLES_ROOT_DIR, example_id)
        if os.path.isdir(example_dir):
            config_path = os.path.join(example_dir, 'config.json')
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        data = json.load(f)
                        metadata = data.get('metadata', {})
                        examples.append({
                            'id': example_id,
                            'name': metadata.get('name', 'Unnamed Example'),
                            'description': metadata.get('description', '')
                        })
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error reading or parsing config.json in {example_id}: {e}")
                    continue
    return jsonify(examples)

@app.route('/api/examples/<string:example_id>', methods=['GET'])
def get_example_details(example_id):
    """
    Returns the full JSON configuration for a given example id.
    The example_id corresponds to the subdirectory name.
    """
    config_path = os.path.join(EXAMPLES_ROOT_DIR, example_id, 'config.json')

    if not os.path.exists(config_path):
        abort(404, description=f"Config file for example '{example_id}' not found.")

    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
            return jsonify(data)
    except (IOError, json.JSONDecodeError) as e:
        abort(500, description=f"Could not read or parse config file for example '{example_id}'.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
