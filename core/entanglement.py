"""
entanglement.py - Управление запутанностью между квантовыми нейронами

Создает и управляет квантовыми связями между нейронами.
Запутанность - это аналог синапсов в нейронной сети.
"""

import numpy as np
import json
import time
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict

from .neuron import QuantumNeuron

class EntanglementGraph:
    """
    Граф запутанности всей сети
    
    Атрибуты:
        nodes (Dict[str, QuantumNeuron]): все нейроны (хеш -> нейрон)
        edges (Dict[Tuple[str, str], float]): сила запутанности между парами
        clusters (Dict[str, Set[str]]): кластеры сильно запутанных нейронов
        last_update (float): время последнего обновления
    """
    
    def __init__(self):
        self.nodes: Dict[str, QuantumNeuron] = {}
        self.edges: Dict[Tuple[str, str], float] = {}
        self.clusters: Dict[str, Set[str]] = {}
        self.last_update = time.time()
        
        # Статистика
        self.stats = {
            'total_entanglements': 0,
            'max_cluster_size': 0,
            'avg_entanglement_strength': 0.0,
            'cluster_count': 0
        }
        
    def add_neuron(self, neuron: QuantumNeuron) -> None:
        """
        Добавляет нейрон в граф
        
        Args:
            neuron: квантовый нейрон
        """
        self.nodes[neuron.hash] = neuron
        
    def remove_neuron(self, neuron_hash: str) -> None:
        """
        Удаляет нейрон из графа и все его связи
        
        Args:
            neuron_hash: хеш нейрона
        """
        if neuron_hash not in self.nodes:
            return
        
        # Удаляем все ребра с этим нейроном
        edges_to_remove = []
        for (h1, h2) in list(self.edges.keys()):
            if h1 == neuron_hash or h2 == neuron_hash:
                edges_to_remove.append((h1, h2))
        
        for edge in edges_to_remove:
            del self.edges[edge]
        
        # Удаляем из кластеров
        for cluster_id, members in list(self.clusters.items()):
            if neuron_hash in members:
                members.remove(neuron_hash)
                if not members:
                    del self.clusters[cluster_id]
        
        # Удаляем нейрон
        del self.nodes[neuron_hash]
        
    def create_entanglement(self, 
                           neuron1: QuantumNeuron, 
                           neuron2: QuantumNeuron,
                           strength: float = 1.0,
                           method: str = 'auto') -> bool:
        """
        Создает запутанность между двумя нейронами
        
        Args:
            neuron1: первый нейрон
            neuron2: второй нейрон
            strength: сила запутанности (0-1)
            method: метод создания ('bell', 'partial', 'auto')
            
        Returns:
            bool: успешно ли создана запутанность
        """
        if neuron1.hash == neuron2.hash:
            return False
        
        # Проверяем, не существуют ли уже
        edge_key = self._get_edge_key(neuron1.hash, neuron2.hash)
        if edge_key in self.edges:
            return False
        
        # Создаем запутанность через нейроны
        success = neuron1.entangle_with(neuron2, strength, method)
        
        if success:
            # Сохраняем в граф
            self.edges[edge_key] = strength
            
            # Обновляем статистику
            self.stats['total_entanglements'] += 1
            
            # Обновляем кластеры
            self._update_clusters(neuron1.hash, neuron2.hash, strength)
            
            # Обновляем среднюю силу
            self._update_avg_strength()
            
        return success
    
    def _get_edge_key(self, h1: str, h2: str) -> Tuple[str, str]:
        """Возвращает нормализованный ключ для ребра"""
        return (h1, h2) if h1 < h2 else (h2, h1)
    
    def get_entanglement_strength(self, h1: str, h2: str) -> float:
        """Возвращает силу запутанности между нейронами"""
        edge_key = self._get_edge_key(h1, h2)
        return self.edges.get(edge_key, 0.0)
    
    def _update_clusters(self, h1: str, h2: str, strength: float) -> None:
        """
        Обновляет кластеры запутанности
        
        Кластер - это множество нейронов, связанных сильными связями
        """
        # Ищем кластеры, содержащие h1 или h2
        cluster1 = None
        cluster2 = None
        
        for cid, members in self.clusters.items():
            if h1 in members:
                cluster1 = cid
            if h2 in members:
                cluster2 = cid
        
        # Если оба уже в одном кластере - ничего не делаем
        if cluster1 and cluster2 and cluster1 == cluster2:
            return
        
        # Если сила маленькая - не объединяем
        if strength < 0.5:
            return
        
        # Объединяем кластеры или создаем новый
        if cluster1 and cluster2:
            # Объединяем два кластера
            self.clusters[cluster1].update(self.clusters[cluster2])
            del self.clusters[cluster2]
            new_cluster = cluster1
        elif cluster1:
            # Добавляем h2 в кластер cluster1
            self.clusters[cluster1].add(h2)
            new_cluster = cluster1
        elif cluster2:
            # Добавляем h1 в кластер cluster2
            self.clusters[cluster2].add(h1)
            new_cluster = cluster2
        else:
            # Создаем новый кластер
            cluster_id = f"cluster_{len(self.clusters)}_{int(time.time())}"
            self.clusters[cluster_id] = {h1, h2}
            new_cluster = cluster_id
        
        # Обновляем статистику кластеров
        if new_cluster:
            cluster_size = len(self.clusters[new_cluster])
            self.stats['max_cluster_size'] = max(
                self.stats['max_cluster_size'], 
                cluster_size
            )
            self.stats['cluster_count'] = len(self.clusters)
    
    def _update_avg_strength(self) -> None:
        """Обновляет среднюю силу запутанности"""
        if self.edges:
            total = sum(self.edges.values())
            self.stats['avg_entanglement_strength'] = total / len(self.edges)
    
    def get_entangled_neighbors(self, neuron_hash: str, 
                                min_strength: float = 0.1) -> List[Tuple[str, float]]:
        """
        Возвращает всех соседей нейрона с силой связи
        
        Args:
            neuron_hash: хеш нейрона
            min_strength: минимальная сила связи
            
        Returns:
            List[(neuron_hash, strength)]
        """
        neighbors = []
        
        for (h1, h2), strength in self.edges.items():
            if strength < min_strength:
                continue
                
            if h1 == neuron_hash:
                neighbors.append((h2, strength))
            elif h2 == neuron_hash:
                neighbors.append((h1, strength))
        
        # Сортируем по убыванию силы
        neighbors.sort(key=lambda x: x[1], reverse=True)
        return neighbors
    
    def find_path(self, start_hash: str, target_hash: str, 
                 max_depth: int = 5) -> List[str]:
        """
        Ищет путь через запутанности между нейронами
        
        Args:
            start_hash: начальный нейрон
            target_hash: целевой нейрон
            max_depth: максимальная глубина поиска
            
        Returns:
            List[str]: путь (включая start и target) или пустой список
        """
        if start_hash == target_hash:
            return [start_hash]
        
        if start_hash not in self.nodes or target_hash not in self.nodes:
            return []
        
        visited = {start_hash}
        queue = [(start_hash, [start_hash])]
        
        while queue and len(visited) < max_depth * 10:
            current, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            for neighbor, _ in self.get_entangled_neighbors(current):
                if neighbor == target_hash:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return []
    
    def get_cluster(self, neuron_hash: str) -> Set[str]:
        """
        Возвращает кластер, содержащий нейрон
        
        Args:
            neuron_hash: хеш нейрона
            
        Returns:
            Set[str]: множество нейронов в кластере
        """
        for members in self.clusters.values():
            if neuron_hash in members:
                return members
        return {neuron_hash}
    
    def measure_cluster_coherence(self, cluster_id: str) -> float:
        """
        Измеряет когерентность кластера
        
        Чем выше значение, тем сильнее связаны нейроны в кластере
        
        Args:
            cluster_id: ID кластера
            
        Returns:
            float: когерентность (0-1)
        """
        if cluster_id not in self.clusters:
            return 0.0
        
        members = self.clusters[cluster_id]
        if len(members) < 2:
            return 1.0
        
        # Считаем среднюю силу связей внутри кластера
        total_strength = 0.0
        edge_count = 0
        
        for h1 in members:
            for h2 in members:
                if h1 >= h2:
                    continue
                strength = self.get_entanglement_strength(h1, h2)
                if strength > 0:
                    total_strength += strength
                    edge_count += 1
        
        if edge_count == 0:
            return 0.0
        
        # Нормализуем на количество возможных связей
        max_edges = len(members) * (len(members) - 1) / 2
        coherence = (total_strength / edge_count) * (edge_count / max_edges)
        
        return coherence
    
    def decay_old_entanglements(self, max_age_seconds: float = 3600) -> int:
        """
        Уменьшает силу старых запутанностей (забывание)
        
        Args:
            max_age_seconds: максимальный возраст в секундах
            
        Returns:
            int: количество удаленных связей
        """
        current_time = time.time()
        removed = 0
        
        edges_to_remove = []
        
        for (h1, h2), strength in list(self.edges.items()):
            # Получаем нейроны
            neuron1 = self.nodes.get(h1)
            neuron2 = self.nodes.get(h2)
            
            if not neuron1 or not neuron2:
                edges_to_remove.append((h1, h2))
                continue
            
            # Вычисляем возраст последней активации
            age1 = current_time - neuron1.last_active
            age2 = current_time - neuron2.last_active
            max_age = max(age1, age2)
            
            if max_age > max_age_seconds:
                # Слишком старые связи удаляем
                edges_to_remove.append((h1, h2))
                removed += 1
            else:
                # Ослабляем связь со временем
                decay_factor = np.exp(-max_age / max_age_seconds)
                new_strength = strength * decay_factor
                
                if new_strength < 0.1:
                    edges_to_remove.append((h1, h2))
                    removed += 1
                else:
                    self.edges[(h1, h2)] = new_strength
        
        # Удаляем старые связи
        for edge in edges_to_remove:
            del self.edges[edge]
        
        # Обновляем кластеры
        self._rebuild_clusters()
        
        self.last_update = current_time
        return removed
    
    def _rebuild_clusters(self) -> None:
        """Перестраивает кластеры на основе текущих связей"""
        self.clusters.clear()
        
        # Строим граф сильных связей (>0.5)
        strong_edges = []
        for (h1, h2), strength in self.edges.items():
            if strength > 0.5:
                strong_edges.append((h1, h2))
        
        if not strong_edges:
            return
        
        # Кластеризация через BFS
        visited = set()
        cluster_id = 0
        
        for h1, h2 in strong_edges:
            for h in [h1, h2]:
                if h not in visited:
                    # Новый кластер
                    cluster = set()
                    queue = [h]
                    
                    while queue:
                        current = queue.pop(0)
                        if current in visited:
                            continue
                        
                        visited.add(current)
                        cluster.add(current)
                        
                        # Ищем соседей по сильным связям
                        for (nh1, nh2), strength in self.edges.items():
                            if strength <= 0.5:
                                continue
                                
                            if nh1 == current and nh2 not in visited:
                                queue.append(nh2)
                            elif nh2 == current and nh1 not in visited:
                                queue.append(nh1)
                    
                    if len(cluster) > 1:
                        self.clusters[f"cluster_{cluster_id}"] = cluster
                        cluster_id += 1
        
        self.stats['cluster_count'] = len(self.clusters)
    
    def get_entanglement_map(self) -> Dict[str, Any]:
        """
        Возвращает карту запутанности для визуализации
        
        Returns:
            Dict с данными для графа
        """
        nodes_data = []
        edges_data = []
        
        # Узлы
        for h, neuron in self.nodes.items():
            nodes_data.append({
                'id': h[:8],  # короткий ID
                'full_hash': h,
                'key': neuron.key[:20] + '...' if len(neuron.key) > 20 else neuron.key,
                'activation_count': neuron.activation_count,
                'cluster': self._get_node_cluster(h)
            })
        
        # Ребра
        for (h1, h2), strength in self.edges.items():
            edges_data.append({
                'source': h1[:8],
                'target': h2[:8],
                'strength': strength,
                'width': strength * 3
            })
        
        return {
            'nodes': nodes_data,
            'edges': edges_data,
            'stats': self.stats,
            'clusters': [
                {
                    'id': cid,
                    'size': len(members),
                    'coherence': self.measure_cluster_coherence(cid)
                }
                for cid, members in self.clusters.items()
            ]
        }
    
    def _get_node_cluster(self, neuron_hash: str) -> Optional[str]:
        """Возвращает ID кластера нейрона"""
        for cid, members in self.clusters.items():
            if neuron_hash in members:
                return cid
        return None
    
    def save(self, filepath: str) -> None:
        """Сохраняет граф в файл"""
        data = {
            'edges': [(h1, h2, strength) for (h1, h2), strength in self.edges.items()],
            'stats': self.stats,
            'last_update': self.last_update
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self, filepath: str, neurons: Dict[str, QuantumNeuron]) -> None:
        """
        Загружает граф из файла
        
        Args:
            filepath: путь к файлу
            neurons: словарь нейронов для восстановления связей
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.nodes = neurons
            self.edges.clear()
            
            for h1, h2, strength in data['edges']:
                self.edges[(h1, h2)] = strength
            
            self.stats = data['stats']
            self.last_update = data['last_update']
            
            # Перестраиваем кластеры
            self._rebuild_clusters()
            
        except FileNotFoundError:
            pass
    
    def __str__(self) -> str:
        return (f"EntanglementGraph("
                f"нейронов:{len(self.nodes)}, "
                f"связей:{len(self.edges)}, "
                f"кластеров:{len(self.clusters)})")


# ===== КВАНТОВЫЙ РЕЗОНАНС =====

class QuantumResonance:
    """
    Квантовый резонанс между нейронами
    
    Резонанс определяет, насколько сильно нейроны влияют друг на друга
    """
    
    def __init__(self, graph: EntanglementGraph):
        self.graph = graph
        self.resonance_field = {}  # neuron_hash -> поле резонанса
        
    def calculate_resonance(self, h1: str, h2: str) -> float:
        """
        Вычисляет резонанс между двумя нейронами
        
        Резонанс учитывает:
        - Прямую запутанность
        - Косвенные связи через другие нейроны
        - Квантовое перекрытие состояний
        """
        if h1 not in self.graph.nodes or h2 not in self.graph.nodes:
            return 0.0
        
        n1 = self.graph.nodes[h1]
        n2 = self.graph.nodes[h2]
        
        # Прямая запутанность
        direct = self.graph.get_entanglement_strength(h1, h2)
        
        # Квантовое перекрытие
        quantum = n1.get_resonance_with(n2)
        
        # Косвенные связи (через общих соседей)
        indirect = self._calculate_indirect_resonance(h1, h2)
        
        # Комбинируем
        resonance = 0.5 * quantum + 0.3 * direct + 0.2 * indirect
        
        return resonance
    
    def _calculate_indirect_resonance(self, h1: str, h2: str) -> float:
        """Вычисляет резонанс через общих соседей"""
        neighbors1 = set(h for h, _ in self.graph.get_entangled_neighbors(h1))
        neighbors2 = set(h for h, _ in self.graph.get_entangled_neighbors(h2))
        
        common = neighbors1 & neighbors2
        
        if not common:
            return 0.0
        
        total = 0.0
        for h in common:
            s1 = self.graph.get_entanglement_strength(h1, h)
            s2 = self.graph.get_entanglement_strength(h2, h)
            total += (s1 * s2)
        
        return total / len(common)
    
    def update_resonance_field(self, neuron_hash: str) -> None:
        """
        Обновляет поле резонанса для нейрона
        
        Поле резонанса - это влияние нейрона на всю сеть
        """
        if neuron_hash not in self.graph.nodes:
            return
        
        field = {}
        neuron = self.graph.nodes[neuron_hash]
        
        for h, other in self.graph.nodes.items():
            if h == neuron_hash:
                continue
            
            resonance = self.calculate_resonance(neuron_hash, h)
            if resonance > 0.1:
                field[h] = resonance
        
        self.resonance_field[neuron_hash] = field
    
    def get_most_resonant(self, seed_hash: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Возвращает нейроны с наибольшим резонансом с seed
        
        Args:
            seed_hash: начальный нейрон
            top_k: количество результатов
            
        Returns:
            List[(neuron_hash, resonance)]
        """
        if seed_hash not in self.graph.nodes:
            return []
        
        resonances = []
        for h in self.graph.nodes:
            if h == seed_hash:
                continue
            
            resonance = self.calculate_resonance(seed_hash, h)
            resonances.append((h, resonance))
        
        resonances.sort(key=lambda x: x[1], reverse=True)
        return resonances[:top_k]


# ===== ТЕСТЫ =====

if __name__ == "__main__":
    print("🌀 Тестирование EntanglementGraph\n")
    
    # Создаем граф
    graph = EntanglementGraph()
    
    # Создаем тестовые нейроны
    from .neuron import QuantumNeuron
    
    neurons = []
    for i, (key, value) in enumerate([
        ("квантовая запутанность", "Эффект мгновенной связи"),
        ("нейронная сеть", "Математическая модель мозга"),
        ("искусственный интеллект", "Имитация интеллекта"),
        ("квантовый компьютер", "Компьютер на кубитах"),
        ("машинное обучение", "Обучение на данных")
    ]):
        n = QuantumNeuron(key, value, creator="test")
        graph.add_neuron(n)
        neurons.append(n)
        print(f"➕ Добавлен нейрон: {n.key[:20]}...")
    
    print(f"\n📊 Граф после добавления: {graph}")
    
    # Создаем запутанности
    print("\n🔗 Создание запутанностей:")
    
    pairs = [
        (neurons[0], neurons[1], 0.9),  # сильная
        (neurons[1], neurons[2], 0.8),  # сильная
        (neurons[2], neurons[3], 0.6),  # средняя
        (neurons[3], neurons[4], 0.4),  # слабая
        (neurons[0], neurons[4], 0.3),  # слабая
    ]
    
    for n1, n2, strength in pairs:
        success = graph.create_entanglement(n1, n2, strength, 'partial')
        status = "✅" if success else "❌"
        print(f"   {status} {n1.key[:15]}... ↔ {n2.key[:15]}... ({strength})")
    
    print(f"\n📊 Статистика:")
    print(f"   Всего связей: {graph.stats['total_entanglements']}")
    print(f"   Средняя сила: {graph.stats['avg_entanglement_strength']:.3f}")
    print(f"   Кластеров: {graph.stats['cluster_count']}")
    
    # Тестируем поиск соседей
    print(f"\n🔍 Соседи нейрона '{neurons[0].key[:15]}...':")
    neighbors = graph.get_entangled_neighbors(neurons[0].hash)
    for h, strength in neighbors:
        neighbor = graph.nodes[h]
        print(f"   → {neighbor.key[:20]}... ({strength:.3f})")
    
    # Тестируем поиск пути
    print(f"\n🛣️ Путь от '{neurons[0].key[:15]}...' к '{neurons[4].key[:15]}...':")
    path = graph.find_path(neurons[0].hash, neurons[4].hash)
    if path:
        for i, h in enumerate(path):
            neuron = graph.nodes[h]
            arrow = " → " if i < len(path)-1 else ""
            print(f"   {i+1}. {neuron.key[:20]}...{arrow}")
    else:
        print("   Путь не найден")
    
    # Тестируем резонанс
    print(f"\n⚡ Резонанс с нейроном '{neurons[0].key[:15]}...':")
    resonance = QuantumResonance(graph)
    resonant = resonance.get_most_resonant(neurons[0].hash, top_k=3)
    for h, r in resonant:
        neuron = graph.nodes[h]
        print(f"   {neuron.key[:20]}...: {r:.3f}")
    
    # Карта для визуализации
    print(f"\n🗺️ Карта запутанности готова для визуализации")
    viz_map = graph.get_entanglement_map()
    print(f"   Узлов для визуализации: {len(viz_map['nodes'])}")
    print(f"   Связей для визуализации: {len(viz_map['edges'])}")