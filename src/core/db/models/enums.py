import enum


class TransportModal(str, enum.Enum):
    BUS = "bus"
    METRO = "metro"
    TRAIN = "train"

    def __str__(self) -> str:
        return self.value


class ReportCategory(str, enum.Enum):
    ATRASO = "atraso"
    LOTACAO = "lotacao"
    SEGURANCA = "seguranca"
    MANUTENCAO = "manutencao"
    OUTRO = "outro"

    def __str__(self) -> str:
        return self.value


class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    REJECTED = "rejected"

    def __str__(self) -> str:
        return self.value


class RatingCategory(str, enum.Enum):
    LIMPEZA = "limpeza"
    PONTUALIDADE = "pontualidade"
    SEGURANCA = "seguranca"
    CONFORTO = "conforto"
    ATENDIMENTO = "atendimento"
    GERAL = "geral"

    def __str__(self) -> str:
        return self.value


class TripDirection(int, enum.Enum):
    PRIMARY_TO_SECONDARY = 1
    SECONDARY_TO_PRIMARY = 2

    def __str__(self) -> str:
        return "ida" if self.value == 1 else "volta"
