from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Tarefa(Base):
    __tablename__ = "tarefas"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(100))
    descricao: Mapped[str | None] = mapped_column(String(500))
    concluida: Mapped[bool] = mapped_column(default=False)
