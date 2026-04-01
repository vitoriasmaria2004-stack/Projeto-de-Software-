class PreferenciasLeitura:
    
    def __init__(self):
        self.modo_noturno = False
        self.tamanho_fonte = "medio"  # pequeno, medio, grande
        self.cor_fundo = "branco"  # branco, preto, bege
        self.fonte = "padrao"
    
    def alternar_modo_noturno(self) -> None:
        #alterna entre modo noturno e normal
        self.modo_noturno = not self.modo_noturno
        if self.modo_noturno:
            self.cor_fundo = "preto"
        else:
            self.cor_fundo = "branco"
    
    def aumentar_fonte(self) -> None:
        tamanhos = ["pequeno", "medio", "grande"]
        if self.tamanho_fonte in tamanhos:
            idx = tamanhos.index(self.tamanho_fonte)
            if idx < len(tamanhos) - 1:
                self.tamanho_fonte = tamanhos[idx + 1]
    
    def diminuir_fonte(self) -> None:
        tamanhos = ["pequeno", "medio", "grande"]
        if self.tamanho_fonte in tamanhos:
            idx = tamanhos.index(self.tamanho_fonte)
            if idx > 0:
                self.tamanho_fonte = tamanhos[idx - 1]
    
    def __str__(self) -> str:
        return f"Modo Noturno: {self.modo_noturno} | Fonte: {self.tamanho_fonte}"
