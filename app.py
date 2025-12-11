"""
Quantum Foam RNG API
Deployed on Render - IonQ Quantum Simulator
Uses async job queue to handle long quantum processing times
"""

from flask import Flask, jsonify, request, send_from_directory
import numpy as np
import hashlib
from datetime import datetime
import warnings
import os
import uuid
import threading

warnings.filterwarnings('ignore')

app = Flask(__name__)

# Job storage (in production, use Redis or database)
jobs = {}
job_lock = threading.Lock()

# Import quantum libraries
try:
    from qbraid.runtime import QbraidProvider
    from qiskit import QuantumCircuit
    QUANTUM_AVAILABLE = True
    print("✓ Quantum libraries loaded successfully")
except Exception as e:
    print(f"⚠️  Quantum libraries not available: {e}")
    QUANTUM_AVAILABLE = False


class QuantumFoamRNG_Free:
    """Community Edition - Quantum Foam Random Number Generator"""
    
    VERSION = "1.0.0-free"
    
    def __init__(self, device_id="ionq_simulator"):
        """Initialize Quantum Foam RNG"""
        print(f"🌊 Initializing Quantum Foam RNG v{self.VERSION}")
        
        if not QUANTUM_AVAILABLE:
            raise Exception("Quantum libraries not available")
        
        self.provider = QbraidProvider()
        self.device = self.provider.get_device(device_id)
        self.bases = ['ZZ', 'XX', 'YY', 'ZX', 'XZ', 'ZY', 'YZ', 'XY', 'YX']
        
        print(f"✓ Device: {self.device.id}")
        print(f"✓ Bases: {len(self.bases)}")
        print(f"✓ Status: {self.device.status()}")
    
    def generate_crypto_key(self, verbose=True):
        """Generate 256-bit crypto key using quantum hardware with randomness extraction"""
        
        if verbose:
            print(f"\n🔐 Generating crypto key...")
        
        start_time = datetime.now()
        n_bits = 256
        theta = 45
        
        # Generate MORE raw bits than needed for randomness extraction
        raw_bits_needed = n_bits * 3  # 3x oversampling for quality
        
        if verbose:
            print(f"   Target: {n_bits} bits")
            print(f"   Raw bits: {raw_bits_needed} (with extraction)")
            print(f"   Angle: θ={theta}°")
        
        # Increase shots per basis for better statistics
        shots_per_basis = max(50, int(np.ceil(raw_bits_needed / (2 * len(self.bases)))))
        
        if verbose:
            print(f"   Shots per basis: {shots_per_basis}")
            print(f"   Submitting {len(self.bases)} circuits...")
        
        # Submit all quantum jobs
        jobs = []
        for basis in self.bases:
            circuit = self._create_bell_circuit(theta, basis)
            job = self.device.run(circuit, shots=shots_per_basis)
            jobs.append((basis, job))
        
        if verbose:
            print(f"✓ Circuits submitted")
            print(f"   Collecting results...")
        
        # Collect results with shuffling to break correlations
        all_bits = []
        expectation_values = []
        
        for i, (basis, job) in enumerate(jobs):
            result = job.result()
            
            try:
                counts = result.data.get_counts()
            except:
                counts = result.get_counts()
            
            # Extract bits with better randomization
            basis_bits = []
            for outcome, count in counts.items():
                if isinstance(outcome, int):
                    outcome_str = format(outcome, '02b')
                else:
                    outcome_str = outcome
                
                # Take both qubits
                bits = [int(b) for b in outcome_str[-2:]]
                for _ in range(count):
                    basis_bits.extend(bits)
            
            # Shuffle bits from this basis to break patterns
            np.random.shuffle(basis_bits)
            all_bits.extend(basis_bits)
            
            # Calculate expectation value
            total = sum(counts.values())
            n_00 = counts.get('00', 0) + counts.get('0', 0) + counts.get(0, 0)
            n_11 = counts.get('11', 0) + counts.get('3', 0) + counts.get(3, 0)
            n_01 = counts.get('01', 0) + counts.get('1', 0) + counts.get(1, 0)
            n_10 = counts.get('10', 0) + counts.get('2', 0) + counts.get(2, 0)
            
            exp_val = (n_00 + n_11 - n_01 - n_10) / total
            expectation_values.append(exp_val)
            
            if verbose and (i + 1) % 3 == 0:
                print(f"   Progress: {i + 1}/{len(jobs)}")
        
        # Shuffle all bits to break any remaining correlations
        np.random.shuffle(all_bits)
        
        if verbose:
            print(f"✓ Collected {len(all_bits)} raw bits")
            print(f"   Applying randomness extraction...")
        
        # Apply von Neumann randomness extraction (removes bias)
        extracted_bits = self._von_neumann_extract(all_bits)
        
        if verbose:
            print(f"   Extracted {len(extracted_bits)} unbiased bits")
        
        # Apply Toeplitz hashing for final conditioning
        final_bits = self._toeplitz_hash(extracted_bits, n_bits)
        
        bit_string = ''.join(map(str, final_bits))
        hex_string = hex(int(bit_string, 2))[2:].zfill(n_bits // 4)
        foam_strength = np.std(expectation_values)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if verbose:
            print(f"✓ Complete!")
            print(f"   Foam strength: σ={foam_strength:.4f}")
            print(f"   Time: {duration:.1f}s")
            print(f"   Rate: {n_bits/duration:.1f} bits/sec")
        
        return {
            'private_key': hex_string,
            'foam_strength': foam_strength,
            'timestamp': end_time.isoformat(),
            'edition': 'free',
            'mode': 'quantum',
            'device': self.device.id,
            'generation_time_sec': duration,
            'bits_per_second': n_bits / duration,
            'n_bases': len(self.bases),
            'total_shots': shots_per_basis * len(self.bases),
            'raw_bits_collected': len(all_bits),
            'extraction_ratio': len(extracted_bits) / len(all_bits),
            'post_processing': 'von_neumann + toeplitz_hash'
        }
    
    def _von_neumann_extract(self, bits):
        """Von Neumann randomness extraction - removes bias"""
        extracted = []
        i = 0
        while i < len(bits) - 1:
            if bits[i] == 0 and bits[i+1] == 1:
                extracted.append(0)
                i += 2
            elif bits[i] == 1 and bits[i+1] == 0:
                extracted.append(1)
                i += 2
            else:
                i += 2  # Skip 00 and 11
        return extracted
    
    def _toeplitz_hash(self, bits, output_length):
        """Toeplitz hashing for final randomness extraction"""
        if len(bits) < output_length:
            # If not enough bits after extraction, use SHA-256 as fallback
            bits_str = ''.join(map(str, bits))
            hash_val = hashlib.sha256(bits_str.encode()).digest()
            result_bits = []
            for byte in hash_val:
                result_bits.extend([int(b) for b in format(byte, '08b')])
            return result_bits[:output_length]
        
        # Simple Toeplitz matrix multiplication (XOR of selected bits)
        np.random.seed(42)  # Deterministic seed for reproducibility
        output = []
        
        for i in range(output_length):
            # Select pseudo-random subset of input bits
            indices = np.random.choice(len(bits), size=min(32, len(bits)), replace=False)
            bit = sum([bits[idx] for idx in indices]) % 2
            output.append(bit)
        
        return output
    
    def _create_bell_circuit(self, theta_deg, basis):
        """Create Bell state circuit"""
        qc = QuantumCircuit(2, 2)
        
        theta_rad = np.radians(theta_deg)
        qc.ry(theta_rad, 0)
        qc.cx(0, 1)
        
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


def generate_key_async(job_id):
    """Background task to generate quantum key"""
    try:
        with job_lock:
            jobs[job_id]['status'] = 'processing'
            jobs[job_id]['updated_at'] = datetime.now().isoformat()
        
        print(f"\n{'='*60}")
        print(f"Job {job_id}: Starting quantum generation")
        print(f"{'='*60}")
        
        rng = QuantumFoamRNG_Free(device_id="ionq_simulator")
        result = rng.generate_crypto_key(verbose=True)
        
        with job_lock:
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['result'] = result
            jobs[job_id]['updated_at'] = datetime.now().isoformat()
        
        print(f"{'='*60}")
        print(f"Job {job_id}: Completed successfully")
        print(f"{'='*60}\n")
    
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"Job {job_id}: ERROR")
        print(f"{'='*60}")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        with job_lock:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = str(e)
            jobs[job_id]['traceback'] = traceback.format_exc()
            jobs[job_id]['updated_at'] = datetime.now().isoformat()


@app.route('/')
def home():
    """Serve landing page"""
    if os.path.exists('static/index.html'):
        return send_from_directory('static', 'index.html')
    
    return jsonify({
        'service': 'Quantum Foam RNG API',
        'version': '1.0.0',
        'status': 'online',
        'quantum_available': QUANTUM_AVAILABLE,
        'device': 'ionq_simulator',
        'mode': 'async',
        'note': 'Quantum processing takes 2-3 minutes. Use async API.',
        'endpoints': {
            'POST /api/v1/key': 'Start key generation job',
            'GET /api/v1/job/<job_id>': 'Check job status',
            'GET /health': 'Health check'
        }
    })


@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'quantum-foam-rng',
        'version': '1.0.0',
        'quantum_available': QUANTUM_AVAILABLE,
        'device': 'ionq_simulator',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/v1/info')
def info():
    """API info"""
    return jsonify({
        'service': 'Quantum Foam RNG',
        'version': '1.0.0',
        'edition': 'community',
        'quantum_available': QUANTUM_AVAILABLE,
        'device': 'ionq_simulator',
        'processing_time': '2-3 minutes',
        'note': 'Use async API - POST to create job, then poll for results',
        'github': 'https://github.com/shemshallah/quantum-foam-rng'
    })


@app.route('/api/v1/key', methods=['POST', 'OPTIONS'])
def create_key_job():
    """Create async quantum key generation job"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    try:
        if not QUANTUM_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Quantum libraries not available on this server'
            }), 503
        
        # Create job
        job_id = str(uuid.uuid4())
        
        with job_lock:
            jobs[job_id] = {
                'id': job_id,
                'status': 'pending',
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        
        print(f"\n→ New job created: {job_id}")
        
        # Start background thread
        thread = threading.Thread(target=generate_key_async, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        response = jsonify({
            'success': True,
            'job_id': job_id,
            'status': 'pending',
            'message': 'Quantum key generation started. This will take 2-3 minutes.',
            'poll_url': f'/api/v1/job/{job_id}',
            'estimated_time_sec': 180,
            'created_at': jobs[job_id]['created_at']
        })
        
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    
    except Exception as e:
        print(f"Error creating job: {e}")
        import traceback
        traceback.print_exc()
        
        error_response = jsonify({
            'success': False,
            'error': str(e)
        })
        error_response.headers['Access-Control-Allow-Origin'] = '*'
        return error_response, 500


@app.route('/api/v1/job/<job_id>', methods=['GET'])
def check_job_status(job_id):
    """Check status of quantum key generation job"""
    
    with job_lock:
        if job_id not in jobs:
            response = jsonify({
                'success': False,
                'error': 'Job not found'
            })
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 404
        
        job = jobs[job_id].copy()
    
    response_data = {
        'success': True,
        'job_id': job['id'],
        'status': job['status'],
        'created_at': job['created_at'],
        'updated_at': job['updated_at']
    }
    
    if job['status'] == 'completed':
        response_data['result'] = job['result']
    elif job['status'] == 'failed':
        response_data['error'] = job.get('error', 'Unknown error')
        response_data['traceback'] = job.get('traceback', '')
    elif job['status'] == 'processing':
        response_data['message'] = 'Quantum circuits running on IonQ simulator...'
    elif job['status'] == 'pending':
        response_data['message'] = 'Job queued, waiting to start...'
    
    response = jsonify(response_data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    
    return response


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            'GET /',
            'GET /health',
            'GET /api/v1/info',
            'POST /api/v1/key',
            'GET /api/v1/job/<job_id>'
        ]
    }), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    import traceback
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': str(e)
    }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"\n{'='*80}")
    print(f"🌊 Quantum Foam RNG API Server 🌊")
    print(f"{'='*80}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"Device: ionq_simulator")
    print(f"Mode: Async (background processing)")
    print(f"Quantum Available: {QUANTUM_AVAILABLE}")
    print(f"\n💡 API Design:")
    print(f"   1. POST /api/v1/key → Get job_id")
    print(f"   2. Poll GET /api/v1/job/<job_id> → Check status")
    print(f"   3. When status='completed' → Get result")
    print(f"\n⏱️  Processing time: 2-3 minutes per key")
    print(f"{'='*80}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
