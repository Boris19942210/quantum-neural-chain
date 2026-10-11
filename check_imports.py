# check_imports.py
import sys
import os

print("Текущая папка:", os.getcwd())
print("Python path:", sys.path)

try:
    print("\nПробуем импортировать core...")
    import core
    print("✅ core импортирован")
    print("core.__file__:", core.__file__)
    print("core.__dict__ keys:", [k for k in dir(core) if not k.startswith('_')])
except Exception as e:
    print("❌ Ошибка импорта core:", e)

try:
    print("\nПробуем импортировать core.neuron...")
    import core.neuron
    print("✅ core.neuron импортирован")
    print("core.neuron.__dict__ keys:", [k for k in dir(core.neuron) if not k.startswith('_')])
except Exception as e:
    print("❌ Ошибка импорта core.neuron:", e)

try:
    print("\nПробуем импортировать QuantumNeuron...")
    from core.neuron import QuantumNeuron
    print("✅ QuantumNeuron импортирован")
    print("QuantumNeuron:", QuantumNeuron)
except Exception as e:
    print("❌ Ошибка импорта QuantumNeuron:", e)