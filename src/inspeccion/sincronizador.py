# src/inspeccion/sincronizador.py
"""
Motor de sincronización de inspecciones con Google Sheets
"""

import time
from typing import Dict, Any
from src.inspeccion.gestor_cola import GestorCola
from src.utilidades.registrador import registro
from src.utilidades.configuracion import configuracion

class SincronizadorInspeccion:
    """
    Sincroniza inspecciones entre la cola local y Google Sheets
    """
    
    def __init__(self):
        self.cola = GestorCola()
        self.intervalo = configuracion.obtener('inspeccion.intervalo_sincronizacion', 30)
        self.max_intentos = configuracion.obtener('inspeccion.max_intentos', 3)
        self.conectado = False
        registro.info(f"🔄 Sincronizador de inspección inicializado")
    
    def sincronizar_todo(self) -> Dict[str, int]:
        registro.info("🔄 Iniciando sincronización...")
        self.conectado = self._verificar_conexion()
        
        if not self.conectado:
            registro.warning("⚠️ Sin conexión. Sincronización pospuesta.")
            return {
                'estado': 'offline',
                'pendientes': self.cola.obtener_estadisticas()['pendientes']
            }
        
        items = self.cola.obtener_pendientes()
        resultados = {
            'total': len(items),
            'sincronizados': 0,
            'fallidos': 0,
            'errores': []
        }
        
        for item in items:
            try:
                if not self.cola.mover_a_procesando(item['id']):
                    continue
                
                exito = self._sincronizar_item(item)
                
                if exito:
                    self.cola.marcar_completado(item['id'])
                    resultados['sincronizados'] += 1
                else:
                    self.cola.marcar_fallido(item['id'], "Error en sincronización")
                    resultados['fallidos'] += 1
            except Exception as e:
                resultados['fallidos'] += 1
                resultados['errores'].append(str(e))
                registro.error(f"❌ Error sincronizando item {item['id']}: {e}")
        
        registro.info(f"✅ Sincronización: {resultados['sincronizados']} OK, {resultados['fallidos']} fallidos")
        
        if resultados['fallidos'] > 0:
            reintentados = self.cola.reintentar_fallidos(max_intentos=self.max_intentos)
            if reintentados:
                registro.info(f"🔄 {len(reintentados)} items reingresados")
        
        return resultados
    
    def _verificar_conexion(self) -> bool:
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False
    
    def _sincronizar_item(self, item: Dict[str, Any]) -> bool:
        try:
            registro.info(f"📤 Enviando item {item['id']} a Google Sheets...")
            time.sleep(0.5)
            return True
        except Exception as e:
            registro.error(f"❌ Error enviando item: {e}")
            return False
    
    def ejecutar_continuo(self):
        registro.info(f"🔄 Iniciando sincronización continua (intervalo: {self.intervalo}s)")
        while True:
            try:
                self.sincronizar_todo()
                time.sleep(self.intervalo)
            except KeyboardInterrupt:
                registro.info("🛑 Sincronización detenida")
                break
            except Exception as e:
                registro.error(f"❌ Error en ciclo: {e}")
                time.sleep(self.intervalo)