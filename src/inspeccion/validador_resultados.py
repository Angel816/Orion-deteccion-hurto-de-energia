# src/inspeccion/validador_resultados.py
"""
Validación de resultados de inspección
"""

from typing import Dict, Tuple, List, Any
from datetime import datetime
from src.utilidades.registrador import registro

class ValidadorResultados:
    """
    Valida resultados de inspección antes de integrarlos al sistema
    """
    
    def __init__(self):
        self.resultados_permitidos = ['Hurto Confirmado', 'Anomalía', 'Normal', 'Falso Positivo']
        self.tipos_permitidos = ['Bypass', 'Cable Rajado', 'Manipulación Medidor', 
                                'Conexión Clandestina', 'Auto-reconexión', 'N/A']
        registro.info("🔍 Validador de resultados inicializado")
    
    def validar(self, resultado: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        limpio = resultado.copy()
        
        requeridos = ['id_cliente', 'resultado']
        for campo in requeridos:
            if campo not in resultado or not resultado[campo]:
                return False, f"Campo requerido faltante: {campo}", {}
        
        if resultado['resultado'] not in self.resultados_permitidos:
            return False, f"Resultado inválido: {resultado['resultado']}", {}
        
        if resultado['resultado'] in ['Hurto Confirmado', 'Anomalía']:
            if 'tipo_irregularidad' not in resultado:
                return False, "Tipo de irregularidad requerido", {}
            
            if resultado['tipo_irregularidad'] not in self.tipos_permitidos:
                return False, f"Tipo inválido: {resultado['tipo_irregularidad']}", {}
            
            if 'cnr_estimado' not in resultado or resultado['cnr_estimado'] <= 0:
                return False, "CNR estimado requerido", {}
        
        limpio = self._limpiar_resultado(limpio)
        limpio['fecha_validacion'] = datetime.now().isoformat()
        limpio['validado'] = True
        
        return True, "Válido", limpio
    
    def validar_lote(self, resultados: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        validos = []
        invalidos = []
        
        for resultado in resultados:
            es_valido, mensaje, limpio = self.validar(resultado)
            if es_valido:
                validos.append(limpio)
            else:
                invalidos.append({'resultado': resultado, 'error': mensaje})
        
        registro.info(f"📊 Validación: {len(validos)} válidos, {len(invalidos)} inválidos")
        return validos, invalidos
    
    def _limpiar_resultado(self, resultado: Dict) -> Dict:
        limpio = resultado.copy()
        
        if 'fecha_inspeccion' in limpio:
            try:
                limpio['fecha_inspeccion'] = datetime.fromisoformat(limpio['fecha_inspeccion']).isoformat()
            except:
                limpio['fecha_inspeccion'] = datetime.now().isoformat()
        
        for campo in ['resultado', 'tipo_irregularidad', 'inspector']:
            if campo in limpio and limpio[campo]:
                limpio[campo] = str(limpio[campo]).strip().title()
        
        if 'cnr_estimado' in limpio:
            try:
                limpio['cnr_estimado'] = float(limpio['cnr_estimado'])
            except:
                limpio['cnr_estimado'] = 0.0
        
        mapa_label = {
            'Hurto Confirmado': 1,
            'Anomalía': 1,
            'Normal': 0,
            'Falso Positivo': 0
        }
        limpio['label'] = mapa_label.get(limpio['resultado'], 0)
        
        return limpio