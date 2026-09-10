# src/inspeccion/gestor_cola.py
"""
Gestión de cola de inspección con persistencia local
Zona horaria: Perú (UTC-5)
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from src.utilidades.registrador import registro
from src.utilidades.configuracion import configuracion
from src.utilidades.tiempo import ahora_peru, iso_peru


class GestorCola:
    """
    Gestiona la cola de inspecciones con persistencia local
    """
    
    def __init__(self):
        self.base_dir = Path(configuracion.obtener('datos.ruta_inspeccion', 'datos/inspeccion/cola'))
        self.directorios = {
            'pendientes': self.base_dir / 'pendientes',
            'procesando': self.base_dir / 'procesando',
            'fallidos': self.base_dir / 'fallidos',
            'completados': self.base_dir / 'completados'
        }
        
        for dir_path in self.directorios.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        registro.info(f"📂 Gestor de cola inicializado")
    
    def agregar(self, id_cliente: str, inspector_id: str, 
                datos: Dict[str, Any]) -> str:
        """Agrega un item a la cola"""
        item_id = str(uuid.uuid4())
        fecha_actual = iso_peru()  # ← HORA PERÚ
        
        item = {
            'id': item_id,
            'id_cliente': id_cliente,
            'inspector_id': inspector_id,
            'datos': datos,
            'estado': 'pendiente',
            'creado_en': fecha_actual,
            'actualizado_en': fecha_actual,
            'intentos': 0,
            'error': None
        }
        
        archivo = self.directorios['pendientes'] / f"{item_id}.json"
        with open(archivo, 'w', encoding='utf-8') as f:
            json.dump(item, f, indent=2, default=str, ensure_ascii=False)
        
        registro.info(f"📥 Item agregado a la cola: {item_id}")
        return item_id
    
    def obtener_pendientes(self, limite: int = 100) -> List[Dict]:
        """Obtiene items pendientes"""
        items = []
        archivos = sorted(self.directorios['pendientes'].glob('*.json'))[:limite]
        
        for archivo in archivos:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    items.append(json.load(f))
            except Exception as e:
                registro.error(f"❌ Error cargando item {archivo}: {e}")
        
        return items
    
    def obtener_fallidos(self, limite: int = 100) -> List[Dict]:
        """Obtiene items fallidos"""
        items = []
        archivos = sorted(self.directorios['fallidos'].glob('*.json'))[:limite]
        
        for archivo in archivos:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    items.append(json.load(f))
            except Exception as e:
                registro.error(f"❌ Error cargando item {archivo}: {e}")
        
        return items
    
    def mover_a_procesando(self, item_id: str) -> bool:
        """Mueve un item a procesando"""
        origen = self.directorios['pendientes'] / f"{item_id}.json"
        if not origen.exists():
            origen = self.directorios['fallidos'] / f"{item_id}.json"
            if not origen.exists():
                registro.warning(f"⚠️ Item {item_id} no encontrado")
                return False
        
        try:
            with open(origen, 'r', encoding='utf-8') as f:
                item = json.load(f)
            
            item['estado'] = 'procesando'
            item['actualizado_en'] = iso_peru()  # ← HORA PERÚ
            
            destino = self.directorios['procesando'] / f"{item_id}.json"
            with open(destino, 'w', encoding='utf-8') as f:
                json.dump(item, f, indent=2, default=str, ensure_ascii=False)
            
            origen.unlink()
            return True
        except Exception as e:
            registro.error(f"❌ Error moviendo item {item_id}: {e}")
            return False
    
    def marcar_completado(self, item_id: str) -> bool:
        """Marca un item como completado"""
        origen = self.directorios['procesando'] / f"{item_id}.json"
        if not origen.exists():
            registro.warning(f"⚠️ Item {item_id} no encontrado")
            return False
        
        try:
            with open(origen, 'r', encoding='utf-8') as f:
                item = json.load(f)
            
            item['estado'] = 'completado'
            item['actualizado_en'] = iso_peru()  # ← HORA PERÚ
            
            destino = self.directorios['completados'] / f"{item_id}.json"
            with open(destino, 'w', encoding='utf-8') as f:
                json.dump(item, f, indent=2, default=str, ensure_ascii=False)
            
            origen.unlink()
            registro.info(f"✅ Item {item_id} completado")
            return True
        except Exception as e:
            registro.error(f"❌ Error completando item {item_id}: {e}")
            return False
    
    def marcar_fallido(self, item_id: str, error: str) -> bool:
        """Marca un item como fallido"""
        origen = None
        for dir_path in self.directorios.values():
            test = dir_path / f"{item_id}.json"
            if test.exists():
                origen = test
                break
        
        if not origen:
            registro.warning(f"⚠️ Item {item_id} no encontrado")
            return False
        
        try:
            with open(origen, 'r', encoding='utf-8') as f:
                item = json.load(f)
            
            item['estado'] = 'fallido'
            item['intentos'] = item.get('intentos', 0) + 1
            item['error'] = error
            item['actualizado_en'] = iso_peru()  # ← HORA PERÚ
            
            destino = self.directorios['fallidos'] / f"{item_id}.json"
            with open(destino, 'w', encoding='utf-8') as f:
                json.dump(item, f, indent=2, default=str, ensure_ascii=False)
            
            origen.unlink()
            registro.warning(f"⚠️ Item {item_id} marcado como fallido")
            return True
        except Exception as e:
            registro.error(f"❌ Error marcando item {item_id} como fallido: {e}")
            return False
    
    def reintentar_fallidos(self, max_intentos: int = 3) -> List[str]:
        """Reintenta items fallidos"""
        items = self.obtener_fallidos()
        reintentados = []
        
        for item in items:
            if item.get('intentos', 0) >= max_intentos:
                registro.warning(f"⚠️ Item {item['id']} excedió intentos máximos")
                continue
            
            origen = self.directorios['fallidos'] / f"{item['id']}.json"
            item['estado'] = 'pendiente'
            item['actualizado_en'] = iso_peru()  # ← HORA PERÚ
            
            destino = self.directorios['pendientes'] / f"{item['id']}.json"
            with open(destino, 'w', encoding='utf-8') as f:
                json.dump(item, f, indent=2, default=str, ensure_ascii=False)
            
            origen.unlink()
            reintentados.append(item['id'])
            registro.info(f"🔄 Item {item['id']} reingresado a la cola")
        
        return reintentados
    
    def obtener_estadisticas(self) -> Dict[str, int]:
        """Retorna estadísticas de la cola"""
        return {
            'pendientes': len(list(self.directorios['pendientes'].glob('*.json'))),
            'procesando': len(list(self.directorios['procesando'].glob('*.json'))),
            'fallidos': len(list(self.directorios['fallidos'].glob('*.json'))),
            'completados': len(list(self.directorios['completados'].glob('*.json')))
        }
    
    def limpiar_completados(self, dias: int = 30) -> int:
        """Limpia items completados antiguos"""
        import time
        corte = time.time() - (dias * 24 * 60 * 60)
        eliminados = 0
        
        for archivo in self.directorios['completados'].glob('*.json'):
            if archivo.stat().st_mtime < corte:
                archivo.unlink()
                eliminados += 1
        
        return eliminados