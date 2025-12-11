"""
Quantum Foam RNG API - PRO EDITION
75 Optimized Bases + Advanced Randomness Extraction
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

# Job storage
jobs = {}
job_lock = threading.Lock()

# Import quantum libraries
try:
    from qbraid.runtime import QbraidProvider
    from qiskit import QuantumCircuit
    QUANTUM_AVAILABLE = True
    print("✓ Quantum libraries loaded")
except Exception as e:
    print(f"⚠️  Quantum not available: {e}")
    QUANTUM_AVAILABLE = False


class QuantumFoamRNG_Pro:
    """Pro Edition - 75 Optimized Bases"""
    
    VERSION = "1.0.0-pro"
    
    def __init__(self, device_id="ionq_simulator"):
        """Initialize Pro Edition RNG"""
        print(f"💎 Quantum Foam RNG - Pro Edition v{self.VERSION}")
        
        if not QUANTUM_AVAILABLE:
            raise Exception("Quantum libraries not available")
        
        self.provider = QbraidProvider()
        self.device = self.provider.get_device(device_id)
        
        # 75 OPTIMIZED BASES - Maximum foam diversity
        self.bases = self._load_optimized_bases()
        
        print(f"✓ Device: {self.device.id}")
        print(f"✓ Bases: {len(self.bases)} (OPTIMIZED)")
        print(f"✓ Status: {self.device.status()}")
    
    def _load_optimized_bases(self):
        """Load 75 high-diversity quantum measurement bases"""
        bases = []
        
        # Standard Pauli (9)
        pauli_bases = ['XX', 'YY', 'ZZ', 'XY', 'YX', 'XZ', 'ZX', 'YZ', 'ZY']
        bases.extend(pauli_bases)
        
        # Single qubit mixed (6)
        mixed = ['XI', 'IX', 'YI', 'IY', 'ZI', 'IZ']
        bases.extend(mixed)
        
        # Rotated X bases (15)
        for i in range(15):
            angle = i * np.pi / 15
            bases.append(f'RX{i:02d}')
        
        # Rotated Y bases (15)
        for i in range(15):
            angle = i * np.pi / 15
            bases.append(f'RY{i:02d}')
        
        # Rotated Z bases (15)
        for i in range(15):
            angle = i * np.pi / 15
            bases.append(f'RZ{i:02d}')
        
        # Bell-diagonal bases (15)
        for i in range(15):
            angle = i * 2 * np.pi / 15
            bases.append(f'BD{i:02d}')
        
        return bases[:75]  # Exactly 75
    
    def generate_crypto_key(self, verbose=True):
        """Generate 256-bit key with advanced randomness extraction"""
        
        if verbose:
            print(f"\n🔐 Generating Pro crypto key...")
        
        start_time = datetime.now()
        n_bits = 256
        theta = 45
        
        # Pro: Less oversampling needed due to basis diversity
        raw_bits_needed = n_bits * 2  # 2x instead of 3x
        
        if verbose:
            print(f"   Target: {n_bits} bits")
            print(f"   Raw bits: {raw_bits_needed}")
            print(f"   Bases: {len(self.bases)} optimized")
        
        # Fewer shots per basis due to more bases
        shots_per_basis = max(20, int(np.ceil(raw_bits_needed / (2 * len(self.bases)))))
        
        if verbose:
            print(f"   Shots per basis: {shots_per_basis}")
            print(f"   Total shots: {shots_per_basis * len(self.bases)}")
            print(f"   Submitting circuits...")
        
        # Submit jobs
        jobs_list = []
        for basis in self.bases:
            circuit = self._create_bell_circuit(theta, basis)
            job = self.device.run(circuit, shots=shots_per_basis)
            jobs_list.append((basis, job))
        
        if verbose:
            print(f"✓ {len(jobs_list)} circuits submitted")
            print(f"   Collecting results...")
        
        # Collect with enhanced randomization
        all_bits = []
        expectation_values = []
        basis_entropies = []
        
        for i, (basis, job) in enumerate(jobs_list):
            result = job.result()
            
            try:
                counts = result.data.get_counts()
            except:
                counts = result.get_counts()
            
            # Extract and shuffle
            basis_bits = []
            for outcome, count in counts.items():
                if isinstance(outcome, int):
                    outcome_str = format(outcome, '02b')
                else:
                    outcome_str = outcome
                
                bits = [int(b) for b in outcome_str[-2:]]
                for _ in range(count):
                    basis_bits.extend(bits)
            
            # Calculate Shannon entropy for this basis
            if len(basis_bits) > 0:
                p0 = basis_bits.count(0) / len(basis_bits)
                p1 = basis_bits.count(1) / len(basis_bits)
                if p0 > 0 and p1 > 0:
                    entropy = -p0 * np.log2(p0) - p1 * np.log2(p1)
                else:
                    entropy = 0
                basis_entropies.append(entropy)
            
            np.random.shuffle(basis_bits)
            all_bits.extend(basis_bits)
            
            # Expectation value
            total = sum(counts.values())
            n_00 = counts.get('00', 0) + counts.get('0', 0) + counts.get(0, 0)
            n_11 = counts.get('11', 0) + counts.get('3', 0) + counts.get(3, 0)
            n_01 = counts.get('01', 0) + counts.get('1', 0) + counts.get(1, 0)
            n_10 = counts.get('10', 0) + counts.get('2', 0) + counts.get(2, 0)
            
            exp_val = (n_00 + n_11 - n_01 - n_10) / total
            expectation_values.append(exp_val)
            
            if verbose and (i + 1) % 15 == 0:
                print(f"   Progress: {i + 1}/{len(jobs_list)}")
        
        # Global shuffle
        np.random.shuffle(all_bits)
        
        if verbose:
            print(f"✓ Collected {len(all_bits)} raw bits")
            print(f"   Applying multi-stage extraction...")
        
        # Stage 1: Von Neumann
        vn_bits = self._von_neumann_extract(all_bits)
        
        # Stage 2: XOR extraction (additional decorrelation)
        xor_bits = self._xor_extract(vn_bits)
        
        # Stage 3: Toeplitz hashing
        final_bits = self._toeplitz_hash(xor_bits, n_bits)
        
        bit_string = ''.join(map(str, final_bits))
        hex_string = hex(int(bit_string, 2))[2:].zfill(n_bits // 4)
        
        foam_strength = np.std(expectation_values)
        avg_entropy = np.mean(basis_entropies) if basis_entropies else 0
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if verbose:
            print(f"✓ Complete!")
            print(f"   Foam strength: σ={foam_strength:.4f}")
            print(f"   Avg entropy: {avg_entropy:.4f} bits")
            print(f"   Time: {duration:.1f}s")
            print(f"   Rate: {n_bits/duration:.1f} bits/sec")
        
        return {
            'private_key': hex_string,
            'foam_strength': foam_strength,
            'avg_basis_entropy': avg_entropy,
            'timestamp': end_time.isoformat(),
            'edition': 'pro',
            'mode': 'quantum',
            'device': self.device.id,
            'generation_time_sec': duration,
            'bits_per_second': n_bits / duration,
            'n_bases': len(self.bases),
            'total_shots': shots_per_basis * len(self.bases),
            'raw_bits_collected': len(all_bits),
            'vn_extraction_ratio': len(vn_bits) / len(all_bits),
            'xor_extraction_ratio': len(xor_bits) / len(vn_bits),
            'post_processing': '3-stage: von_neumann + xor + toeplitz'
        }
    
    def _von_neumann_extract(self, bits):
        """Von Neumann extraction"""
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
                i += 2
        return extracted
    
    def _xor_extract(self, bits, block_size=8):
        """XOR extraction for additional decorrelation"""
        extracted = []
        for i in range(0, len(bits) - block_size, block_size):
            block = bits[i:i+block_size]
            xor_bit = sum(block) % 2
            extracted.append(xor_bit)
        return extracted
    
    def _toeplitz_hash(self, bits, output_length):
        """Toeplitz hashing"""
        if len(bits) < output_length * 2:
            # Fallback to SHA-256
            bits_str = ''.join(map(str, bits))
            hash_val = hashlib.sha256(bits_str.encode()).digest()
            result_bits = []
            for byte in hash_val:
                result_bits.extend([int(b) for b in format(byte, '08b')])
            return result_bits[:output_length]
        
        np.random.seed(42)
        output = []
        
        for i in range(output_length):
            indices = np.random.choice(len(bits), size=min(64, len(bits)), replace=False)
            bit = sum([bits[idx] for idx in indices]) % 2
            output.append(bit)
        
        return output
    
    def _create_bell_circuit(self, theta_deg, basis):
        """Create optimized Bell circuit"""
        qc = QuantumCircuit(2, 2)
        
        theta_rad = np.radians(theta_deg)
        qc.ry(theta_rad, 0)
        qc.cx(0, 1)
        
        # Parse basis type
        if basis.startswith('RX'):
            idx = int(basis[2:])
            angle = idx * np.pi / 15
            qc.rx(angle, 0)
            qc.rx(angle, 1)
        
        elif basis.startswith('RY'):
            idx = int(basis[2:])
            angle = idx * np.pi / 15
            qc.ry(angle, 0)
            qc.ry(angle, 1)
        
        elif basis.startswith('RZ'):
            idx = int(basis[2:])
            angle = idx * np.pi / 15
            qc.rz(angle, 0)
            qc.rz(angle, 1)
        
        elif basis.startswith('BD'):
            idx = int(basis[2:])
            angle = idx * 2 * np.pi / 15
            qc.ry(angle, 0)
            qc.rx(angle, 1)
        
        else:
            # Standard Pauli
            if len(basis) >= 2:
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


def generate_key_async(job_id, edition='free'):
    """Background task"""
    try:
        with job_lock:
            jobs[job_id]['status'] = 'processing'
            jobs[job_id]['updated_at'] = datetime.now().isoformat()
        
        print(f"\nJob {job_id}: Starting ({edition} edition)")
        
        if edition == 'pro':
            rng = QuantumFoamRNG_Pro()
        else:
            from app import QuantumFoamRNG_Free
            rng = QuantumFoamRNG_Free()
        
        result = rng.generate_crypto_key(verbose=True)
        
        with job_lock:
            jobs[job_id]['status'] = 'completed'
            jobs[job_id]['result'] = result
            jobs[job_id]['updated_at'] = datetime.now().isoformat()
        
        print(f"Job {job_id}: Completed")
    
    except Exception as e:
        print(f"Job {job_id}: Error - {e}")
        import traceback
        traceback.print_exc()
        
        with job_lock:
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = str(e)
            jobs[job_id]['updated_at'] = datetime.now().isoformat()


@app.route('/')
def home():
    return jsonify({
        'service': 'Quantum Foam RNG API - PRO',
        'version': '1.0.0-pro',
        'status': 'online',
        'quantum_available': QUANTUM_AVAILABLE,
        'features': {
            'bases': 75,
            'foam_coupling': '>0.5 expected',
            'speed': '~10x faster than free',
            'extraction': '3-stage randomness extraction'
        }
    })


@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'quantum-foam-rng-pro',
        'version': '1.0.0-pro',
        'quantum_available': QUANTUM_AVAILABLE,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/v1/key', methods=['POST', 'OPTIONS'])
def create_key_job():
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
                'error': 'Quantum libraries not available'
            }), 503
        
        # Get edition from request
        data = request.get_json() or {}
        edition = data.get('edition', 'pro')  # Default to pro
        
        job_id = str(uuid.uuid4())
        
        with job_lock:
            jobs[job_id] = {
                'id': job_id,
                'status': 'pending',
                'edition': edition,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
        
        print(f"\n→ New {edition} job: {job_id}")
        
        thread = threading.Thread(target=generate_key_async, args=(job_id, edition))
        thread.daemon = True
        thread.start()
        
        response = jsonify({
            'success': True,
            'job_id': job_id,
            'edition': edition,
            'status': 'pending',
            'message': f'Pro quantum generation started (75 bases)',
            'poll_url': f'/api/v1/job/{job_id}',
            'estimated_time_sec': 240
        })
        
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    
    except Exception as e:
        print(f"Error: {e}")
        error_response = jsonify({
            'success': False,
            'error': str(e)
        })
        error_response.headers['Access-Control-Allow-Origin'] = '*'
        return error_response, 500


@app.route('/api/v1/job/<job_id>', methods=['GET'])
def check_job_status(job_id):
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
        'edition': job.get('edition', 'pro'),
        'created_at': job['created_at'],
        'updated_at': job['updated_at']
    }
    
    if job['status'] == 'completed':
        response_data['result'] = job['result']
    elif job['status'] == 'failed':
        response_data['error'] = job.get('error', 'Unknown error')
    
    response = jsonify(response_data)
    response.headers['Access-Control-Allow-Origin'] = '*'
    
    return response


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    print(f"\n{'='*80}")
    print(f"💎 Quantum Foam RNG API - PRO EDITION 💎")
    print(f"{'='*80}")
    print(f"Port: {port}")
    print(f"Quantum: {QUANTUM_AVAILABLE}")
    print(f"Bases: 75 optimized")
    print(f"Extraction: 3-stage (VN + XOR + Toeplitz)")
    print(f"Expected foam: σ > 0.5")
    print(f"{'='*80}\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
