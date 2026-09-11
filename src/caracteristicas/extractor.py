# src/caracteristicas/extractor.py
"""
Extracción de características CAUSALES para detección de hurto
Proyecto Orion - Zona horaria: Perú (UTC-5)

FILOSOFÍA:
-----------
Solo extraemos variables que EVIDENCIEN hurto, no estadísticas genéricas.

Categorías de evidencia:
1. EVIDENCIA FÍSICA: Alarmas del medidor (bypass, precinto, tapa)
2. EVIDENCIA DE CONSUMO: Caídas, anomalías vs pares, patrones extraños
3. EVIDENCIA DE HISTORIAL: Reincidencia, hurtos previos

Variables ELIMINADAS (no causan hurto):
- consumo_std, consumo_cv, consumo_mediana, consumo_rango (estadísticas)
- deuda_total, ratio_pago, dias_mora (morosidad ≠ hurto)
- variacion_facturacion (administrativo)

Variables NUEVAS (evidencia directa):
- alarmas_precinto_roto, alarmas_tapa_abierta (manipulación física)
- consumo_minimo_sostenido (bypass sostenido)
- ratio_consumo_nocturno (patrón nocturno)
- score_evidencia_fisica (compuesto)
- score_evidencia_consumo (compuesto)
- score_reincidencia (compuesto)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from src.utilidades.registrador import registro
from src.utilidades.tiempo import ahora_peru


class ExtractorCaracteristicas:
    """
    Extrae características CAUSALES de hurto
    """
    
    def __init__(self):
        # Tipos de alarma que son EVIDENCIA DIRECTA de hurto
        self.alarmas_hurto_directo = [
            'bypass', 'magneto', 'iman', 'precinto', 'tapa',
            'inversion', 'fase', 'puente', 'derivacion'
        ]
        
        # Tipos de alarma que son EVIDENCIA INDIRECTA
        self.alarmas_hurto_indirecto = [
            'caida', 'brusca', 'consumo cero', 'error'
        ]
        
        registro.info("📊 Extractor CAUSAL inicializado")
        registro.info(f"   🚨 Alarmas directas: {len(self.alarmas_hurto_directo)}")
        registro.info(f"   ⚠️ Alarmas indirectas: {len(self.alarmas_hurto_indirecto)}")
    
    # ============================================================
    # GRUPO A: EVIDENCIA FÍSICA (ALARMAS)
    # ============================================================
    
    def extraer_evidencia_fisica(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extrae evidencia física de hurto desde las alarmas
        
        Variables:
        - alarmas_tipo_bypass: Bypass/magneto detectado
        - alarmas_precinto_roto: Precinto manipulado
        - alarmas_tapa_abierta: Medidor abierto
        - alarmas_ultimos_30_dias: Alarmas recientes
        - dias_ultima_alarma: Recencia
        - score_evidencia_fisica: Score compuesto
        """
        registro.info("🚨 Extrayendo evidencia física (alarmas)...")
        
        if df.empty or 'id_cliente' not in df.columns:
            registro.warning("⚠️ No hay datos de alarmas")
            return pd.DataFrame()
        
        caracteristicas = pd.DataFrame()
        caracteristicas['id_cliente'] = df['id_cliente'].unique()
        
        # Normalizar tipo de alarma (sin tildes, minúsculas)
        df = df.copy()
        df['tipo_norm'] = (
            df['tipo_alarma']
            .astype(str)
            .str.lower()
            .str.strip()
            .str.replace('á', 'a', regex=False)
            .str.replace('é', 'e', regex=False)
            .str.replace('í', 'i', regex=False)
            .str.replace('ó', 'o', regex=False)
            .str.replace('ú', 'u', regex=False)
            .str.replace('ñ', 'n', regex=False)
        )
        
        # --------------------------------------------------------
        # 1. Alarmas de BYPASS/MAGNETO (señal directa)
        # --------------------------------------------------------
        mask_bypass = df['tipo_norm'].str.contains('bypass|magneto|iman|puente', na=False)
        bypass_count = df[mask_bypass].groupby('id_cliente').size().reset_index(name='alarmas_tipo_bypass')
        caracteristicas = caracteristicas.merge(bypass_count, on='id_cliente', how='left')
        caracteristicas['alarmas_tipo_bypass'] = caracteristicas['alarmas_tipo_bypass'].fillna(0)
        
        # --------------------------------------------------------
        # 2. Alarmas de PRECINTO ROTO (manipulación)
        # --------------------------------------------------------
        mask_precinto = df['tipo_norm'].str.contains('precinto', na=False)
        precinto_count = df[mask_precinto].groupby('id_cliente').size().reset_index(name='alarmas_precinto_roto')
        caracteristicas = caracteristicas.merge(precinto_count, on='id_cliente', how='left')
        caracteristicas['alarmas_precinto_roto'] = caracteristicas['alarmas_precinto_roto'].fillna(0)
        
        # --------------------------------------------------------
        # 3. Alarmas de TAPA ABIERTA (acceso al medidor)
        # --------------------------------------------------------
        mask_tapa = df['tipo_norm'].str.contains('tapa|apertura', na=False)
        tapa_count = df[mask_tapa].groupby('id_cliente').size().reset_index(name='alarmas_tapa_abierta')
        caracteristicas = caracteristicas.merge(tapa_count, on='id_cliente', how='left')
        caracteristicas['alarmas_tapa_abierta'] = caracteristicas['alarmas_tapa_abierta'].fillna(0)
        
        # --------------------------------------------------------
        # 4. Alarmas de INVERSIÓN DE FASES (manipulación técnica)
        # --------------------------------------------------------
        mask_fases = df['tipo_norm'].str.contains('inversion|fase', na=False)
        fases_count = df[mask_fases].groupby('id_cliente').size().reset_index(name='alarmas_inversion_fases')
        caracteristicas = caracteristicas.merge(fases_count, on='id_cliente', how='left')
        caracteristicas['alarmas_inversion_fases'] = caracteristicas['alarmas_inversion_fases'].fillna(0)
        
        # --------------------------------------------------------
        # 5. Alarmas en los últimos 30 días (hurto activo)
        # --------------------------------------------------------
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
            hace_30 = ahora_peru().replace(tzinfo=None) - pd.Timedelta(days=30)
            hace_90 = ahora_peru().replace(tzinfo=None) - pd.Timedelta(days=90)
            
            # Alarmas últimos 30 días
            recientes_30 = df[df['fecha'] >= hace_30]
            count_30 = recientes_30.groupby('id_cliente').size().reset_index(name='alarmas_ultimos_30_dias')
            caracteristicas = caracteristicas.merge(count_30, on='id_cliente', how='left')
            caracteristicas['alarmas_ultimos_30_dias'] = caracteristicas['alarmas_ultimos_30_dias'].fillna(0)
            
            # Alarmas últimos 90 días
            recientes_90 = df[df['fecha'] >= hace_90]
            count_90 = recientes_90.groupby('id_cliente').size().reset_index(name='alarmas_ultimos_90_dias')
            caracteristicas = caracteristicas.merge(count_90, on='id_cliente', how='left')
            caracteristicas['alarmas_ultimos_90_dias'] = caracteristicas['alarmas_ultimos_90_dias'].fillna(0)
            
            # Días desde última alarma
            ultima = df.groupby('id_cliente')['fecha'].max().reset_index()
            ultima['dias_ultima_alarma'] = (
                ahora_peru().replace(tzinfo=None) - ultima['fecha']
            ).dt.days
            caracteristicas = caracteristicas.merge(
                ultima[['id_cliente', 'dias_ultima_alarma']],
                on='id_cliente', how='left'
            )
            # Si no tiene alarma, poner 999 (muy lejano)
            caracteristicas['dias_ultima_alarma'] = caracteristicas['dias_ultima_alarma'].fillna(999)
        else:
            caracteristicas['alarmas_ultimos_30_dias'] = 0
            caracteristicas['alarmas_ultimos_90_dias'] = 0
            caracteristicas['dias_ultima_alarma'] = 999
        
        # --------------------------------------------------------
        # 6. SCORE DE EVIDENCIA FÍSICA (compuesto ponderado)
        # --------------------------------------------------------
        caracteristicas['score_evidencia_fisica'] = (
            caracteristicas['alarmas_tipo_bypass'] * 0.40 +        # Bypass = señal muy fuerte
            caracteristicas['alarmas_precinto_roto'] * 0.20 +      # Precinto = señal fuerte
            caracteristicas['alarmas_tapa_abierta'] * 0.10 +       # Tapa = señal media
            caracteristicas['alarmas_inversion_fases'] * 0.15 +    # Fases = señal media-alta
            caracteristicas['alarmas_ultimos_30_dias'] * 0.15      # Recencia = señal fuerte
        )
        # Normalizar entre 0 y 1
        max_score = caracteristicas['score_evidencia_fisica'].max()
        if max_score > 0:
            caracteristicas['score_evidencia_fisica'] = (
                caracteristicas['score_evidencia_fisica'] / max_score
            )
        
        caracteristicas = caracteristicas.fillna(0)
        
        registro.info(f"✅ {len(caracteristicas)} clientes con evidencia física")
        
        return caracteristicas
    
    # ============================================================
    # GRUPO B: EVIDENCIA DE CONSUMO
    # ============================================================
    
    def extraer_evidencia_consumo(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extrae evidencia de hurto desde el consumo
        
        Variables:
        - caida_brusca: Caída reciente
        - meses_con_caida: Persistencia
        - consumo_vs_similares: Anomalía vs pares
        - consumo_minimo_sostenido: Bypass sostenido
        - ratio_consumo_nocturno: Patrón nocturno
        - score_evidencia_consumo: Score compuesto
        """
        registro.info("📉 Extrayendo evidencia de consumo...")
        
        if 'consumo_kwh' not in df.columns or 'id_cliente' not in df.columns:
            registro.warning("⚠️ No hay datos de consumo")
            return pd.DataFrame()
        
        # Limpiar
        df = df.copy()
        df['consumo_kwh'] = pd.to_numeric(df['consumo_kwh'], errors='coerce')
        df = df[df['consumo_kwh'] >= 0]
        df = df.dropna(subset=['consumo_kwh'])
        df = df[df['consumo_kwh'] <= 10000]
        
        if df.empty:
            return pd.DataFrame()
        
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df = df.dropna(subset=['fecha'])
        
        caracteristicas = pd.DataFrame()
        caracteristicas['id_cliente'] = df['id_cliente'].unique()
        
        # --------------------------------------------------------
        # 1. CONSUMO PROMEDIO (solo para comparar, no como feature)
        # --------------------------------------------------------
        consumo_avg = df.groupby('id_cliente')['consumo_kwh'].mean().reset_index()
        consumo_avg.columns = ['id_cliente', 'consumo_promedio']
        caracteristicas = caracteristicas.merge(consumo_avg, on='id_cliente', how='left')
        
        # --------------------------------------------------------
        # 2. CAÍDA BRUSCA (últimos 90 días vs promedio histórico)
        # --------------------------------------------------------
        df_ordenado = df.sort_values(['id_cliente', 'fecha'])
        ultimos_90 = df_ordenado.groupby('id_cliente').tail(90)
        consumo_reciente = ultimos_90.groupby('id_cliente')['consumo_kwh'].mean().reset_index()
        consumo_reciente.columns = ['id_cliente', 'consumo_reciente']
        caracteristicas = caracteristicas.merge(consumo_reciente, on='id_cliente', how='left')
        
        caracteristicas['caida_brusca'] = (
            (caracteristicas['consumo_promedio'] - caracteristicas['consumo_reciente']) /
            (caracteristicas['consumo_promedio'] + 0.01)
        ).clip(0, 1)
        
        # --------------------------------------------------------
        # 3. MESES CON CAÍDA > 20%
        # --------------------------------------------------------
        df['mes'] = df['fecha'].dt.to_period('M')
        mensual = df.groupby(['id_cliente', 'mes'])['consumo_kwh'].mean().reset_index()
        
        meses_caida = []
        for cliente in caracteristicas['id_cliente']:
            consumos = mensual[mensual['id_cliente'] == cliente]['consumo_kwh'].values
            if len(consumos) > 1:
                variaciones = np.diff(consumos) / (consumos[:-1] + 0.01)
                n_meses = int((variaciones < -0.2).sum())
            else:
                n_meses = 0
            meses_caida.append(n_meses)
        caracteristicas['meses_con_caida'] = meses_caida
        
        # --------------------------------------------------------
        # 4. CONSUMO MÍNIMO SOSTENIDO (promedio de los 3 meses más bajos)
        # --------------------------------------------------------
        min_sostenido = []
        for cliente in caracteristicas['id_cliente']:
            consumos = mensual[mensual['id_cliente'] == cliente]['consumo_kwh'].values
            if len(consumos) >= 3:
                # Promedio de los 3 meses más bajos
                consumos_ordenados = np.sort(consumos)
                min_sost = consumos_ordenados[:3].mean()
            else:
                min_sost = consumos.mean() if len(consumos) > 0 else 0
            min_sostenido.append(min_sost)
        caracteristicas['consumo_minimo_sostenido'] = min_sostenido
        
        # --------------------------------------------------------
        # 5. CONSUMO VS SIMILARES (comparar con promedio global)
        # --------------------------------------------------------
        # Nota: En producción, agrupar por tipo_cliente y sector
        promedio_global = caracteristicas['consumo_promedio'].mean()
        caracteristicas['consumo_vs_similares'] = (
            caracteristicas['consumo_promedio'] / (promedio_global + 0.01)
        )
        
        # --------------------------------------------------------
        # 6. RATIO CONSUMO NOCTURNO (si hay datos horarios)
        # --------------------------------------------------------
        # Por ahora, solo si el dataset tiene información de hora
        if 'hora' in df.columns or 'consumo_nocturno' in df.columns:
            # Implementación futura
            caracteristicas['ratio_consumo_nocturno'] = 1.0
        else:
            # Sin datos horarios, asumir 1.0 (neutro)
            caracteristicas['ratio_consumo_nocturno'] = 1.0
        
        # --------------------------------------------------------
        # 7. SCORE DE EVIDENCIA DE CONSUMO (compuesto)
        # --------------------------------------------------------
        # Normalizar componentes
        def norm(serie):
            max_val = serie.max()
            if max_val > 0:
                return serie / max_val
            return serie
        
        caida_norm = norm(caracteristicas['caida_brusca'])
        meses_norm = norm(caracteristicas['meses_con_caida'])
        # consumo_vs_similares: mientras MENOR, más sospechoso (invertir)
        similares_norm = 1 - norm(caracteristicas['consumo_vs_similares']).clip(0, 1)
        # consumo_minimo_sostenido: mientras menor, más sospechoso (invertir)
        min_norm = 1 - norm(caracteristicas['consumo_minimo_sostenido'])
        
        caracteristicas['score_evidencia_consumo'] = (
            caida_norm * 0.35 +         # Caída reciente = señal fuerte
            meses_norm * 0.20 +          # Persistencia = señal media
            similares_norm * 0.25 +      # Anomalía vs pares = señal fuerte
            min_norm * 0.20              # Bypass sostenido = señal fuerte
        )
        
        caracteristicas = caracteristicas.fillna(0)
        
        registro.info(f"✅ {len(caracteristicas)} clientes con evidencia de consumo")
        
        return caracteristicas
    
    # ============================================================
    # GRUPO C: EVIDENCIA DE HISTORIAL
    # ============================================================
    
    def extraer_evidencia_historial(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extrae evidencia de historial de inspecciones
        
        Variables:
        - hurto_confirmado_previo: Booleano
        - inspecciones_previas: Count
        - tasa_exito_historica: Ratio
        - meses_desde_ultima_inspeccion: Recencia
        - score_reincidencia: Score compuesto
        """
        registro.info("📚 Extrayendo evidencia de historial...")
        
        if df.empty or 'id_cliente' not in df.columns:
            registro.warning("⚠️ No hay datos de inspecciones")
            return pd.DataFrame(columns=[
                'id_cliente', 'hurto_confirmado_previo', 'inspecciones_previas',
                'tasa_exito_historica', 'meses_desde_ultima_inspeccion',
                'score_reincidencia'
            ])
        
        df = df.copy()
        df['resultado_norm'] = df['resultado'].astype(str).str.lower() if 'resultado' in df.columns else ''
        
        # --------------------------------------------------------
        # 1. INSPECCIONES PREVIAS
        # --------------------------------------------------------
        caracteristicas = df.groupby('id_cliente').size().reset_index(name='inspecciones_previas')
        
        # --------------------------------------------------------
        # 2. HURTO CONFIRMADO PREVIO
        # --------------------------------------------------------
        if 'resultado' in df.columns:
            hurto = df[df['resultado_norm'].str.contains('hurto', na=False)]
            hurto_count = hurto.groupby('id_cliente').size().reset_index(name='hurto_count')
            caracteristicas = caracteristicas.merge(hurto_count, on='id_cliente', how='left')
            caracteristicas['hurto_count'] = caracteristicas['hurto_count'].fillna(0)
            caracteristicas['hurto_confirmado_previo'] = (
                caracteristicas['hurto_count'] > 0
            ).astype(int)
        else:
            caracteristicas['hurto_confirmado_previo'] = 0
        
        # --------------------------------------------------------
        # 3. TASA DE ÉXITO HISTÓRICA
        # --------------------------------------------------------
        caracteristicas['tasa_exito_historica'] = (
            caracteristicas['hurto_confirmado_previo'] /
            (caracteristicas['inspecciones_previas'] + 0.01)
        ).clip(0, 1)
        
        # --------------------------------------------------------
        # 4. MESES DESDE ÚLTIMA INSPECCIÓN
        # --------------------------------------------------------
        if 'fecha_inspeccion' in df.columns:
            df['fecha_inspeccion'] = pd.to_datetime(df['fecha_inspeccion'], errors='coerce')
            ultima = df.groupby('id_cliente')['fecha_inspeccion'].max().reset_index()
            ultima['meses_desde_ultima_inspeccion'] = (
                (ahora_peru().replace(tzinfo=None) - ultima['fecha_inspeccion']).dt.days / 30
            ).round(0)
            caracteristicas = caracteristicas.merge(
                ultima[['id_cliente', 'meses_desde_ultima_inspeccion']],
                on='id_cliente', how='left'
            )
            caracteristicas['meses_desde_ultima_inspeccion'] = (
                caracteristicas['meses_desde_ultima_inspeccion'].fillna(999)
            )
        else:
            caracteristicas['meses_desde_ultima_inspeccion'] = 999
        
        # --------------------------------------------------------
        # 5. SCORE DE REINCIDENCIA (compuesto)
        # --------------------------------------------------------
        caracteristicas['score_reincidencia'] = (
            caracteristicas['hurto_confirmado_previo'] * 0.5 +      # Reincidencia directa
            caracteristicas['tasa_exito_historica'] * 0.3 +          # Proporción de hurtos
            (1 - (caracteristicas['meses_desde_ultima_inspeccion'] / 999).clip(0, 1)) * 0.2
        )
        
        caracteristicas = caracteristicas.fillna(0)
        
        registro.info(f"✅ {len(caracteristicas)} clientes con evidencia de historial")
        
        return caracteristicas
    
    # ============================================================
    # EXTRACCIÓN COMPLETA
    # ============================================================
    
    def extraer_todas(self, consumo: pd.DataFrame,
                      alarmas: Optional[pd.DataFrame] = None,
                      facturacion: Optional[pd.DataFrame] = None,
                      inspecciones: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Extrae todas las características CAUSALES
        
        Retorna un DataFrame con 17 variables:
        - 6 de evidencia física (alarmas)
        - 6 de evidencia de consumo
        - 5 de evidencia de historial
        """
        registro.info("=" * 70)
        registro.info("📊 EXTRACCIÓN CAUSAL DE EVIDENCIA DE HURTO")
        registro.info("=" * 70)
        
        if consumo.empty:
            registro.error("❌ No hay datos de consumo")
            return pd.DataFrame()
        
        # 1. Evidencia de consumo
        ev_consumo = self.extraer_evidencia_consumo(consumo)
        
        # 2. Evidencia física (alarmas)
        if alarmas is not None and not alarmas.empty:
            ev_fisica = self.extraer_evidencia_fisica(alarmas)
            if not ev_fisica.empty:
                ev_consumo = ev_consumo.merge(ev_fisica, on='id_cliente', how='left')
        else:
            # Si no hay alarmas, agregar columnas vacías
            for col in ['alarmas_tipo_bypass', 'alarmas_precinto_roto',
                        'alarmas_tapa_abierta', 'alarmas_inversion_fases',
                        'alarmas_ultimos_30_dias', 'alarmas_ultimos_90_dias',
                        'dias_ultima_alarma', 'score_evidencia_fisica']:
                ev_consumo[col] = 0
            ev_consumo['dias_ultima_alarma'] = 999
        
        # 3. Evidencia de historial
        if inspecciones is not None and not inspecciones.empty:
            ev_historial = self.extraer_evidencia_historial(inspecciones)
            if not ev_historial.empty:
                ev_consumo = ev_consumo.merge(ev_historial, on='id_cliente', how='left')
        else:
            for col in ['hurto_confirmado_previo', 'inspecciones_previas',
                        'tasa_exito_historica', 'meses_desde_ultima_inspeccion',
                        'score_reincidencia']:
                ev_consumo[col] = 0
            ev_consumo['meses_desde_ultima_inspeccion'] = 999
        
        # 4. Imputar nulos
        ev_consumo = ev_consumo.fillna(0)
        
        # 5. Eliminar columnas auxiliares
        columnas_excluir = ['consumo_reciente', 'hurto_count']
        ev_consumo = ev_consumo.drop(
            columns=[c for c in columnas_excluir if c in ev_consumo.columns],
            errors='ignore'
        )
        
        registro.info("=" * 70)
        registro.info(f"✅ Total: {len(ev_consumo)} clientes")
        registro.info(f"📊 Variables generadas: {len(ev_consumo.columns)}")
        registro.info(f"📋 Columnas:")
        for col in ev_consumo.columns:
            registro.info(f"   - {col}")
        registro.info("=" * 70)
        
        return ev_consumo