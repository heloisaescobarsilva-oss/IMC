"""
Calculadora de IMC — Backend Python
Público: praticantes de academia e médicos especialistas
Uso: python imc.py
"""

from dataclasses import dataclass
from enum import Enum


# ─────────────────────────────────────────
#  Enumerações e constantes
# ─────────────────────────────────────────

class Sexo(Enum):
    MASCULINO = "M"
    FEMININO  = "F"


class NivelAtividade(Enum):
    SEDENTARIO   = ("Sedentário",               1.200)
    LEVE         = ("Leve (1–2×/sem)",           1.375)
    MODERADO     = ("Moderado (3–4×/sem)",        1.550)
    ATIVO        = ("Ativo (5–6×/sem)",           1.725)
    MUITO_ATIVO  = ("Muito ativo (treino 2×/dia)", 1.900)

    def __init__(self, descricao: str, fator: float):
        self.descricao = descricao
        self.fator     = fator


# Classificação OMS (adultos 18–65 anos)
CLASSIFICACOES_IMC = [
    (16.0,  "Magreza grave (grau III)",    "Muito elevado"),
    (17.0,  "Magreza moderada (grau II)",  "Elevado"),
    (18.5,  "Magreza leve (grau I)",       "Moderado"),
    (25.0,  "Peso normal",                 "Baixo"),
    (30.0,  "Pré-obesidade / Sobrepeso",   "Aumentado"),
    (35.0,  "Obesidade grau I",            "Alto"),
    (40.0,  "Obesidade grau II",           "Muito alto"),
    (float("inf"), "Obesidade grau III (mórbida)", "Extremamente alto"),
]

# Limites de circunferência abdominal OMS
CINTURA_RISCO = {
    Sexo.MASCULINO: {"aumentado": 94, "muito_aumentado": 102},
    Sexo.FEMININO:  {"aumentado": 80, "muito_aumentado": 88},
}

# Faixas de gordura corporal (Deurenberg modificado)
GORDURA_CLASSES = {
    Sexo.MASCULINO: [
        (6,  "Nível essencial"),
        (14, "Atleta"),
        (18, "Fitness"),
        (25, "Aceitável"),
        (float("inf"), "Obesidade"),
    ],
    Sexo.FEMININO: [
        (14, "Nível essencial"),
        (21, "Atleta"),
        (25, "Fitness"),
        (32, "Aceitável"),
        (float("inf"), "Obesidade"),
    ],
}


# ─────────────────────────────────────────
#  Estrutura de resultado
# ─────────────────────────────────────────

@dataclass
class ResultadoIMC:
    # Dados de entrada
    peso_kg:     float
    altura_m:    float
    idade:       int
    sexo:        Sexo

    # IMC
    imc:          float
    classificacao: str
    risco_cardio: str

    # Composição corporal
    gordura_pct:   float
    gordura_classe: str
    peso_ideal_kg: float
    diferenca_kg:  float

    # Metabolismo (fitness)
    tmb_kcal:  float
    get_kcal:  float | None  # None se atividade não fornecida

    # Cintura (opcional)
    cintura_cm:    float | None
    cintura_risco: str | None


# ─────────────────────────────────────────
#  Funções de cálculo
# ─────────────────────────────────────────

def calcular_imc(peso_kg: float, altura_m: float) -> float:
    if altura_m <= 0:
        raise ValueError("Altura deve ser maior que zero.")
    return peso_kg / (altura_m ** 2)


def classificar_imc(imc: float) -> tuple[str, str]:
    """Retorna (classificação_OMS, risco_cardiometabólico)."""
    for limite, classe, risco in CLASSIFICACOES_IMC:
        if imc < limite:
            return classe, risco
    return CLASSIFICACOES_IMC[-1][1], CLASSIFICACOES_IMC[-1][2]


def estimar_gordura_corporal(imc: float, idade: int, sexo: Sexo) -> float:
    """Fórmula de Deurenberg (1991): %GC = 1,20·IMC + 0,23·idade − 10,8·sexo − 5,4."""
    s = 1 if sexo == Sexo.MASCULINO else 0
    return round(1.20 * imc + 0.23 * idade - 10.8 * s - 5.4, 1)


def classificar_gordura(pct: float, sexo: Sexo) -> str:
    for limite, classe in GORDURA_CLASSES[sexo]:
        if pct < limite:
            return classe
    return "Obesidade"


def calcular_tmb(peso_kg: float, altura_cm: float, idade: int, sexo: Sexo) -> float:
    """Taxa Metabólica Basal — equação de Harris-Benedict revisada (Mifflin-St Jeor)."""
    if sexo == Sexo.MASCULINO:
        return 88.362 + 13.397 * peso_kg + 4.799 * altura_cm - 5.677 * idade
    return 447.593 + 9.247 * peso_kg + 3.098 * altura_cm - 4.330 * idade


def avaliar_cintura(cintura_cm: float, sexo: Sexo) -> str:
    limites = CINTURA_RISCO[sexo]
    if cintura_cm < limites["aumentado"]:
        return "Normal — sem risco adicional por circunferência abdominal"
    if cintura_cm < limites["muito_aumentado"]:
        return "Risco aumentado (OMS) — gordura visceral acima do recomendado"
    return "Risco substancialmente elevado — avaliação médica recomendada"


# ─────────────────────────────────────────
#  Função principal de avaliação
# ─────────────────────────────────────────

def avaliar(
    peso_kg:     float,
    altura_cm:   float,
    idade:       int,
    sexo:        Sexo,
    cintura_cm:  float | None = None,
    atividade:   NivelAtividade | None = None,
) -> ResultadoIMC:
    """
    Calcula e retorna todos os indicadores de saúde baseados no IMC.

    Parâmetros
    ----------
    peso_kg    : peso em quilogramas
    altura_cm  : altura em centímetros
    idade      : idade em anos
    sexo       : Sexo.MASCULINO ou Sexo.FEMININO
    cintura_cm : circunferência abdominal em cm (opcional)
    atividade  : NivelAtividade (opcional; necessário para GET)
    """
    altura_m   = altura_cm / 100
    imc        = calcular_imc(peso_kg, altura_m)
    cls, risco = classificar_imc(imc)
    gordura    = estimar_gordura_corporal(imc, idade, sexo)
    gc_classe  = classificar_gordura(gordura, sexo)
    ideal_imc  = 22.0  # ponto médio da faixa saudável
    peso_ideal = round(ideal_imc * (altura_m ** 2), 1)
    diferenca  = round(peso_kg - peso_ideal, 1)
    tmb        = round(calcular_tmb(peso_kg, altura_cm, idade, sexo), 0)
    get        = round(tmb * atividade.fator, 0) if atividade else None

    c_risco = avaliar_cintura(cintura_cm, sexo) if cintura_cm else None

    return ResultadoIMC(
        peso_kg        = peso_kg,
        altura_m       = altura_m,
        idade          = idade,
        sexo           = sexo,
        imc            = round(imc, 2),
        classificacao  = cls,
        risco_cardio   = risco,
        gordura_pct    = gordura,
        gordura_classe = gc_classe,
        peso_ideal_kg  = peso_ideal,
        diferenca_kg   = diferenca,
        tmb_kcal       = tmb,
        get_kcal       = get,
        cintura_cm     = cintura_cm,
        cintura_risco  = c_risco,
    )


# ─────────────────────────────────────────
#  Geração de relatório clínico em texto
# ─────────────────────────────────────────

def gerar_relatorio(r: ResultadoIMC, atividade: NivelAtividade | None = None) -> str:
    sep  = "─" * 52
    sep2 = "═" * 52

    sinal    = "+" if r.diferenca_kg >= 0 else ""
    diff_msg = (
        "✅ Dentro da faixa saudável"
        if abs(r.diferenca_kg) <= 2
        else f"{'⬆' if r.diferenca_kg > 0 else '⬇'}  {sinal}{r.diferenca_kg} kg em relação ao peso ideal"
    )

    linhas = [
        "",
        sep2,
        "  CALCULADORA DE IMC — RELATÓRIO COMPLETO",
        sep2,
        "",
        "  DADOS DO PACIENTE / ATLETA",
        sep,
        f"  Peso       : {r.peso_kg} kg",
        f"  Altura     : {r.altura_m * 100:.1f} cm",
        f"  Idade      : {r.idade} anos",
        f"  Sexo       : {r.sexo.value}",
        "",
        "  ÍNDICE DE MASSA CORPORAL",
        sep,
        f"  IMC        : {r.imc:.2f} kg/m²",
        f"  Classificação OMS : {r.classificacao}",
        f"  Risco cardiometabólico : {r.risco_cardio}",
        "",
        "  COMPOSIÇÃO CORPORAL (estimativa Deurenberg)",
        sep,
        f"  Gordura corporal est. : {r.gordura_pct}%  [{r.gordura_classe}]",
        f"  Peso ideal (IMC 22)   : {r.peso_ideal_kg} kg",
        f"  Diferença             : {diff_msg}",
    ]

    if r.cintura_cm:
        linhas += [
            "",
            "  CIRCUNFERÊNCIA ABDOMINAL",
            sep,
            f"  Cintura    : {r.cintura_cm} cm",
            f"  Avaliação  : {r.cintura_risco}",
        ]

    linhas += [
        "",
        "  METABOLISMO ENERGÉTICO",
        sep,
        f"  TMB (Harris-Benedict) : {int(r.tmb_kcal)} kcal/dia",
    ]

    if r.get_kcal and atividade:
        linhas += [
            f"  Nível de atividade    : {atividade.descricao}",
            f"  GET (TDEE)            : {int(r.get_kcal)} kcal/dia",
            f"  Meta emagrecimento    : ~{int(r.get_kcal - 500)} kcal/dia  (déficit 500 kcal)",
            f"  Meta ganho de massa   : ~{int(r.get_kcal + 300)} kcal/dia  (superávit 300 kcal)",
        ]

    linhas += [
        "",
        sep2,
        "  ⚠  Este relatório é informativo. O diagnóstico clínico",
        "     exige avaliação profissional completa.",
        sep2,
        "",
    ]

    return "\n".join(linhas)


# ─────────────────────────────────────────
#  Interface de linha de comando (CLI)
# ─────────────────────────────────────────

def _input_float(prompt: str, minv: float = 0, maxv: float = 1e6) -> float:
    while True:
        try:
            v = float(input(prompt).replace(",", "."))
            if minv <= v <= maxv:
                return v
            print(f"  ⚠  Insira um valor entre {minv} e {maxv}.")
        except ValueError:
            print("  ⚠  Valor inválido. Tente novamente.")


def _input_int(prompt: str, minv: int = 0, maxv: int = 120) -> int:
    while True:
        try:
            v = int(input(prompt))
            if minv <= v <= maxv:
                return v
            print(f"  ⚠  Insira um valor entre {minv} e {maxv}.")
        except ValueError:
            print("  ⚠  Valor inválido. Tente novamente.")


def _input_opcao(prompt: str, opcoes: list[str]) -> int:
    """Exibe menu numerado e retorna índice (0-based) da escolha."""
    for i, op in enumerate(opcoes, 1):
        print(f"  {i}. {op}")
    while True:
        try:
            v = int(input(prompt))
            if 1 <= v <= len(opcoes):
                return v - 1
        except ValueError:
            pass
        print("  ⚠  Opção inválida.")


def cli():
    print("\n" + "═" * 52)
    print("  CALCULADORA DE IMC — Academia & Clínico")
    print("═" * 52)

    peso     = _input_float("\n  Peso (kg)   : ", 20, 300)
    altura   = _input_float("  Altura (cm) : ", 100, 250)
    idade    = _input_int  ("  Idade (anos): ", 10, 120)

    print("\n  Sexo biológico:")
    idx_sexo = _input_opcao("  Escolha [1/2]: ", ["Masculino", "Feminino"])
    sexo = Sexo.MASCULINO if idx_sexo == 0 else Sexo.FEMININO

    print("\n  Nível de atividade física:")
    ops_atv = [n.descricao for n in NivelAtividade]
    idx_atv = _input_opcao("  Escolha [1–5]: ", ops_atv)
    atividade = list(NivelAtividade)[idx_atv]

    cintura_str = input("\n  Circunferência abdominal (cm) [opcional, Enter p/ pular]: ").strip()
    cintura = float(cintura_str.replace(",", ".")) if cintura_str else None

    resultado = avaliar(peso, altura, idade, sexo, cintura, atividade)
    print(gerar_relatorio(resultado, atividade))


# ─────────────────────────────────────────
#  Exemplo de uso programático
# ─────────────────────────────────────────

def exemplo():
    """Demonstração com valores fixos (útil para testes e integração com HTML)."""
    r = avaliar(
        peso_kg    = 82.0,
        altura_cm  = 175.0,
        idade      = 32,
        sexo       = Sexo.MASCULINO,
        cintura_cm = 95.0,
        atividade  = NivelAtividade.MODERADO,
    )
    print(gerar_relatorio(r, NivelAtividade.MODERADO))
    return r


if __name__ == "__main__":
    import sys
    if "--exemplo" in sys.argv:
        exemplo()
    else:
        cli()