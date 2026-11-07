"""Generación de reportes en Excel (.xlsx) con openpyxl."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from models.colaborador import Colaborador


class ExportadorExcel:
    """Convierte una lista de colaboradores en un libro de Excel."""

    COLOR_PRIMARIO = "173B5E"
    COLOR_SUAVE = "5B6B7D"
    COLUMNAS = (
        ("ID", 7),
        ("Fecha de registro", 18),
        ("Nombre completo", 30),
        ("País", 16),
        ("Correo electrónico", 32),
        ("Teléfono / WhatsApp", 20),
        ("Áreas de colaboración", 44),
        ("Modalidad", 13),
        ("Disponibilidad", 19),
        ("Motivación", 60),
        ("Estado", 13),
    )
    FILA_ENCABEZADO = 4

    def generar(self, colaboradores: list[Colaborador], descripcion_filtros: str = "") -> BytesIO:
        libro = Workbook()
        listado = libro.active
        listado.title = "Colaboradores"
        self._escribir_listado(listado, colaboradores, descripcion_filtros)
        self._escribir_resumen(libro.create_sheet("Resumen"), colaboradores)

        archivo = BytesIO()
        libro.save(archivo)
        archivo.seek(0)
        return archivo

    # ------------------------------------------------------------------
    def _escribir_listado(self, hoja, colaboradores: list[Colaborador], descripcion_filtros: str) -> None:
        self._titulo(hoja, "Fundación Beit Shalom · Reporte de colaboradores")
        hoja["A2"] = (
            f"Generado el {datetime.now():%d/%m/%Y %H:%M} · "
            f"Filtros: {descripcion_filtros or 'ninguno'} · Total: {len(colaboradores)}"
        )
        hoja["A2"].font = Font(italic=True, color=self.COLOR_SUAVE)

        for columna, (titulo, ancho) in enumerate(self.COLUMNAS, start=1):
            self._encabezado(hoja.cell(row=self.FILA_ENCABEZADO, column=columna), titulo)
            hoja.column_dimensions[get_column_letter(columna)].width = ancho

        for fila, colaborador in enumerate(colaboradores, start=self.FILA_ENCABEZADO + 1):
            valores = (
                colaborador.id,
                colaborador.fecha_registro,
                colaborador.nombre,
                colaborador.pais,
                colaborador.correo,
                colaborador.telefono,
                ", ".join(colaborador.nombres_areas),
                colaborador.modalidad,
                colaborador.disponibilidad,
                colaborador.motivacion,
                colaborador.estado,
            )
            for columna, valor in enumerate(valores, start=1):
                celda = hoja.cell(row=fila, column=columna)
                self._asignar(celda, valor)
                celda.alignment = Alignment(vertical="top", wrap_text=columna in (7, 10))
            hoja.cell(row=fila, column=2).number_format = "dd/mm/yyyy hh:mm"

        ultima_fila = self.FILA_ENCABEZADO + max(len(colaboradores), 1)
        hoja.auto_filter.ref = f"A{self.FILA_ENCABEZADO}:{get_column_letter(len(self.COLUMNAS))}{ultima_fila}"
        hoja.freeze_panes = hoja.cell(row=self.FILA_ENCABEZADO + 1, column=1)

    def _escribir_resumen(self, hoja, colaboradores: list[Colaborador]) -> None:
        self._titulo(hoja, "Resumen de solicitudes")
        hoja.column_dimensions["A"].width = 36
        hoja.column_dimensions["B"].width = 12

        por_estado = Counter(colaborador.estado for colaborador in colaboradores)
        por_area = Counter(area for colaborador in colaboradores for area in colaborador.nombres_areas)

        fila = 3
        fila = self._tabla(hoja, fila, "Estado", [(estado, por_estado.get(estado, 0)) for estado in Colaborador.ESTADOS])
        hoja.cell(row=fila, column=1, value="Total").font = Font(bold=True)
        hoja.cell(row=fila, column=2, value=len(colaboradores)).font = Font(bold=True)
        self._tabla(hoja, fila + 2, "Área de colaboración", por_area.most_common())

    def _tabla(self, hoja, fila: int, titulo: str, datos: list[tuple[str, int]]) -> int:
        self._encabezado(hoja.cell(row=fila, column=1), titulo)
        self._encabezado(hoja.cell(row=fila, column=2), "Solicitudes")
        for desplazamiento, (etiqueta, total) in enumerate(datos, start=1):
            self._asignar(hoja.cell(row=fila + desplazamiento, column=1), etiqueta)
            hoja.cell(row=fila + desplazamiento, column=2, value=total)
        return fila + len(datos) + 1

    def _titulo(self, hoja, texto: str) -> None:
        hoja["A1"] = texto
        hoja["A1"].font = Font(bold=True, size=14, color=self.COLOR_PRIMARIO)

    def _encabezado(self, celda, texto: str) -> None:
        celda.value = texto
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor=self.COLOR_PRIMARIO)
        celda.alignment = Alignment(vertical="center", wrap_text=True)

    @staticmethod
    def _asignar(celda, valor) -> None:
        """Escribe el valor siempre como dato y nunca como fórmula.

        Si alguien escribe "=..." en el formulario, Excel lo mostrará como
        texto en lugar de ejecutarlo (prevención de inyección de fórmulas).
        """
        celda.value = valor
        if isinstance(valor, str):
            celda.data_type = "s"
