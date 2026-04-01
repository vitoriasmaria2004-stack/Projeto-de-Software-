from typing import List
from datetime import datetime, timedelta

class SistemaStatusHistoria:
    #monitora e identifica histórias abandonadas
    
    DIAS_LIMITE_ABANDONO = 90  # 3 meses
    
    @staticmethod
    def verificar_historias_abandonadas(historias: List['Historia']) -> List['Historia']:
        #retorna lista de histórias que estão abandonadas
        abandonadas = []
        for historia in historias:
            historia.verificar_status_abandono()
            if historia.status.value == "abandonada":
                abandonadas.append(historia)
        return abandonadas
    
    @staticmethod
    def get_status_legenda(status) -> str:
        #retorna uma legenda visual para o status
        from models.historia import StatusHistoria
        legendas = {
            StatusHistoria.EM_ANDAMENTO: "🟢 Em andamento",
            StatusHistoria.CONCLUIDA: "🔵 Concluída",
            StatusHistoria.ABANDONADA: "🟡 Possivelmente abandonada (3+ meses sem atualização)"
        }
        return legendas.get(status, status)
    
    @staticmethod
    def gerar_alerta_abandono(historia: 'Historia') -> str:
        dias_sem_atualizacao = (datetime.now() - historia.data_ultima_atualizacao).days
        return (f"⚠️ AVISO: '{historia.titulo}' está há {dias_sem_atualizacao} dias "
                f"sem atualização. Pode estar abandonada.")
