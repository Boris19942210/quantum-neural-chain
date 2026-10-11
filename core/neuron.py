"""
neuron.py - Квантовый нейрон для Quantum Neural Chain

Каждый нейрон это:
- Квантовое состояние (2 кубита)
- Классические данные (ключ, значение)
- Запутанность с другими нейронами
- Метаданные для блокчейна
"""

import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

from .quantum_state import QuantumState

class QuantumNeuron:
    """
    Квантовый нейрон - основной строительный блок системы
    
    Атрибуты:
        key (str): уникальный идентификатор нейрона (как адрес в блокчейне)
        value (Any): данные, которые хранит нейрон
        quantum_state (QuantumState): квантовое состояние нейрона
        created_at (float): timestamp создания
        last_active (float): timestamp последней активации
        activation_count (int): сколько раз нейрон использовался
        creator (str): кто создал нейрон (node_id)
        parent_hash (Optional[str]): хеш предыдущего нейрона в цепи
        entangled_with (Dict[str, float]): карта запутанности {neuron_hash: strength}
        hash (str): хеш текущего состояния нейрона
        metadata (Dict): дополнительные метаданные
    """
    
    def __init__(self, 
                 key: str,
                 value: Any,
                 creator: str = "system",
                 parent_hash: Optional[str] = None,
                 quantum_state: Optional[QuantumState] = None):
        """
        Инициализация квантового нейрона
        
        Args:
            key: уникальный идентификатор
            value: данные для хранения
            creator: ID создателя
            parent_hash: хеш предыдущего нейрона (для блокчейна)
            quantum_state: готовое квантовое состояние (если есть)
        """
        self.key = key
        self.value = value
        self.creator = creator
        self.parent_hash = parent_hash
        
        # Временные метки
        current_time = time.time()
        self.created_at = current_time
        self.last_active = current_time
        self.activation_count = 0
        
        # Квантовое состояние
        if quantum_state:
            self.quantum_state = quantum_state
        else:
            # Создаем состояние из ключа и значения
            self.quantum_state = self._create_quantum_from_data(key, value)
        
        # Запутанность с другими нейронами (хеш -> сила связи)
        self.entangled_with: Dict[str, float] = {}
        
        # История активаций (для обучения)
        self.activation_history: List[Dict] = []
        
        # Метаданные
        self.metadata = {
            'version': '1.0',
            'type': 'quantum_neuron',
            'tags': []
        }
        
        # Хеш текущего состояния
        self.hash = self._calculate_hash()
        
    def _create_quantum_from_data(self, key: str, value: Any) -> QuantumState:
        """
        Создает квантовое состояние из ключа и значения
        
        Использует хеши для генерации уникальных амплитуд
        
        Args:
            key: ключ нейрона
            value: значение нейрона
            
        Returns:
            QuantumState: квантовое состояние
        """
        # Комбинируем ключ и значение для уникальности
        combined = f"{key}:{value}"
        return QuantumState.from_text(combined)
    
    def _calculate_hash(self) -> str:
        """
        Вычисляет хеш текущего состояния нейрона
        
        Хешируются все важные атрибуты для блокчейна
        """
        # Подготавливаем данные для хеширования
        data = {
            'key': self.key,
            'value': str(self.value),  # конвертируем в строку
            'creator': self.creator,
            'created_at': self.created_at,
            'last_active': self.last_active,
            'activation_count': self.activation_count,
            'parent_hash': self.parent_hash,
            'quantum_state': self.quantum_state.to_dict(),
            'entangled_with': self.entangled_with,
            'metadata': self.metadata
        }
        
        # Сортируем ключи для детерминизма
        json_str = json.dumps(data, sort_keys=True, default=str)
        
        # Вычисляем SHA-256 хеш
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def activate(self, 
                 input_signal: float = 1.0, 
                 context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Активация нейрона входным сигналом
        
        Процесс:
        1. Применяем входной сигнал к квантовому состоянию
        2. Измеряем состояние (получаем классический выход)
        3. Обновляем метаданные
        4. Возвращаем результат
        
        Args:
            input_signal: сила входного сигнала (0-1)
            context: дополнительный контекст (для обучения)
            
        Returns:
            Dict с результатами активации
        """
        context = context or {}
        
        # Сохраняем состояние до активации
        before_state = self.quantum_state.amplitudes.copy()
        
        # 1. Применяем входной сигнал (фазовый сдвиг)
        # Сигнал влияет на фазу квантового состояния
        phase_shift = input_signal * np.pi
        self.quantum_state.apply_phase_shift(phase_shift)
        
        # 2. Измеряем первый кубит (получаем классический выход)
        # 0 или 1
        output = self.quantum_state.measure(qubit=0)
        
        # 3. Обновляем метаданные
        self.last_active = time.time()
        self.activation_count += 1
        
        # 4. Сохраняем в историю
        activation_record = {
            'timestamp': self.last_active,
            'input_signal': input_signal,
            'output': output,
            'context': context,
            'quantum_before': before_state.tolist(),
            'quantum_after': self.quantum_state.amplitudes.tolist()
        }
        self.activation_history.append(activation_record)
        
        # Ограничиваем историю (храним последние 100)
        if len(self.activation_history) > 100:
            self.activation_history = self.activation_history[-100:]
        
        # Обновляем хеш (состояние изменилось)
        self.hash = self._calculate_hash()
        
        return {
            'neuron_key': self.key,
            'neuron_hash': self.hash[:8],  # короткий хеш для отображения
            'output': output,
            'activation_count': self.activation_count,
            'quantum_state': self.quantum_state.amplitudes.tolist(),
            'entropy': self.quantum_state.von_neumann_entropy()
        }
    
    def entangle_with(self, 
                      other: 'QuantumNeuron', 
                      strength: float = 1.0,
                      method: str = 'auto') -> bool:
        """
        Создает запутанность с другим нейроном
        
        Args:
            other: другой нейрон
            strength: сила запутанности (0-1)
            method: метод создания ('bell', 'partial', 'auto')
            
        Returns:
            bool: успешно ли создана запутанность
        """
        if self.hash == other.hash:
            return False  # нельзя запутать с самим собой
        
        # Проверяем, не запутаны ли уже
        if other.hash in self.entangled_with:
            return False
        
        if method == 'bell':
            # Создаем максимальную запутанность (состояние Белла)
            # (|00⟩ + |11⟩)/√2
            self.quantum_state.reset()
            other.quantum_state.reset()
            
            # Создаем запутанность через H и CNOT
            self.quantum_state.apply_hadamard(0)
            self.quantum_state.apply_cnot(0, 1)
            
            # Синхронизируем состояния
            other.quantum_state.amplitudes = self.quantum_state.amplitudes.copy()
            
        elif method == 'partial':
            # Частичная запутанность
            # Смешиваем состояния
            mixed = (self.quantum_state.amplitudes + other.quantum_state.amplitudes) / np.sqrt(2)
            mixed = mixed / np.linalg.norm(mixed)
            
            self.quantum_state.amplitudes = mixed * np.sqrt(strength)
            other.quantum_state.amplitudes = mixed * np.sqrt(1 - strength)
            
            self.quantum_state.normalize()
            other.quantum_state.normalize()
            
        else:  # 'auto'
            # Автоматический выбор метода в зависимости от силы
            if strength > 0.8:
                return self.entangle_with(other, strength, 'bell')
            else:
                return self.entangle_with(other, strength, 'partial')
        
        # Записываем запутанность в обе стороны
        self.entangled_with[other.hash] = strength
        other.entangled_with[self.hash] = strength
        
        # Обновляем хеши
        self.hash = self._calculate_hash()
        other.hash = other._calculate_hash()
        
        return True
    
    def measure(self, collapse: bool = True) -> int:
        """
        Полное измерение нейрона (коллапс)
        
        Args:
            collapse: разрушать ли запутанность
            
        Returns:
            int: результат измерения (0 или 1)
        """
        # Измеряем всё состояние
        result = self.quantum_state.measure()
        
        if collapse:
            # Разрушаем все запутанности
            self.entangled_with.clear()
            
        # Обновляем хеш
        self.hash = self._calculate_hash()
        
        return result[0] if isinstance(result, tuple) else result
    
    def get_resonance_with(self, other: 'QuantumNeuron') -> float:
        """
        Вычисляет квантовый резонанс с другим нейроном
        
        Резонанс = |⟨ψ|φ⟩|² * (1 + сила_запутанности)
        
        Args:
            other: другой нейрон
            
        Returns:
            float: резонанс (0-1)
        """
        # Базовое перекрытие состояний
        overlap = self.quantum_state.fidelity(other.quantum_state)
        
        # Усиление, если запутаны
        entanglement_boost = 1.0
        if other.hash in self.entangled_with:
            strength = self.entangled_with[other.hash]
            entanglement_boost = 1.0 + strength
        
        return overlap * entanglement_boost
    
    def add_tag(self, tag: str) -> None:
        """Добавляет тег к нейрону"""
        if 'tags' not in self.metadata:
            self.metadata['tags'] = []
        if tag not in self.metadata['tags']:
            self.metadata['tags'].append(tag)
            self.hash = self._calculate_hash()
    
    def to_block(self) -> Dict:
        """
        Конвертирует нейрон в блок для блокчейна
        
        Returns:
            Dict: данные блока
        """
        return {
            'hash': self.hash,
            'key': self.key,
            'value': self.value,
            'creator': self.creator,
            'created_at': self.created_at,
            'last_active': self.last_active,
            'activation_count': self.activation_count,
            'parent_hash': self.parent_hash,
            'quantum_state': self.quantum_state.to_dict(),
            'entangled_with': self.entangled_with,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_block(cls, block: Dict) -> 'QuantumNeuron':
        """
        Восстанавливает нейрон из блока
        
        Args:
            block: данные блока
            
        Returns:
            QuantumNeuron: восстановленный нейрон
        """
        # Восстанавливаем квантовое состояние
        quantum_state = QuantumState.from_dict(block['quantum_state'])
        
        # Создаем нейрон
        neuron = cls(
            key=block['key'],
            value=block['value'],
            creator=block['creator'],
            parent_hash=block.get('parent_hash'),
            quantum_state=quantum_state
        )
        
        # Восстанавливаем остальные атрибуты
        neuron.created_at = block['created_at']
        neuron.last_active = block['last_active']
        neuron.activation_count = block['activation_count']
        neuron.entangled_with = block['entangled_with']
        neuron.metadata = block['metadata']
        neuron.hash = block['hash']
        
        return neuron
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь"""
        return {
            'key': self.key,
            'value': self.value,
            'creator': self.creator,
            'hash': self.hash,
            'parent_hash': self.parent_hash,
            'created_at': self.created_at,
            'last_active': self.last_active,
            'activation_count': self.activation_count,
            'quantum_state': self.quantum_state.to_dict(),
            'entangled_with': self.entangled_with,
            'metadata': self.metadata
        }
    
    def __str__(self) -> str:
        """Краткое представление"""
        return (f"Neuron({self.key[:20]}... | "
                f"acts:{self.activation_count} | "
                f"ent:{len(self.entangled_with)} | "
                f"hash:{self.hash[:8]})")
    
    def __repr__(self) -> str:
        return self.__str__()


# ===== БЫСТРЫЕ ТЕСТЫ =====
if __name__ == "__main__":
    print("🧠 Тестирование QuantumNeuron\n")
    
    # Создаем первый нейрон
    n1 = QuantumNeuron(
        key="квантовая запутанность",
        value="Эффект мгновенной связи между частицами",
        creator="test_user"
    )
    print(f"1. Создан нейрон 1: {n1}")
    print(f"   Квантовое состояние: {n1.quantum_state}")
    
    # Создаем второй нейрон
    n2 = QuantumNeuron(
        key="нейронная сеть",
        value="Математическая модель мозга",
        creator="test_user"
    )
    print(f"\n2. Создан нейрон 2: {n2}")
    print(f"   Квантовое состояние: {n2.quantum_state}")
    
    # Запутываем нейроны
    success = n1.entangle_with(n2, strength=0.9, method='bell')
    print(f"\n3. Запутывание нейронов: {'✅' if success else '❌'}")
    print(f"   Запутанность n1: {n1.entangled_with}")
    print(f"   Запутанность n2: {n2.entangled_with}")
    
    # Вычисляем резонанс
    resonance = n1.get_resonance_with(n2)
    print(f"\n4. Резонанс между нейронами: {resonance:.3f}")
    
    # Активируем первый нейрон
    activation = n1.activate(input_signal=0.7, context={'test': True})
    print(f"\n5. Активация нейрона 1:")
    print(f"   Выход: {activation['output']}")
    print(f"   Счетчик активаций: {activation['activation_count']}")
    print(f"   Энтропия: {activation['entropy']:.3f}")
    
    # Конвертируем в блок
    block = n1.to_block()
    print(f"\n6. Блок нейрона:")
    print(f"   Хеш: {block['hash'][:16]}...")
    print(f"   Ключ: {block['key']}")
    
    # Восстанавливаем из блока
    n1_restored = QuantumNeuron.from_block(block)
    print(f"\n7. Восстановленный нейрон: {n1_restored}")
    print(f"   Хеш совпадает: {n1.hash == n1_restored.hash}")