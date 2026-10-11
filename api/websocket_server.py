"""
websocket_server.py - WebSocket сервер для квантовой памяти

Соединяет фронтенд с квантовой памятью.
Поддерживает все команды из твоего интерфейса.
"""

import asyncio
import json
import websockets
import threading
import time
from typing import Set, Dict, Any
import sys
import os

# Добавляем корневую папку в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from memory.quantum_memory import QuantumMemory

class QuantumWebSocketServer:
    """
    WebSocket сервер для квантовой памяти
    
    Поддерживает:
    - Поиск фактов (recall)
    - Запоминание новых фактов (remember)
    - Запутывание фактов (entangle)
    - Статистику (stats)
    - Список фактов (facts)
    """
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.memory = QuantumMemory("quantum_memory.json")
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.server = None
        
    async def start(self):
        """Запускает WebSocket сервер"""
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        print(f"🔌 WebSocket сервер запущен на ws://{self.host}:{self.port}")
        
        # Запускаем фоновые задачи
        asyncio.create_task(self.broadcast_stats())
        
    async def handle_client(self, websocket):
        """
        Обрабатывает подключение клиента
        """
        self.clients.add(websocket)
        client_id = id(websocket)
        print(f"✅ Клиент {client_id} подключился (всего: {len(self.clients)})")
        
        try:
            # Отправляем приветственное сообщение
            await websocket.send(json.dumps({
                "type": "system",
                "message": "🔮 Квантовая память готова"
            }))
            
            # Отправляем статистику при подключении
            await self.send_stats(websocket)
            
            # Обрабатываем сообщения
            async for message in websocket:
                await self.process_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            print(f"❌ Клиент {client_id} отключился")
        finally:
            self.clients.remove(websocket)
            print(f"📊 Клиентов осталось: {len(self.clients)}")
    
    async def process_message(self, websocket, message: str):
        """
        Обрабатывает входящее сообщение
        """
        try:
            data = json.loads(message)
            msg_type = data.get("type", "unknown")
            content = data.get("text", "")
            
            print(f"📨 Получено: {msg_type} - {content[:50]}...")
            
            # Обработка разных типов сообщений
            if msg_type == "message":
                # Обычное сообщение - интерпретируем как команду
                response = await self.handle_command(content)
                await websocket.send(json.dumps({
                    "type": "reply",
                    "text": response
                }))
                
            elif msg_type == "command":
                # Явная команда
                response = await self.handle_command(content)
                await websocket.send(json.dumps({
                    "type": "reply",
                    "text": response
                }))
                
            elif msg_type == "ping":
                # Проверка соединения
                await websocket.send(json.dumps({
                    "type": "pong",
                    "time": time.time()
                }))
                
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "text": f"Неизвестный тип сообщения: {msg_type}"
                }))
                
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "text": "Неверный формат JSON"
            }))
        except Exception as e:
            await websocket.send(json.dumps({
                "type": "error",
                "text": f"Ошибка: {str(e)}"
            }))
    
    async def handle_command(self, text: str) -> str:
        """
        Обрабатывает текстовые команды (как в твоём интерфейсе)
        """
        cmd = text.lower().strip()
        
        # Статистика
        if cmd == "/stats":
            stats = self.memory.get_stats()
            return (
                f"📊 **КВАНТОВАЯ СТАТИСТИКА**\n\n"
                f"🧠 Фактов: {stats['total_facts']}\n"
                f"🌀 Запутанностей: {stats['total_entanglements']}\n"
                f"🔍 Поисков: {stats['total_searches']}\n"
                f"⚡ Среднее время поиска: {stats['avg_search_time_ms']:.2f}мс\n"
                f"📈 Средняя релевантность: {stats['avg_relevance']:.2f}\n"
                f"🌟 Кластеров: {stats['clusters']}\n"
                f"📊 Макс. размер кластера: {stats['max_cluster_size']}\n"
                f"📏 Памяти: {stats['memory_usage'] / 1024:.1f} KB"
            )
        
        # Список фактов
        elif cmd == "/facts":
            facts = self.memory.get_all_facts(limit=20)
            if not facts:
                return "🧠 Память пуста"
            
            result = "🧠 **ФАКТЫ В ПАМЯТИ**\n\n"
            for f in facts:
                entangled = "🌀" if f['entangled_count'] > 0 else "  "
                result += f"{entangled} **{f['key']}** (акт:{f['activation_count']})\n"
                result += f"   {f['value'][:60]}...\n"
            return result
        
        # Список запутанностей
        elif cmd == "/entanglements":
            viz_map = self.memory.get_entanglement_map()
            if not viz_map['edges']:
                return "⚛️ Нет активных запутанностей"
            
            result = "⚛️ **ЗАПУТАННЫЕ ПАРЫ**\n\n"
            for edge in viz_map['edges'][:10]:
                result += f"   {edge['source']} ↔ {edge['target']} ({edge['strength']:.1f})\n"
            
            if len(viz_map['edges']) > 10:
                result += f"\n   ... и ещё {len(viz_map['edges']) - 10} пар"
            
            return result
        
        # Запомнить факт
        elif cmd.startswith("/remember "):
            rest = text[10:].strip()
            if "→" not in rest:
                return "❌ Формат: /remember вопрос → ответ"
            
            key, value = rest.split("→", 1)
            key = key.strip()
            value = value.strip()
            
            self.memory.remember(key, value)
            return f"✅ Запомнил: **{key}**"
        
        # Запутать факты
        elif cmd.startswith("/entangle "):
            rest = text[10:].strip()
            if "↔" not in rest and "->" not in rest:
                return "❌ Формат: /entangle факт1 ↔ факт2"
            
            sep = "↔" if "↔" in rest else "->"
            k1, k2 = [x.strip() for x in rest.split(sep, 1)]
            
            if self.memory.entangle_facts(k1, k2):
                return f"🌀 Запутаны: **{k1}** ↔ **{k2}**"
            else:
                return "❌ Не удалось запутать (факты не найдены или уже запутаны)"
        
        # Измерить факт
        elif cmd.startswith("/measure "):
            key = text[9:].strip()
            fact = self.memory.get_fact(key)
            if fact:
                return (
                    f"📊 Измерен факт **{key}**:\n"
                    f"   Значение: {fact['value'][:100]}...\n"
                    f"   Активаций: {fact['activation_count']}\n"
                    f"   Запутан с: {', '.join(fact['entangled_with']) or 'нет'}"
                )
            return f"❌ Факт '{key}' не найден"
        
        # Поиск в Wikipedia (заглушка)
        elif cmd.startswith("/search "):
            query = text[8:].strip()
            return f"🌐 Поиск в Wikipedia для '{query}' (будет добавлен позже)"
        
        # Помощь
        elif cmd == "/help":
            return (
                "🆘 **КВАНТОВЫЕ КОМАНДЫ**\n\n"
                "• `/stats` — статистика памяти\n"
                "• `/facts` — список фактов\n"
                "• `/entanglements` — список запутанностей\n"
                "• `/remember вопрос → ответ` — запомнить факт\n"
                "• `/entangle факт1 ↔ факт2` — запутать факты\n"
                "• `/measure факт` — измерить факт\n"
                "• `/search запрос` — поиск в Wikipedia\n"
                "• `/help` — это сообщение\n\n"
                "🌀 Просто напиши вопрос — будет квантовый поиск по памяти!"
            )
        
        # Обычный запрос - квантовый поиск
        else:
            results = self.memory.recall(text, top_k=3)
            
            if not results:
                return (
                    f"❓ Я не знаю ответа на этот вопрос.\n\n"
                    f"Попробуй:\n"
                    f"• `/remember {text} → твой ответ`\n"
                    f"• `/search {text}` — поиск в Wikipedia"
                )
            
            # Формируем ответ как в твоём интерфейсе
            best = results[0]
            
            # Выбираем эмодзи по релевантности
            if best['relevance'] > 0.8:
                emoji = "✅"
            elif best['relevance'] > 0.5:
                emoji = "🔄"
            else:
                emoji = "🌀"
            
            response = f"{emoji} {best['value']}"
            
            # Добавляем информацию о запутанности
            if best.get('via'):
                response += f"\n\n⚛️ *Квантовое усиление: через {best['via']}*"
            
            # Показываем альтернативы
            if len(results) > 1:
                response += "\n\n🔍 **Также найдено:**\n"
                for i, r in enumerate(results[1:], 1):
                    response += f"   • {r['key']} ({r['relevance']:.0%})\n"
            
            return response
    
    async def send_stats(self, websocket):
        """Отправляет статистику конкретному клиенту"""
        stats = self.memory.get_stats()
        viz_map = self.memory.get_entanglement_map()
        
        await websocket.send(json.dumps({
            "type": "stats",
            "data": stats
        }))
        
        await websocket.send(json.dumps({
            "type": "viz_map",
            "data": viz_map
        }))
    
    async def broadcast_stats(self):
        """
        Периодически рассылает статистику всем клиентам
        """
        while True:
            if self.clients:
                stats = self.memory.get_stats()
                viz_map = self.memory.get_entanglement_map()
                
                message = json.dumps({
                    "type": "update",
                    "stats": stats,
                    "viz": {
                        "nodes": len(viz_map['nodes']),
                        "edges": len(viz_map['edges']),
                        "clusters": len(viz_map['clusters'])
                    }
                })
                
                # Рассылаем всем клиентам
                await asyncio.gather(
                    *[client.send(message) for client in self.clients],
                    return_exceptions=True
                )
            
            await asyncio.sleep(2)  # Каждые 2 секунды
    
    async def stop(self):
        """Останавливает сервер"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()


# ===== ЗАПУСК =====

async def main():
    """Главная функция запуска"""
    server = QuantumWebSocketServer(host="localhost", port=8765)
    
    try:
        print("=" * 50)
        print("🚀 ЗАПУСК КВАНТОВОГО WEBСОКЕТ СЕРВЕРА")
        print("=" * 50)
        print(f"📁 Память: quantum_memory.json")
        print(f"🔌 WebSocket: ws://localhost:8765")
        print(f"🌐 Для интерфейса: открыть frontend/public/index.html")
        print("=" * 50)
        print("Нажми Ctrl+C для остановки")
        print()
        
        await server.start()
        await asyncio.Future()  # Бесконечное ожидание
        
    except KeyboardInterrupt:
        print("\n⏹️ Остановка сервера...")
        await server.stop()
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())