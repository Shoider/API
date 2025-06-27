from marshmallow import Schema, fields, validate, post_load

class Schema(Schema):
    # Campos que esperas después de parsear cada línea
    label = fields.String(required=True)
    id = fields.Integer(required=True)
    evaluations = fields.Integer(required=True)
    packets_matched = fields.Integer(required=True)
    bytes_matched = fields.Integer(required=True)
    states_created = fields.Integer(required=True)
    state_packets = fields.Integer(required=True)
    state_bytes = fields.Integer(required=True)
    last_field = fields.Integer(required=False) # Si el último campo es opcional o no siempre significativo