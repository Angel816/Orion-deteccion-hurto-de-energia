# src/utilidades/configuracion.py
"""
Gestión de configuración centralizada para Orion
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Configuracion:
    """
    Gestor de configuración del sistema
    """
    
    _instancia = None
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia
    
    def __init__(self):
        if self._inicializado:
            return
        
        self._inicializado = True
        self.entorno = os.getenv('ENTORNO', 'desarrollo')
        self.directorio_base = Path(__file__).parent.parent.parent
        
        self._cargar_configuracion()
    
    def _cargar_configuracion(self):
        archivo_config = self.directorio_base / 'configuracion' / f'{self.entorno}.yaml'
        if archivo_config.exists():
            with open(archivo_config, 'r', encoding='utf-8') as f:
                self.datos = yaml.safe_load(f)
        else:
            self.datos = {}
        
        self._cargar_variables_entorno()
    
    def _cargar_variables_entorno(self):
        mapeo = {
            'NIVEL_LOG': 'registro.nivel',
            'RUTA_DATOS_BRUTOS': 'datos.ruta_brutos',
            'RUTA_DATOS_PROCESADOS': 'datos.ruta_procesados',
            'RUTA_MODELOS': 'modelos.ruta',
            'HOST_API': 'api.host',
            'PUERTO_API': 'api.puerto'
        }
        
        for var_env, ruta_config in mapeo.items():
            valor = os.getenv(var_env)
            if valor is not None:
                self._establecer_anidado(ruta_config, valor)
    
    def _establecer_anidado(self, ruta, valor):
        claves = ruta.split('.')
        destino = self.datos
        for clave in claves[:-1]:
            if clave not in destino:
                destino[clave] = {}
            destino = destino[clave]
        destino[claves[-1]] = valor
    
    def obtener(self, clave, valor_por_defecto=None):
        claves = clave.split('.')
        valor = self.datos
        for k in claves:
            if isinstance(valor, dict):
                valor = valor.get(k)
                if valor is None:
                    return valor_por_defecto
            else:
                return valor_por_defecto
        return valor

configuracion = Configuracion()