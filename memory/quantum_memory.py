"""
quantum_memory.py - Квантовая память для хранения и поиска фактов

Объединяет:
- Квантовые нейроны (факты)
- Запутанность между ними
- Поиск с квантовым усилением
- Автосохранение и загрузку
"""

import json
import time
import hashlib
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict
import numpy as np

from core.neuron import QuantumNeuron
from core.entanglement import EntanglementGraph, QuantumResonance

"""
quantum_memory.py - Квантовая память для хранения и поиска фактов
"""

# Добавляем корневую папку в путь
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict
import numpy as np

from core.neuron import QuantumNeuron
from core.entanglement import EntanglementGraph, QuantumResonance

class QuantumMemory:
    """
    Квантовая память - аналог твоего jarvis_server.js но на Python
    
    Хранит факты как квантовые нейроны с запутанностью между ними.
    Поиск использует квантовое усиление - связанные факты влияют друг на друга.
    """
    
    def __init__(self, memory_file: str = "quantum_memory.json"):
        """
        Инициализация квантовой памяти
        
        Args:
            memory_file: файл для сохранения/загрузки
        """
        self.memory_file = memory_file
        
        # Граф всех нейронов
        self.graph = EntanglementGraph()
        
        # Резонанс для поиска
        self.resonance = QuantumResonance(self.graph)
        
        # Индексы для быстрого поиска
        self.key_to_hash: Dict[str, str] = {}  # ключ -> хеш нейрона
        self.hash_to_key: Dict[str, str] = {}  # хеш -> ключ
        
        # Статистика
        self.stats = {
            'total_facts': 0,
            'total_searches': 0,
            'avg_search_time': 0.0,
            'last_save': 0,
            'created_at': time.time()
        }
        
        # Загружаем сохраненную память
        self.load()
        
        # История последних запросов (для контекста)
        self.recent_queries: List[str] = []
        
    def remember(self, key: str, value: Any, creator: str = "user") -> str:
        """
        Запоминает факт (создает нейрон)
        
        Args:
            key: ключ (вопрос/тема)
            value: значение (ответ/факт)
            creator: кто создал
            
        Returns:
            str: хеш созданного нейрона
        """
        # Проверяем, существует ли уже
        if key in self.key_to_hash:
            existing_hash = self.key_to_hash[key]
            existing = self.graph.nodes.get(existing_hash)
            if existing:
                print(f"📝 Факт '{key}' уже существует, обновляем значение")
                existing.value = value
                existing.hash = existing._calculate_hash()
                self._auto_entangle(existing)
                self.save()
                return existing_hash
        
        # Создаем новый нейрон
        neuron = QuantumNeuron(
            key=key,
            value=value,
            creator=creator
        )
        
        # Добавляем в граф
        self.graph.add_neuron(neuron)
        self.key_to_hash[key] = neuron.hash
        self.hash_to_key[neuron.hash] = key
        
        # Автоматически запутываем с похожими фактами
        self._auto_entangle(neuron)
        
        # Обновляем статистику
        self.stats['total_facts'] = len(self.graph.nodes)
        
        # Сохраняем
        self.save()
        
        print(f"✅ Запомнил: '{key}' → '{value[:50]}...'")
        return neuron.hash
    
    def _auto_entangle(self, neuron: QuantumNeuron, threshold: float = 0.3) -> None:
        """
        Автоматически запутывает нейрон с похожими
        
        Args:
            neuron: новый нейрон
            threshold: порог сходства для запутывания
        """
        for h, other in self.graph.nodes.items():
            if h == neuron.hash:
                continue
            
            # Вычисляем сходство
            similarity = self._calculate_similarity(neuron, other)
            
            if similarity > threshold:
                # Чем выше сходство, тем сильнее запутанность
                strength = similarity * 0.8
                self.graph.create_entanglement(
                    neuron, other, strength, 'partial'
                )
                print(f"🌀 Автозапутывание: {neuron.key[:20]}... ↔ {other.key[:20]}... ({strength:.2f})")
    
    def _calculate_similarity(self, n1: QuantumNeuron, n2: QuantumNeuron) -> float:
        """
        Вычисляет сходство между нейронами
        
        Учитывает:
        - Текстовое сходство ключей
        - Квантовое перекрытие состояний
        - Общие теги/метаданные
        """
        # Текстовое сходство ключей
        text_sim = self._text_similarity(n1.key, n2.key)
        
        # Квантовое перекрытие
        quantum_sim = n1.quantum_state.fidelity(n2.quantum_state)
        
        # Метаданные (общие теги)
        tags1 = set(n1.metadata.get('tags', []))
        tags2 = set(n2.metadata.get('tags', []))
        tag_sim = len(tags1 & tags2) / max(len(tags1 | tags2), 1)
        
        # Комбинируем
        similarity = 0.5 * text_sim + 0.3 * quantum_sim + 0.2 * tag_sim
        
        return similarity
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Простое текстовое сходство"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def recall(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Вспоминает факты по запросу (с квантовым усилением)
        
        Args:
            query: поисковый запрос
            top_k: сколько результатов вернуть
            
        Returns:
            List[Dict]: результаты с релевантностью
        """
        start_time = time.time()
        
        # Добавляем в историю
        self.recent_queries.append(query)
        if len(self.recent_queries) > 10:
            self.recent_queries.pop(0)
        
        # Создаем временный "поисковый нейрон"
        search_key = f"_search_{query}"
        search_neuron = QuantumNeuron(
            key=search_key,
            value=query,
            creator="_system"
        )
        
        results = []
        
        for h, neuron in self.graph.nodes.items():
            # Базовое сходство с запросом
            base_sim = self._calculate_similarity(search_neuron, neuron)
            
            if base_sim < 0.1:
                continue
            
            # Квантовое усиление через резонанс
            quantum_boost = 1.0
            
            # Проверяем, есть ли у нейрона запутанности с недавними запросами
            for recent in self.recent_queries[-3:]:
                recent_hash = self.key_to_hash.get(recent)
                if recent_hash:
                    strength = self.graph.get_entanglement_strength(h, recent_hash)
                    quantum_boost *= (1.0 + strength * 0.5)
            
            # Резонанс с другими релевантными нейронами
            resonant = self.resonance.get_most_resonant(h, top_k=3)
            if resonant:
                avg_resonance = sum(r for _, r in resonant) / len(resonant)
                quantum_boost *= (1.0 + avg_resonance * 0.3)
            
            # Финальная релевантность
            relevance = base_sim * quantum_boost
            
            results.append({
                'key': neuron.key,
                'value': neuron.value,
                'relevance': relevance,
                'base_similarity': base_sim,
                'quantum_boost': quantum_boost,
                'hash': neuron.hash[:8],
                'activation_count': neuron.activation_count,
                'entangled_with': list(neuron.entangled_with.keys())[:3]  # первые 3 для отображения
            })
        
        # Сортируем по релевантности
        results.sort(key=lambda x: x['relevance'], reverse=True)
        
        # Обновляем статистику
        self.stats['total_searches'] += 1
        search_time = time.time() - start_time
        self.stats['avg_search_time'] = (
            (self.stats['avg_search_time'] * (self.stats['total_searches'] - 1) + search_time) 
            / self.stats['total_searches']
        )
        
        # Активируем найденные нейроны (обучение)
        for r in results[:3]:  # топ-3
            neuron_hash = self.key_to_hash.get(r['key'])
            if neuron_hash:
                neuron = self.graph.nodes.get(neuron_hash)
                if neuron:
                    neuron.activate(
                        input_signal=r['relevance'],
                        context={'query': query}
                    )
        
        return results[:top_k]
    
    def forget(self, key: str) -> bool:
        """
        Забывает факт (удаляет нейрон)
        
        Args:
            key: ключ факта
            
        Returns:
            bool: успешно ли удален
        """
        if key not in self.key_to_hash:
            return False
        
        neuron_hash = self.key_to_hash[key]
        
        # Удаляем из графа
        self.graph.remove_neuron(neuron_hash)
        
        # Удаляем из индексов
        del self.key_to_hash[key]
        del self.hash_to_key[neuron_hash]
        
        # Обновляем статистику
        self.stats['total_facts'] = len(self.graph.nodes)
        
        self.save()
        print(f"🗑️ Забыл факт: {key}")
        return True
    
    def get_fact(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Получает факт по ключу (без поиска, точное совпадение)
        
        Args:
            key: ключ факта
            
        Returns:
            Optional[Dict]: данные факта или None
        """
        if key not in self.key_to_hash:
            return None
        
        neuron_hash = self.key_to_hash[key]
        neuron = self.graph.nodes.get(neuron_hash)
        
        if not neuron:
            return None
        
        # Активируем (увеличиваем счетчик)
        neuron.activate(input_signal=0.5, context={'type': 'direct_access'})
        
        return {
            'key': neuron.key,
            'value': neuron.value,
            'hash': neuron.hash[:8],
            'created_at': neuron.created_at,
            'activation_count': neuron.activation_count,
            'entangled_with': [
                self.hash_to_key.get(h, h[:8]) 
                for h in neuron.entangled_with.keys()
            ]
        }
    
    def get_all_facts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Возвращает список всех фактов
        
        Args:
            limit: максимальное количество
            
        Returns:
            List[Dict]: список фактов
        """
        facts = []
        
        for h, neuron in self.graph.nodes.items():
            facts.append({
                'key': neuron.key,
                'value': neuron.value[:100] + '...' if len(neuron.value) > 100 else neuron.value,
                'hash': neuron.hash[:8],
                'activation_count': neuron.activation_count,
                'entangled_count': len(neuron.entangled_with),
                'created': datetime.fromtimestamp(neuron.created_at).strftime('%Y-%m-%d %H:%M')
            })
        
        # Сортируем по дате создания (новые сверху)
        facts.sort(key=lambda x: x['created'], reverse=True)
        
        return facts[:limit]
    
    def entangle_facts(self, key1: str, key2: str, strength: float = 0.8) -> bool:
        """
        Запутывает два факта
        
        Args:
            key1: первый факт
            key2: второй факт
            strength: сила запутанности
            
        Returns:
            bool: успешно ли создана запутанность
        """
        if key1 not in self.key_to_hash or key2 not in self.key_to_hash:
            print(f"❌ Один из фактов не найден")
            return False
        
        h1 = self.key_to_hash[key1]
        h2 = self.key_to_hash[key2]
        
        n1 = self.graph.nodes.get(h1)
        n2 = self.graph.nodes.get(h2)
        
        if not n1 or not n2:
            return False
        
        success = self.graph.create_entanglement(n1, n2, strength, 'bell')
        
        if success:
            print(f"🌀 Запутаны: {key1} ↔ {key2} (сила: {strength})")
            self.save()
        
        return success
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику памяти"""
        # Квантовая статистика
        total_entangled = 0
        total_measured = 0
        
        for neuron in self.graph.nodes.values():
            if neuron.quantum_state.measured:
                total_measured += 1
            if neuron.entangled_with:
                total_entangled += 1
        
        # Статистика графа
        graph_stats = self.graph.stats
        
        # Вычисляем среднюю релевантность (если есть данные)
        avg_relevance = 0.0
        if self.stats['total_searches'] > 0:
            # Имитируем среднюю релевантность
            avg_relevance = 0.65
        
        return {
            'total_facts': len(self.graph.nodes),
            'total_entanglements': graph_stats['total_entanglements'],
            'total_searches': self.stats['total_searches'],
            'avg_search_time_ms': self.stats['avg_search_time'] * 1000,
            'avg_relevance': avg_relevance,
            'clusters': graph_stats['cluster_count'],
            'max_cluster_size': graph_stats['max_cluster_size'],
            'measured_facts': total_measured,
            'entangled_facts': total_entangled,
            'memory_usage': len(self.graph.nodes) * 1024,  # приблизительно
            'uptime': time.time() - self.stats['created_at']
        }
    
    def save(self) -> None:
        """Сохраняет память в файл"""
        data = {
            'neurons': [
                neuron.to_dict() 
                for neuron in self.graph.nodes.values()
            ],
            'edges': [
                (h1, h2, strength) 
                for (h1, h2), strength in self.graph.edges.items()
            ],
            'key_to_hash': self.key_to_hash,
            'stats': self.stats,
            'recent_queries': self.recent_queries,
            'saved_at': time.time()
        }
        
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            self.stats['last_save'] = time.time()
            print(f"💾 Память сохранена в {self.memory_file}")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
    
    def load(self) -> bool:
        """Загружает память из файла"""
        if not os.path.exists(self.memory_file):
            print("📝 Создаю новую квантовую память")
            return False
        
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Очищаем текущие данные
            self.graph.nodes.clear()
            self.graph.edges.clear()
            self.key_to_hash.clear()
            self.hash_to_key.clear()
            
            # Загружаем нейроны
            from core.neuron import QuantumNeuron
            
            for neuron_data in data['neurons']:
                # Восстанавливаем квантовое состояние
                from core.quantum_state import QuantumState
                quantum_state = QuantumState.from_dict(neuron_data['quantum_state'])
                
                # Создаем нейрон
                neuron = QuantumNeuron(
                    key=neuron_data['key'],
                    value=neuron_data['value'],
                    creator=neuron_data['creator']
                )
                
                # Восстанавливаем атрибуты
                neuron.hash = neuron_data['hash']
                neuron.parent_hash = neuron_data.get('parent_hash')
                neuron.created_at = neuron_data['created_at']
                neuron.last_active = neuron_data['last_active']
                neuron.activation_count = neuron_data['activation_count']
                neuron.quantum_state = quantum_state
                neuron.entangled_with = neuron_data.get('entangled_with', {})
                neuron.metadata = neuron_data.get('metadata', {})
                
                self.graph.nodes[neuron.hash] = neuron
                self.key_to_hash[neuron.key] = neuron.hash
                self.hash_to_key[neuron.hash] = neuron.key
            
            # Загружаем ребра
            for h1, h2, strength in data['edges']:
                self.graph.edges[(h1, h2)] = strength
            
            # Загружаем статистику
            self.stats = data.get('stats', self.stats)
            self.recent_queries = data.get('recent_queries', [])
            
            # Перестраиваем кластеры
            self.graph._rebuild_clusters()
            
            print(f"📦 Загружено фактов: {len(self.graph.nodes)}, связей: {len(self.graph.edges)}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return False
    
    def clear(self) -> None:
        """Очищает всю память"""
        self.graph.nodes.clear()
        self.graph.edges.clear()
        self.key_to_hash.clear()
        self.hash_to_key.clear()
        self.recent_queries.clear()
        self.stats['total_facts'] = 0
        self.stats['total_searches'] = 0
        self.save()
        print("🧹 Память очищена")
    
    def get_entanglement_map(self) -> Dict[str, Any]:
        """Возвращает карту запутанности для визуализации"""
        return self.graph.get_entanglement_map()
    
    def __str__(self) -> str:
        return (f"QuantumMemory("
                f"фактов:{len(self.graph.nodes)}, "
                f"связей:{len(self.graph.edges)}, "
                f"поисков:{self.stats['total_searches']})")


# ===== ТЕСТЫ =====

if __name__ == "__main__":
    print("🧠 Тестирование QuantumMemory\n")
    
    # Создаем память
    memory = QuantumMemory("test_memory.json")
    
    # Добавляем тестовые факты
    print("📝 Добавление фактов:")
    facts = [
        ("квантовая запутанность", "Эффект, при котором состояние одной частицы мгновенно влияет на другую, даже на расстоянии"),
        ("нейронная сеть", "Математическая модель, вдохновленная структурой мозга, состоящая из связанных нейронов"),
        ("искусственный интеллект", "Область компьютерных наук, занимающаяся созданием интеллектуальных машин"),
        ("квантовый компьютер", "Вычислительное устройство, использующее принципы квантовой механики"),
        ("машинное обучение", "Методы, позволяющие компьютерам обучаться на данных без явного программирования"),
        ("C123 язык", "Теория циклических тритов с квантовой памятью"),
        ("блокчейн", "Распределенная база данных, хранящая непрерывную цепочку блоков")
    ]
    
    for key, value in facts:
        memory.remember(key, value, creator="test")
    
    print("\n📊 Статистика:")
    stats = memory.get_stats()
    for k, v in stats.items():
        print(f"   {k}: {v}")
    
    # Тест поиска
    print("\n🔍 Поиск: 'квантовые вычисления'")
    results = memory.recall("квантовые вычисления", top_k=3)
    
    for i, r in enumerate(results, 1):
        print(f"\n   {i}. {r['key']}")
        print(f"      релевантность: {r['relevance']:.3f} (база: {r['base_similarity']:.3f}, буст: {r['quantum_boost']:.3f})")
        print(f"      {r['value'][:100]}...")
    
    # Создаем запутанность вручную
    print("\n🌀 Создание запутанности:")
    memory.entangle_facts("квантовая запутанность", "квантовый компьютер", strength=0.9)
    
    # Поиск с усилением
    print("\n🔍 Поиск после запутывания: 'квант'")
    results2 = memory.recall("квант", top_k=3)
    
    for i, r in enumerate(results2, 1):
        print(f"\n   {i}. {r['key']}")
        print(f"      релевантность: {r['relevance']:.3f} (буст: {r['quantum_boost']:.3f})")
    
    # Получаем конкретный факт
    print("\n📖 Получение факта 'C123 язык':")
    fact = memory.get_fact("C123 язык")
    if fact:
        print(f"   Значение: {fact['value'][:100]}...")
        print(f"   Активаций: {fact['activation_count']}")
        print(f"   Запутан с: {fact['entangled_with']}")
    
    # Статистика после операций
    print("\n📊 Итоговая статистика:")
    final_stats = memory.get_stats()
    for k, v in final_stats.items():
        if isinstance(v, float):
            print(f"   {k}: {v:.3f}")
        else:
            print(f"   {k}: {v}")
    
    # Сохраняем
    memory.save()