from flask import Flask, jsonify, request
from quantumfoam.free import QuantumFoamRNG_Free
from quantumfoam.pro import QuantumFoamRNG_Pro
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'service': 'Quantum Foam RNG API',
        'version': '1.0.0',
        'endpoints': {
            '/health': 'Health check',
            '/api/v1/generate': 'Generate entropy (POST)',
            '/api/v1/key': 'Generate crypto key (POST)'
        },
        'docs': 'https://github.com/shemshallah/quantum-foam-rng'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'quantum-foam-rng'})

@app.route('/api/v1/generate', methods=['POST'])
def generate_entropy():
    """
    Generate quantum entropy
    
    Body: {
        "bits": 256,
        "api_key": "optional_for_pro"
    }
    """
    try:
        data = request.get_json()
        n_bits = data.get('bits', 256)
        api_key = data.get('api_key')
        
        # Use Pro if API key provided, else Free
        if api_key:
            rng = QuantumFoamRNG_Pro(api_key=api_key)
        else:
            rng = QuantumFoamRNG_Free()
        
        result = rng.generate_entropy(n_bits=n_bits, verbose=False)
        
        return jsonify({
            'success': True,
            'entropy': result['hex'],
            'foam_strength': result['foam_strength'],
            'metadata': result['metadata']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/key', methods=['POST'])
def generate_key():
    """
    Generate crypto key
    
    Body: {
        "api_key": "optional_for_pro"
    }
    """
    try:
        data = request.get_json() or {}
        api_key = data.get('api_key')
        
        if api_key:
            rng = QuantumFoamRNG_Pro(api_key=api_key)
        else:
            rng = QuantumFoamRNG_Free()
        
        key = rng.generate_crypto_key(verbose=False)
        
        return jsonify({
            'success': True,
            'private_key': key['private_key'],
            'foam_strength': key['foam_strength'],
            'timestamp': key['timestamp']
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
