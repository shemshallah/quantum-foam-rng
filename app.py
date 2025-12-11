"""
Quantum Foam RNG API
Deployed on Render
"""

from flask import Flask, jsonify, request, send_from_directory
import numpy as np
from qbraid.runtime import QbraidProvider
from qiskit import QuantumCircuit
import hashlib
from datetime import datetime
import warnings
import os

warnings.filterwarnings('ignore')

app = Flask(__name__)

# ===============================================================================
# QUANTUM FOAM RNG - FREE VERSION (EMBEDDED)
# ===============================================================================

class QuantumFoamRNG_Free:
    """
    Community Edition - Quantum Foam Random Number Generator
    """
    
    VERSION = "1.0.0-free"
    
    def __init__(self, device_id="ionq_simulator"):
        """Initialize Quantum Foam RNG"""
        print(f"🌊 Quantum Foam RNG - Community Edition v{self.VERSION}")
        
        self.provider = QbraidProvider()
        self.device = self.provider.get_device(device_id)
        
        # Basic basis set
        self.bases = ['ZZ', 'XX', 'YY', 'ZX', 'XZ', 'ZY', 'YZ', 'XY', 'YX']
        
        print(f"✓ Device: {self.device.id}")
        print(f"✓ Bases: {len(self.bases)}")
        print(f"✓ Status: {self.device.status()}")
    
    def generate_entropy(self, n_bits=256, theta=45, verbose=True):
        """Generate quantum random bits"""
        
        if verbose:
            print(f"\n🎲 Generating {n_bits} bits at θ={theta}°")
        
        start_time = datetime.now()
        
        # Calculate shots
        shots_per_basis = int(np.ceil(n_bits / (2 * len(self.bases))))
        
        if verbose:
            print(f"   Shots per basis: {shots_per_basis}")
            print(f"   Submitting {len(self.bases)} circuits...")
        
        # Submit jobs
        jobs = []
        for basis in self.bases:
            circuit = self._create_bell_circuit(theta, basis)
            job = self.device.run(circuit, shots=shots_per_basis)
            jobs.append((basis, job))
        
        if verbose:
            print(f"   Collecting results...")
        
        # Collect results
        all_bits = []
        expectation_values = []
        
        for i, (basis, job) in enumerate(jobs):
            result = job.result()
            
            try:
                counts = result.data.get_counts()
            except:
                counts = result.get_counts()
            
            # Extract bits
            for outcome, count in counts.items():
                if isinstance(outcome, int):
                    outcome_str = format(outcome, '02b')
                else:
                    outcome_str = outcome
                
                bits = [int(b) for b in outcome_str[-2:]]
                all_bits.extend(bits * count)
            
            # Expectation value
            total = sum(counts.values())
            n_00 = counts.get('00', 0) + counts.get('0', 0) + counts.get(0, 0)
            n_11 = counts.get('11', 0) + counts.get('3', 0) + counts.get(3, 0)
            n_01 = counts.get('01', 0) + counts.get('1', 0) + counts.get(1, 0)
            n_10 = counts.get('10', 0) + counts.get('2', 0) + counts.get(2, 0)
            
            exp_val = (n_00 + n_11 - n_01 - n_10) / total
            expectation_values.append(exp_val)
            
            if verbose and (i + 1) % 3 == 0:
                print(f"   Progress: {i + 1}/{len(jobs)}")
        
        # Truncate to requested length
        entropy_bits = all_bits[:n_bits]
        bit_string = ''.join(map(str, entropy_bits))
        hex_string = hex(int(bit_string, 2))[2:].zfill(n_bits // 4)
        
        # Foam strength
        foam_strength = np.std(expectation_values)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if verbose:
            print(f"✓ Complete!")
            print(f"   Foam strength: σ={foam_strength:.4f}")
            print(f"   Time: {duration:.1f}s")
        
        metadata = {
            'version': self.VERSION,
            'edition': 'free',
            'device': self.device.id,
            'theta_deg': theta,
            'n_bases': len(self.bases),
            'shots_per_basis': shots_per_basis,
            'total_shots': shots_per_basis * len(self.bases),
            'generation_time_sec': duration,
            'bits_per_second': len(entropy_bits) / duration,
            'timestamp': end_time.isoformat()
        }
        
        return {
            'bits': bit_string,
            'hex': hex_string,
            'foam_strength': foam_strength,
            'metadata': metadata
        }
    
    def generate_crypto_key(self, verbose=True):
        """Generate 256-bit crypto key"""
        
        if verbose:
            print(f"\n🔐 Generating crypto key...")
        
        result = self.generate_entropy(n_bits=256, verbose=verbose)
        
        return {
            'private_key': result['hex'],
            'foam_strength': result['foam_strength'],
            'timestamp': result['metadata']['timestamp'],
            'edition': 'free'
        }
    
    def _create_bell_circuit(self, theta_deg, basis):
        """Create Bell state circuit"""
        qc = QuantumCircuit(2, 2)
        
        # Bell state
        theta_rad = np.radians(theta_deg)
        qc.ry(theta_rad, 0)
        qc.cx(0, 1)
        
        # Basis rotations
        if basis[0] == 'X':
            qc.ry(-np.pi/2, 0)
        elif basis[0] == 'Y':
            qc.rx(np.pi/2, 0)
        
        if basis[1] == 'X':
            qc.ry(-np.pi/2, 1)
        elif basis[1] == 'Y':
            qc.rx(np.pi/2, 1)
        
        qc.measure([0, 1], [0, 1])
        
        return qc


# ===============================================================================
# FLASK API ROUTES
# ===============================================================================

@app.route('/')
def home():
    """Serve landing page or API info"""
    # Try to serve static file
    if os.path.exists('static/index.html'):
        return send_from_directory('static', 'index.html')
    
    # Fallback JSON response
    return jsonify({
        'service': 'Quantum Foam RNG API',
        'version': '1.0.0',
        'status': 'online',
        'endpoints': {
            'GET /': 'This page',
            'GET /health': 'Health check',
            'GET /api/v1/info': 'API information',
            'POST /api/v1/generate': 'Generate entropy',
            'POST /api/v1/key': 'Generate crypto key'
        },
        'usage': {
            'generate_key': 'POST /api/v1/key (no body required)',
            'generate_entropy': 'POST /api/v1/generate with {"bits": 256, "theta": 45}'
        },
        'github': 'https://github.com/shemshallah/quantum-foam-rng',
        'contact': 'shemshallah@gmail.com'
    })

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'quantum-foam-rng',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/v1/info')
def info():
    """API info"""
    return jsonify({
        'service': 'Quantum Foam RNG',
        'version': '1.0.0',
        'edition': 'community',
        'features': {
            'free': {
                'bases': 9,
                'foam_coupling': '~0.15',
                'speed': '~100 bits/min',
                'support': 'community'
            },
            'pro': {
                'bases': 75,
                'foam_coupling': '>0.5',
                'speed': '~1000 bits/min',
                'support': 'priority',
                'contact': 'shemshallah@gmail.com'
            }
        },
        'github': 'https://github.com/shemshallah/quantum-foam-rng'
    })

@app.route('/api/v1/generate', methods=['GET', 'POST'])
def generate_entropy():
    """
    Generate quantum entropy
    
    POST with JSON body:
    {
        "bits": 256,    // optional, default 256
        "theta": 45     // optional, default 45
    }
    
    OR GET with query params:
    /api/v1/generate?bits=256&theta=45
    """
    try:
        # Handle both GET and POST
        if request.method == 'POST':
            # Try to get JSON, but don't fail if empty
            try:
                data = request.get_json(force=True, silent=True) or {}
            except:
                data = {}
        else:  # GET
            data = request.args.to_dict()
        
        # Parse parameters with defaults
        try:
            n_bits = int(data.get('bits', 256))
        except (ValueError, TypeError):
            n_bits = 256
        
        try:
            theta = float(data.get('theta', 45))
        except (ValueError, TypeError):
            theta = 45
        
        # Validate
        if n_bits < 1 or n_bits > 2048:
            return jsonify({
                'success': False,
                'error': 'bits must be between 1 and 2048'
            }), 400
        
        if theta < 0 or theta > 90:
            return jsonify({
                'success': False,
                'error': 'theta must be between 0 and 90'
            }), 400
        
        # Generate
        print(f"API Request: Generate {n_bits} bits at θ={theta}°")
        rng = QuantumFoamRNG_Free()
        result = rng.generate_entropy(n_bits=n_bits, theta=theta, verbose=True)
        
        return jsonify({
            'success': True,
            'entropy': result['hex'],
            'foam_strength': result['foam_strength'],
            'metadata': result['metadata']
        })
    
    except Exception as e:
        print(f"Error in generate_entropy: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/key', methods=['GET', 'POST'])
def generate_key():
    """
    Generate crypto key
    
    No parameters required - always generates 256-bit key
    Works with GET or POST
    """
    try:
        print(f"API Request: Generate crypto key")
        
        rng = QuantumFoamRNG_Free()
        key = rng.generate_crypto_key(verbose=True)
        
        return jsonify({
            'success': True,
            'private_key': key['private_key'],
            'foam_strength': key['foam_strength'],
            'timestamp': key['timestamp'],
            'edition': key['edition']
        })
    
    except Exception as e:
        print(f"Error in generate_key: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(400)
def bad_request(e):
    """Handle 400 errors"""
    return jsonify({
        'error': 'Bad request',
        'message': 'The request was malformed or missing required data',
        'help': 'For /api/v1/key, no body required. For /api/v1/generate, send {"bits": 256, "theta": 45} or use GET with query params'
    }), 400

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            'GET /',
            'GET /health',
            'GET /api/v1/info',
            'POST /api/v1/generate',
            'POST /api/v1/key'
        ]
    }), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error',
        'message': str(e)
    }), 500


# ===============================================================================
# MAIN
# ===============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"\n{'='*80}")
    print(f"🌊 Quantum Foam RNG API Server 🌊")
    print(f"{'='*80}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"{'='*80}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)        # Basic basis set
        self.bases = ['ZZ', 'XX', 'YY', 'ZX', 'XZ', 'ZY', 'YZ', 'XY', 'YX']
        
        print(f"✓ Device: {self.device.id}")
        print(f"✓ Bases: {len(self.bases)}")
        print(f"✓ Status: {self.device.status()}")
    
    def generate_entropy(self, n_bits=256, theta=45, verbose=True):
        """Generate quantum random bits"""
        
        if verbose:
            print(f"\n🎲 Generating {n_bits} bits at θ={theta}°")
        
        start_time = datetime.now()
        
        # Calculate shots
        shots_per_basis = int(np.ceil(n_bits / (2 * len(self.bases))))
        
        if verbose:
            print(f"   Shots per basis: {shots_per_basis}")
            print(f"   Submitting {len(self.bases)} circuits...")
        
        # Submit jobs
        jobs = []
        for basis in self.bases:
            circuit = self._create_bell_circuit(theta, basis)
            job = self.device.run(circuit, shots=shots_per_basis)
            jobs.append((basis, job))
        
        if verbose:
            print(f"   Collecting results...")
        
        # Collect results
        all_bits = []
        expectation_values = []
        
        for i, (basis, job) in enumerate(jobs):
            result = job.result()
            
            try:
                counts = result.data.get_counts()
            except:
                counts = result.get_counts()
            
            # Extract bits
            for outcome, count in counts.items():
                if isinstance(outcome, int):
                    outcome_str = format(outcome, '02b')
                else:
                    outcome_str = outcome
                
                bits = [int(b) for b in outcome_str[-2:]]
                all_bits.extend(bits * count)
            
            # Expectation value
            total = sum(counts.values())
            n_00 = counts.get('00', 0) + counts.get('0', 0) + counts.get(0, 0)
            n_11 = counts.get('11', 0) + counts.get('3', 0) + counts.get(3, 0)
            n_01 = counts.get('01', 0) + counts.get('1', 0) + counts.get(1, 0)
            n_10 = counts.get('10', 0) + counts.get('2', 0) + counts.get(2, 0)
            
            exp_val = (n_00 + n_11 - n_01 - n_10) / total
            expectation_values.append(exp_val)
            
            if verbose and (i + 1) % 3 == 0:
                print(f"   Progress: {i + 1}/{len(jobs)}")
        
        # Truncate to requested length
        entropy_bits = all_bits[:n_bits]
        bit_string = ''.join(map(str, entropy_bits))
        hex_string = hex(int(bit_string, 2))[2:].zfill(n_bits // 4)
        
        # Foam strength
        foam_strength = np.std(expectation_values)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if verbose:
            print(f"✓ Complete!")
            print(f"   Foam strength: σ={foam_strength:.4f}")
            print(f"   Time: {duration:.1f}s")
        
        metadata = {
            'version': self.VERSION,
            'edition': 'free',
            'device': self.device.id,
            'theta_deg': theta,
            'n_bases': len(self.bases),
            'shots_per_basis': shots_per_basis,
            'total_shots': shots_per_basis * len(self.bases),
            'generation_time_sec': duration,
            'bits_per_second': len(entropy_bits) / duration,
            'timestamp': end_time.isoformat()
        }
        
        return {
            'bits': bit_string,
            'hex': hex_string,
            'foam_strength': foam_strength,
            'metadata': metadata
        }
    
    def generate_crypto_key(self, verbose=True):
        """Generate 256-bit crypto key"""
        
        if verbose:
            print(f"\n🔐 Generating crypto key...")
        
        result = self.generate_entropy(n_bits=256, verbose=verbose)
        
        return {
            'private_key': result['hex'],
            'foam_strength': result['foam_strength'],
            'timestamp': result['metadata']['timestamp'],
            'edition': 'free'
        }
    
    def _create_bell_circuit(self, theta_deg, basis):
        """Create Bell state circuit"""
        qc = QuantumCircuit(2, 2)
        
        # Bell state
        theta_rad = np.radians(theta_deg)
        qc.ry(theta_rad, 0)
        qc.cx(0, 1)
        
        # Basis rotations
        if basis[0] == 'X':
            qc.ry(-np.pi/2, 0)
        elif basis[0] == 'Y':
            qc.rx(np.pi/2, 0)
        
        if basis[1] == 'X':
            qc.ry(-np.pi/2, 1)
        elif basis[1] == 'Y':
            qc.rx(np.pi/2, 1)
        
        qc.measure([0, 1], [0, 1])
        
        return qc


# ===============================================================================
# FLASK API ROUTES
# ===============================================================================

@app.route('/')
def home():
    """Serve landing page or API info"""
    # Try to serve static file
    if os.path.exists('static/index.html'):
        return send_from_directory('static', 'index.html')
    
    # Fallback JSON response
    return jsonify({
        'service': 'Quantum Foam RNG API',
        'version': '1.0.0',
        'status': 'online',
        'endpoints': {
            'GET /': 'This page',
            'GET /health': 'Health check',
            'GET /api/v1/info': 'API information',
            'POST /api/v1/generate': 'Generate entropy',
            'POST /api/v1/key': 'Generate crypto key'
        },
        'usage': {
            'generate_key': 'POST /api/v1/key (no body required)',
            'generate_entropy': 'POST /api/v1/generate with {"bits": 256, "theta": 45}'
        },
        'github': 'https://github.com/shemshallah/quantum-foam-rng',
        'contact': 'shemshallah@gmail.com'
    })

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'quantum-foam-rng',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/v1/info')
def info():
    """API info"""
    return jsonify({
        'service': 'Quantum Foam RNG',
        'version': '1.0.0',
        'edition': 'community',
        'features': {
            'free': {
                'bases': 9,
                'foam_coupling': '~0.15',
                'speed': '~100 bits/min',
                'support': 'community'
            },
            'pro': {
                'bases': 75,
                'foam_coupling': '>0.5',
                'speed': '~1000 bits/min',
                'support': 'priority',
                'contact': 'shemshallah@gmail.com'
            }
        },
        'github': 'https://github.com/shemshallah/quantum-foam-rng'
    })

@app.route('/api/v1/generate', methods=['GET', 'POST'])
def generate_entropy():
    """
    Generate quantum entropy
    
    POST with JSON body:
    {
        "bits": 256,    // optional, default 256
        "theta": 45     // optional, default 45
    }
    
    OR GET with query params:
    /api/v1/generate?bits=256&theta=45
    """
    try:
        # Handle both GET and POST
        if request.method == 'POST':
            # Try to get JSON, but don't fail if empty
            try:
                data = request.get_json(force=True, silent=True) or {}
            except:
                data = {}
        else:  # GET
            data = request.args.to_dict()
        
        # Parse parameters with defaults
        try:
            n_bits = int(data.get('bits', 256))
        except (ValueError, TypeError):
            n_bits = 256
        
        try:
            theta = float(data.get('theta', 45))
        except (ValueError, TypeError):
            theta = 45
        
        # Validate
        if n_bits < 1 or n_bits > 2048:
            return jsonify({
                'success': False,
                'error': 'bits must be between 1 and 2048'
            }), 400
        
        if theta < 0 or theta > 90:
            return jsonify({
                'success': False,
                'error': 'theta must be between 0 and 90'
            }), 400
        
        # Generate
        print(f"API Request: Generate {n_bits} bits at θ={theta}°")
        rng = QuantumFoamRNG_Free()
        result = rng.generate_entropy(n_bits=n_bits, theta=theta, verbose=True)
        
        return jsonify({
            'success': True,
            'entropy': result['hex'],
            'foam_strength': result['foam_strength'],
            'metadata': result['metadata']
        })
    
    except Exception as e:
        print(f"Error in generate_entropy: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/key', methods=['GET', 'POST'])
def generate_key():
    """
    Generate crypto key
    
    No parameters required - always generates 256-bit key
    Works with GET or POST
    """
    try:
        print(f"API Request: Generate crypto key")
        
        rng = QuantumFoamRNG_Free()
        key = rng.generate_crypto_key(verbose=True)
        
        return jsonify({
            'success': True,
            'private_key': key['private_key'],
            'foam_strength': key['foam_strength'],
            'timestamp': key['timestamp'],
            'edition': key['edition']
        })
    
    except Exception as e:
        print(f"Error in generate_key: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(400)
def bad_request(e):
    """Handle 400 errors"""
    return jsonify({
        'error': 'Bad request',
        'message': 'The request was malformed or missing required data',
        'help': 'For /api/v1/key, no body required. For /api/v1/generate, send {"bits": 256, "theta": 45} or use GET with query params'
    }), 400

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            'GET /',
            'GET /health',
            'GET /api/v1/info',
            'POST /api/v1/generate',
            'POST /api/v1/key'
        ]
    }), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error',
        'message': str(e)
    }), 500


# ===============================================================================
# MAIN
# ===============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"\n{'='*80}")
    print(f"🌊 Quantum Foam RNG API Server 🌊")
    print(f"{'='*80}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"{'='*80}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
