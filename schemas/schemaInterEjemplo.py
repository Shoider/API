from marshmallow import Schema, fields, validate, validates, ValidationError
import ipaddress
import re

# Definimos la lógica UNA SOLA VEZ en una función.
def validar_formato_url(value):
    """
    Validador reutilizable que comprueba si un valor (que no sea vacío)
    comienza con 'http'.
    """
    # Si el campo es opcional y viene vacío, es válido.
    if not value: # Esto cubre None, "" y otros valores "falsy".
        return

    if not isinstance(value, str) or not value.lower().startswith("http"):
        raise ValidationError("El campo debe ser una URL válida que comience con 'http'.")
    
def validar_ip_interna(value):
    """
    Validador reutilizable que comprueba si un valor es una IP
    que comienza con "172.".
    """
    try:
        ip = ipaddress.ip_address(value)
        if str(ip).startswith("172."):
            return  # Es una IP válida que cumple la condición
    except ValueError:
        # Si no es una IP válida, dejamos que lance el error al final.
        pass

    # Nota: Corregí el doble punto ".." al final de tu mensaje de error original.
    raise ValidationError("Debe ser una dirección IP válida que inicie con '172.'.")
def validar_telefono_usuario(value):
    patron = r'^[0-9\-\s()]+$'
    if not re.fullmatch(patron, value):
        raise ValidationError("El teléfono solo puede contener números, guiones, espacios o paréntesis.")

class RegistroSchemaInter(Schema):

    class Meta:
        ordered = True

    memo=fields.String(required=True)
    noticket=fields.String(required=True)
        
    uaUsuario= fields.String(required=True)
    areaUsuario= fields.String(required=True)
    nombreUsuario= fields.String(required=True)
    puestoUsuario= fields.String(required=True)
    correoUsuario=fields.Email(required=False, error_messages={"invalid": "Correo electrónico inválido"})
    direccion= fields.String(required=True)
    teleUsuario= fields.String(required=True, validate=validar_telefono_usuario)
    extUsuario= fields.String(required=True, validate=validate.Length(4, error="Número de extensión inválido"))
    nombreJefe= fields.String(required=True)
    puestoJefe= fields.String(required=True)

    cambio = fields.String(required=True)
    ipUsuario = fields.String(required=True, validate=validar_ip_interna)
    ipAnterior = fields.String(required=False, validate=validar_ip_interna)

    almacenamiento= fields.Boolean(required=True)
    blogs= fields.Boolean(required=True)
    shareware= fields.Boolean(required=True)
    redes= fields.Boolean(required=True)
    transmision= fields.Boolean(required=True)
    
    otra= fields.Boolean(required=True)
    otra2= fields.Boolean(required=False)
    otra3= fields.Boolean(required=False)
    otra4= fields.Boolean(required=False)

    
    justificaAlmacenamiento = fields.String(required=False, validate=validate.Length(min=50, max=256, error="La justificación debe tener mínimo 50 caracteres."))
    justificaBlogs= fields.String(required=False, validate=validate.Length(min=50, max=256, error="La justificación debe tener mínimo 50 caracteres."))
    justificaShareware= fields.String(required=False, validate=validate.Length(min=50, max=256, error="La justificación debe tener mínimo 50 caracteres."))
    justificaRedes= fields.String(required=False, validate=validate.Length(min=50, max=256, error="La justificación debe tener mínimo 50 caracteres."))
    justificaTransmision= fields.String(required=False, validate=validate.Length(min=50, max=256, error="La justificación debe tener mínimo 50 caracteres."))
    
    urlOtra= fields.String(required=False, allow_none=True, validate=validar_formato_url)
    justificaOtra= fields.String(required=False, validate=validate.Length(min=50, max=256, error="La justificación debe tener mínimo 50 caracteres."))
    otraC= fields.String(required=False)
    urlOtra2= fields.String(required=False, allow_none=True, validate=validar_formato_url)
    justificaOtra2= fields.String(required=False, validate=validate.Length(min=50, max=256, error="La justificación debe tener mínimo 50 caracteres."))
    otraC2= fields.String(required=False)
    urlOtra3= fields.String(required=False, allow_none=True, validate=validar_formato_url)
    justificaOtra3= fields.String(required=False, validate=validate.Length(min=50, max=256, error="La justificación debe tener mínimo 50 caracteres."))
    otraC3= fields.String(required=False)
    urlOtra4= fields.String(required=False, allow_none=True, validate=validar_formato_url)
    justificaOtra4= fields.String(required=False, validate=validate.Length(min=50, max=256, error="La justificación debe tener mínimo 50 caracteres."))
    otraC4= fields.String(required=False)

    ala= fields.String(required=False)
    piso= fields.String(required=False)

    politicasaceptadas = fields.Boolean(required=True)


    
