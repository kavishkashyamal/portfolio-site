import os
import uuid
import subprocess
from flask import Flask, render_template, request, jsonify
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Configuration
MAX_RUNTIME = 5  # seconds
WORKING_DIR = 'tmp_files'  # Changed from 'tmp' to avoid confusion

if not os.path.exists(WORKING_DIR):
    os.makedirs(WORKING_DIR)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute():
    data = request.get_json()
    code = data.get('code', '')
    
    if not code.strip():
        return jsonify({'success': False, 'error': 'No code provided'})
    
    # Generate a unique filename
    filename = os.path.join(WORKING_DIR, f"{uuid.uuid4().hex}.py")
    
    try:
        # Write code to file
        with open(filename, 'w') as f:
            f.write(code)
        
        # Execute the code - specify the full path
        process = subprocess.run(
            ['python', filename],
            capture_output=True,
            text=True,
            timeout=MAX_RUNTIME
        )
        
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)
        
        if process.returncode == 0:
            return jsonify({
                'success': True,
                'output': process.stdout,
                'html': highlight(code, PythonLexer(), HtmlFormatter())
            })
        else:
            return jsonify({
                'success': False,
                'error': process.stderr,
                'html': highlight(code, PythonLexer(), HtmlFormatter())
            })
            
    except subprocess.TimeoutExpired:
        if os.path.exists(filename):
            os.remove(filename)
        return jsonify({
            'success': False,
            'error': f'Execution timed out (max {MAX_RUNTIME} seconds)'
        })
    except Exception as e:
        if os.path.exists(filename):
            os.remove(filename)
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
