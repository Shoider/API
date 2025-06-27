# schemas/schemaDate.py
from marshmallow import Schema, fields, validate, EXCLUDE

class DateRangeSchema(Schema):
    # Por defecto, fields.Date espera 'YYYY-MM-DD'
    fechaInicio = fields.Date(required=True, metadata={"description": "Fecha de inicio en formato YYYY-MM-DD"})
    fechaFin = fields.Date(required=True, metadata={"description": "Fecha de fin en formato YYYY-MM-DD"})

    class Meta:
        # Esto permite que el esquema ignore campos que no estén definidos
        # si se envían accidentalmente, en lugar de lanzar un error.
        unknown = EXCLUDE