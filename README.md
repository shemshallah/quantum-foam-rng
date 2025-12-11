# 🌊 Quantum Foam Entropy

The world's first quantum foam-based random number generator.

## Editions

### Community Edition (Free)
- Open source (MIT License)
- 9 basic Pauli bases
- Perfect for learning and prototyping
- [Documentation](docs/free.md)

### Pro Edition ($99/mo)
- 75 optimized high-foam bases
- 10x faster generation
- Quantum certificates
- Priority support
- [Get API Key](https://quantumfoam.io/pricing)

## Quick Start

### Free Edition
```python
from quantumfoam.free import QuantumFoamRNG_Free

rng = QuantumFoamRNG_Free()
key = rng.generate_crypto_key()
print(key['private_key'])
Pro Edition
from quantumfoam.pro import QuantumFoamRNG_Pro

rng = QuantumFoamRNG_Pro(api_key="YOUR_KEY")
key = rng.generate_crypto_key()
print(key['private_key'])
print(key['certificate'])