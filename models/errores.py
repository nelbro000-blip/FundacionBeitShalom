"""Excepciones propias de las reglas del negocio."""


class ReglaNegocioError(ValueError):
    """Se lanza cuando una operación incumple una regla del negocio.

    Hereda de ValueError (herencia): sigue siendo un error de valor, pero con
    un nombre que explica mejor su origen.
    """
