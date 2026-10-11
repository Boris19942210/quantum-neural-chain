"""
quantum_state.py - Квантовое состояние для нейрона

Представляет состояние 2-кубитной системы:
|ψ⟩ = α|00⟩ + β|01⟩ + γ|10⟩ + δ|11⟩

где α, β, γ, δ - комплексные амплитуды вероятности
"""

import numpy as np
import json
import hashlib
from typing import Tuple, List, Optional, Union

class QuantumState:
    """
    Квантовое состояние нейрона
    
    Атрибуты:
        amplitudes (np.ndarray): массив из 4 комплексных чисел [α, β, γ, δ]
        measured (bool): было ли состояние измерено
        collapsed_value (Optional[int]): значение после коллапса (0 или 1)
        phase (float): глобальная фаза (для резонанса)
    """
    
    def __init__(self, amplitudes: Optional[np.ndarray] = None):
        """
        Инициализация квантового состояния
        
        Args:
            amplitudes: начальные амплитуды, если None - состояние |00⟩
        """
        if amplitudes is not None:
            if len(amplitudes) != 4:
                raise ValueError("Должно быть 4 амплитуды для 2 кубитов")
            self.amplitudes = np.array(amplitudes, dtype=complex)
            self.normalize()
        else:
            # Состояние |00⟩ по умолчанию
            self.amplitudes = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
        
        self.measured = False
        self.collapsed_value = None
        self.phase = 0.0
        self.last_evolution = 0.0
        
    @classmethod
    def from_text(cls, text: str) -> 'QuantumState':
        """
        Создает квантовое состояние из текста
        
        Использует хеш текста для генерации амплитуд
        Это позволяет разным текстам иметь разные квантовые состояния
        
        Args:
            text: строка текста (ключ или значение)
            
        Returns:
            QuantumState: квантовое состояние, представляющее текст
        """
        # Получаем хеш текста
        hash_obj = hashlib.sha256(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()
        
        # Используем первые 32 байта для генерации 4 комплексных чисел
        amplitudes = []
        for i in range(4):
            # Берем 8 байт для действительной и 8 для мнимой части
            real_bytes = hash_bytes[i*8:(i*8)+4]
            imag_bytes = hash_bytes[i*8+4:(i*8)+8]
            
            # Преобразуем в числа от -1 до 1
            real = int.from_bytes(real_bytes, 'big') / (2**32) * 2 - 1
            imag = int.from_bytes(imag_bytes, 'big') / (2**32) * 2 - 1
            
            amplitudes.append(complex(real, imag))
        
        return cls(amplitudes)
    
    def normalize(self) -> None:
        """
        Нормализует состояние: сумма квадратов модулей = 1
        """
        norm = np.sqrt(np.sum(np.abs(self.amplitudes) ** 2))
        if norm > 0:
            self.amplitudes = self.amplitudes / norm
    
    def apply_gate(self, gate_matrix: np.ndarray, qubits: List[int]) -> None:
        """
        Применяет квантовый гейт к указанным кубитам
        
        Args:
            gate_matrix: матрица гейта (2x2 для 1 кубита, 4x4 для 2)
            qubits: индексы кубитов (0 или 1 для нашей 2-кубитной системы)
        """
        if len(qubits) == 1:
            # Однокубитный гейт
            qubit = qubits[0]
            
            # Создаем новое состояние
            new_amplitudes = np.zeros(4, dtype=complex)
            
            # Применяем гейт к указанному кубиту
            for i in range(4):
                # Определяем состояние другого кубита
                other_bit = (i >> (1 - qubit)) & 1
                
                # Применяем гейт к текущему кубиту
                for j in range(2):
                    # Индекс источника: j на целевом кубите, other_bit на другом
                    if qubit == 0:
                        source_idx = (j << 1) | other_bit
                    else:  # qubit == 1
                        source_idx = (other_bit << 1) | j
                    
                    # Индекс в матрице гейта: [текущее состояние целевого кубита][исходное состояние]
                    gate_row = (i >> qubit) & 1
                    gate_col = j
                    
                    new_amplitudes[i] += gate_matrix[gate_row, gate_col] * self.amplitudes[source_idx]
            
            self.amplitudes = new_amplitudes
            
        elif len(qubits) == 2:
            # Двухкубитный гейт
            self.amplitudes = gate_matrix @ self.amplitudes
        
        self.normalize()
    
    def apply_hadamard(self, qubit: int) -> None:
        """
        Применяет гейт Адамара к кубиту
        
        Создает состояние суперпозиции:
        H|0⟩ = (|0⟩ + |1⟩)/√2
        H|1⟩ = (|0⟩ - |1⟩)/√2
        
        Args:
            qubit: индекс кубита (0 или 1)
        """
        H = (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)
        self.apply_gate(H, [qubit])
    
    def apply_pauli_x(self, qubit: int) -> None:
        """
        Применяет гейт Паули X (NOT)
        
        X|0⟩ = |1⟩
        X|1⟩ = |0⟩
        
        Args:
            qubit: индекс кубита (0 или 1)
        """
        X = np.array([[0, 1], [1, 0]], dtype=complex)
        self.apply_gate(X, [qubit])
    
    def apply_pauli_y(self, qubit: int) -> None:
        """
        Применяет гейт Паули Y
        
        Y|0⟩ = i|1⟩
        Y|1⟩ = -i|0⟩
        
        Args:
            qubit: индекс кубита (0 или 1)
        """
        Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
        self.apply_gate(Y, [qubit])
    
    def apply_pauli_z(self, qubit: int) -> None:
        """
        Применяет гейт Паули Z (фазовый сдвиг)
        
        Z|0⟩ = |0⟩
        Z|1⟩ = -|1⟩
        
        Args:
            qubit: индекс кубита (0 или 1)
        """
        Z = np.array([[1, 0], [0, -1]], dtype=complex)
        self.apply_gate(Z, [qubit])
    
    def apply_cnot(self, control: int, target: int) -> None:
        """
        Применяет гейт CNOT (Controlled-NOT)
        
        Если control = 1, то target инвертируется
        Создает запутанность между кубитами
        
        Args:
            control: индекс управляющего кубита (0 или 1)
            target: индекс целевого кубита (0 или 1)
        """
        if control == target:
            raise ValueError("Control и target должны быть разными кубитами")
        
        # Матрица CNOT для порядка |00>, |01>, |10>, |11>
        CNOT = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0]
        ], dtype=complex)
        
        # Если control=1 и target=0, нужно переставить строки/столбцы
        if control == 1 and target == 0:
            # Перестановка: |00> -> |00>, |01> -> |10>, |10> -> |01>, |11> -> |11>
            perm = [0, 2, 1, 3]
            CNOT = CNOT[perm][:, perm]
        
        self.apply_gate(CNOT, [0, 1])
    
    def apply_phase_shift(self, phase: float, qubit: Optional[int] = None) -> None:
        """
        Применяет фазовый сдвиг
        
        Args:
            phase: угол сдвига в радианах
            qubit: если указан, сдвиг только для этого кубита,
                  иначе глобальный сдвиг для всего состояния
        """
        if qubit is None:
            # Глобальный фазовый сдвиг
            self.amplitudes *= np.exp(1j * phase)
        else:
            # Фазовый сдвиг для конкретного кубита
            R = np.array([[1, 0], [0, np.exp(1j * phase)]], dtype=complex)
            self.apply_gate(R, [qubit])
    
    def measure(self, qubit: Optional[int] = None) -> Union[int, Tuple[int, int]]:
        """
        Измеряет состояние (коллапс)
        
        Args:
            qubit: если указан, измеряет только этот кубит,
                  иначе измеряет всю систему
            
        Returns:
            если qubit указан: 0 или 1
            если не указан: (бит0, бит1)
        """
        if self.measured:
            if qubit is None:
                return (self.collapsed_value >> 1) & 1, self.collapsed_value & 1
            else:
                return (self.collapsed_value >> (1 - qubit)) & 1
        
        if qubit is not None:
            # Измерение одного кубита
            if qubit == 0:
                prob0 = np.abs(self.amplitudes[0])**2 + np.abs(self.amplitudes[1])**2
                prob1 = np.abs(self.amplitudes[2])**2 + np.abs(self.amplitudes[3])**2
            else:  # qubit == 1
                prob0 = np.abs(self.amplitudes[0])**2 + np.abs(self.amplitudes[2])**2
                prob1 = np.abs(self.amplitudes[1])**2 + np.abs(self.amplitudes[3])**2
            
            # Случайный выбор
            rand = np.random.random()
            result = 0 if rand < prob0 else 1
            
            # Коллапс состояния
            if result == 0:
                if qubit == 0:
                    self.amplitudes = np.array([self.amplitudes[0], self.amplitudes[1], 0, 0])
                else:
                    self.amplitudes = np.array([self.amplitudes[0], 0, self.amplitudes[2], 0])
            else:
                if qubit == 0:
                    self.amplitudes = np.array([0, 0, self.amplitudes[2], self.amplitudes[3]])
                else:
                    self.amplitudes = np.array([0, self.amplitudes[1], 0, self.amplitudes[3]])
            
            self.normalize()
            return result
        
        else:
            # Измерение всей системы
            probs = np.abs(self.amplitudes) ** 2
            rand = np.random.random()
            
            cumsum = 0
            for i, prob in enumerate(probs):
                cumsum += prob
                if rand < cumsum:
                    result = i
                    break
            else:
                result = 3
            
            # Коллапс в измеренное состояние
            new_amplitudes = np.zeros(4, dtype=complex)
            new_amplitudes[result] = 1.0
            self.amplitudes = new_amplitudes
            self.measured = True
            self.collapsed_value = result
            
            return (result >> 1) & 1, result & 1
    
    def evolve(self, time_step: float = 0.1) -> None:
        """
        Эволюция состояния во времени (унитарная)
        
        Просто добавляет фазу для демонстрации
        В реальности здесь должно быть уравнение Шредингера
        
        Args:
            time_step: шаг времени
        """
        # Унитарная эволюция: поворачиваем фазу всех амплитуд
        phase = time_step * np.pi
        self.amplitudes *= np.exp(1j * phase)
        self.phase += phase
        self.last_evolution += time_step
    
    def density_matrix(self) -> np.ndarray:
        """
        Возвращает матрицу плотности ρ = |ψ⟩⟨ψ|
        
        Returns:
            np.ndarray: матрица 4x4
        """
        return np.outer(self.amplitudes, np.conj(self.amplitudes))
    
    def reduced_density_matrix(self, qubit: int) -> np.ndarray:
        """
        Частичная матрица плотности для одного кубита
        
        Args:
            qubit: индекс кубита (0 или 1)
            
        Returns:
            np.ndarray: матрица 2x2
        """
        rho = self.density_matrix()
        
        if qubit == 0:
            # Частичный след по второму кубиту
            rho_A = np.array([
                [rho[0,0] + rho[1,1], rho[0,2] + rho[1,3]],
                [rho[2,0] + rho[3,1], rho[2,2] + rho[3,3]]
            ])
        else:
            # Частичный след по первому кубиту
            rho_A = np.array([
                [rho[0,0] + rho[2,2], rho[0,1] + rho[2,3]],
                [rho[1,0] + rho[3,2], rho[1,1] + rho[3,3]]
            ])
        
        return rho_A
    
    def von_neumann_entropy(self) -> float:
        """
        Энтропия фон Неймана S = -Tr(ρ log ρ)
        
        Мера запутанности всей системы
        """
        rho = self.density_matrix()
        eigenvalues = np.linalg.eigvalsh(rho)
        eigenvalues = eigenvalues[eigenvalues > 1e-10]  # убираем шум
        
        entropy = -np.sum(eigenvalues * np.log2(eigenvalues))
        return entropy
    
    def entanglement_entropy(self, qubit: int) -> float:
        """
        Энтропия запутанности для кубита
        
        Args:
            qubit: индекс кубита
            
        Returns:
            float: энтропия (0 - нет запутанности, 1 - максимальная)
        """
        rho_A = self.reduced_density_matrix(qubit)
        eigenvalues = np.linalg.eigvalsh(rho_A)
        eigenvalues = eigenvalues[eigenvalues > 1e-10]
        
        entropy = -np.sum(eigenvalues * np.log2(eigenvalues))
        return entropy
    
    def concurrence(self) -> float:
        """
        Concurrence - мера запутанности для двух кубитов
        
        Returns:
            float: от 0 (нет запутанности) до 1 (максимальная)
        """
        # Матрица для спин-флип операции
        sigma_y = np.array([[0, -1j], [1j, 0]])
        YY = np.kron(sigma_y, sigma_y)
        
        # Вычисляем ρ̃ = (Y⊗Y) ρ* (Y⊗Y)
        rho = self.density_matrix()
        rho_tilde = YY @ np.conj(rho) @ YY
        
        # Собственные значения R = sqrt(√ρ ρ̃ √ρ)
        sqrt_rho = np.sqrt(rho)
        R = sqrt_rho @ rho_tilde @ sqrt_rho
        eigenvalues = np.sort(np.linalg.eigvalsh(R))[::-1]
        
        # Concurrence = max(0, λ1 - λ2 - λ3 - λ4)
        concurrence = max(0, eigenvalues[0] - eigenvalues[1] - 
                          eigenvalues[2] - eigenvalues[3])
        
        return float(np.real(concurrence))
    
    def fidelity(self, other: 'QuantumState') -> float:
        """
        Fidelity между двумя состояниями F = |⟨ψ|φ⟩|²
        
        Args:
            other: другое квантовое состояние
            
        Returns:
            float: мера близости состояний (0-1)
        """
        overlap = np.vdot(self.amplitudes, other.amplitudes)
        return float(np.abs(overlap) ** 2)
    
    def reset(self) -> None:
        """Сбрасывает состояние в |00⟩"""
        self.amplitudes = np.array([1.0, 0.0, 0.0, 0.0], dtype=complex)
        self.measured = False
        self.collapsed_value = None
        self.phase = 0.0
    
    def to_dict(self) -> dict:
        """Сериализация в словарь"""
        return {
            'amplitudes': [[amp.real, amp.imag] for amp in self.amplitudes],
            'measured': self.measured,
            'collapsed_value': self.collapsed_value,
            'phase': self.phase,
            'last_evolution': self.last_evolution
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'QuantumState':
        """Восстановление из словаря"""
        amplitudes = [complex(amp[0], amp[1]) for amp in data['amplitudes']]
        state = cls(amplitudes)
        state.measured = data['measured']
        state.collapsed_value = data['collapsed_value']
        state.phase = data['phase']
        state.last_evolution = data['last_evolution']
        return state
    
    def __str__(self) -> str:
        """Строковое представление"""
        amps = self.amplitudes
        s = f"|ψ⟩ = {amps[0]:.3f}{amps[0].imag:+.3f}j|00⟩"
        if np.abs(amps[1]) > 1e-3:
            s += f" + {amps[1]:.3f}{amps[1].imag:+.3f}j|01⟩"
        if np.abs(amps[2]) > 1e-3:
            s += f" + {amps[2]:.3f}{amps[2].imag:+.3f}j|10⟩"
        if np.abs(amps[3]) > 1e-3:
            s += f" + {amps[3]:.3f}{amps[3].imag:+.3f}j|11⟩"
        
        if self.measured:
            s += f" [измерено: {self.collapsed_value}]"
        
        s += f" (φ={self.phase:.2f})"
        return s
    
    def __repr__(self) -> str:
        return self.__str__()


# ===== БЫСТРЫЕ ТЕСТЫ =====
if __name__ == "__main__":
    print("🔬 Тестирование QuantumState\n")
    
    # Создаем состояние |00⟩
    state = QuantumState()
    print(f"1. Начальное состояние: {state}")
    
    # Применяем Адамара к первому кубиту
    state.apply_hadamard(0)
    print(f"2. После H на кубите 0: {state}")
    
    # Применяем CNOT
    state.apply_cnot(0, 1)
    print(f"3. После CNOT (0→1): {state}")
    
    # Проверяем запутанность
    print(f"4. Concurrence: {state.concurrence():.3f}")
    print(f"5. Энтропия запутанности кубита 0: {state.entanglement_entropy(0):.3f}")
    
    # Измеряем
    result = state.measure()
    print(f"6. Измерение: {result}")
    print(f"7. После измерения: {state}")
    
    # Создаем состояние из текста
    text_state = QuantumState.from_text("квантовая запутанность")
    print(f"\n8. Состояние из текста: {text_state}")
    
    # Эволюция
    text_state.evolve(0.5)
    print(f"9. После эволюции: {text_state}")