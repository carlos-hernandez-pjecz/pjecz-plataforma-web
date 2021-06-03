"""
Ubicacion de Expedientes, vistas
"""
from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from lib.safe_string import safe_expediente

from plataforma_web.blueprints.roles.models import Permiso
from plataforma_web.blueprints.usuarios.decorators import permission_required

from plataforma_web.blueprints.ubicaciones_expedientes.models import UbicacionExpediente
from plataforma_web.blueprints.ubicaciones_expedientes.forms import UbicacionExpedienteNewForm, UbicacionExpedienteEditForm, UbicacionExpedienteSearchForm

from plataforma_web.blueprints.autoridades.models import Autoridad
from plataforma_web.blueprints.distritos.models import Distrito

ubicaciones_expedientes = Blueprint("ubicaciones_expedientes", __name__, template_folder="templates")


@ubicaciones_expedientes.before_request
@login_required
@permission_required(Permiso.VER_JUSTICIABLES)
def before_request():
    """Permiso por defecto"""


@ubicaciones_expedientes.route("/ubicaciones_expedientes")
def list_active():
    """Listado de Ubicaciones de Expedientes"""
    # Si es administrador, ve las ubicaciones de expedientes de todas las autoridades
    if current_user.can_admin("sentencias"):
        ubicaciones_expedientes_activos = UbicacionExpediente.query.filter(UbicacionExpediente.estatus == "A").order_by(UbicacionExpediente.creado.desc()).limit(100).all()
        return render_template("ubicaciones_expedientes/list.jinja2", ubicaciones_expedientes=ubicaciones_expedientes_activos, estatus="A")
    # No es administrador, consultar su autoridad
    if current_user.autoridad.es_jurisdiccional:
        sus_ubicaciones_expedientes_activos = UbicacionExpediente.query.filter(UbicacionExpediente.autoridad == current_user.autoridad).filter(UbicacionExpediente.estatus == "A").order_by(UbicacionExpediente.creado.desc()).limit(100).all()
        return render_template("ubicaciones_expedientes/list.jinja2", ubicaciones_expedientes=sus_ubicaciones_expedientes_activos, estatus="A")
    # No es jurisdiccional, se redirige al listado de distritos
    return redirect(url_for("ubicaciones_expedientes.list_distritos"))


@ubicaciones_expedientes.route("/ubicaciones_expedientes/inactivos")
@permission_required(Permiso.MODIFICAR_JUSTICIABLES)
def list_inactive():
    """Listado de Ubicaciones de Expedientes inactivos"""
    # Si es administrador, ve las ubicaciones de expedientes de todas las autoridades
    if current_user.can_admin("sentencias"):
        ubicaciones_expedientes_inactivos = UbicacionExpediente.query.filter(UbicacionExpediente.estatus == "B").order_by(UbicacionExpediente.creado.desc()).limit(100).all()
        return render_template("ubicaciones_expedientes/list.jinja2", ubicaciones_expedientes=ubicaciones_expedientes_inactivos, estatus="B")
    # No es administrador, consultar su autoridad
    if current_user.autoridad.es_jurisdiccional:
        sus_ubicaciones_expedientes_inactivos = UbicacionExpediente.query.filter(UbicacionExpediente.autoridad == current_user.autoridad).filter(UbicacionExpediente.estatus == "B").order_by(UbicacionExpediente.creado.desc()).limit(100).all()
        return render_template("ubicaciones_expedientes/list.jinja2", ubicaciones_expedientes=sus_ubicaciones_expedientes_inactivos, estatus="B")
    # No es jurisdiccional, se redirige al listado de distritos
    return redirect(url_for("ubicaciones_expedientes.list_distritos"))


@ubicaciones_expedientes.route("/ubicaciones_expedientes/distritos")
def list_distritos():
    """Listado de Distritos"""
    distritos = Distrito.query.filter(Distrito.es_distrito_judicial == True).filter(Distrito.estatus == "A").order_by(Distrito.nombre).all()
    return render_template("ubicaciones_expedientes/list_distritos.jinja2", distritos=distritos, estatus="A")


@ubicaciones_expedientes.route("/ubicaciones_expedientes/distrito/<int:distrito_id>")
def list_autoridades(distrito_id):
    """Listado de Autoridades de un distrito"""
    distrito = Distrito.query.get_or_404(distrito_id)
    autoridades = Autoridad.query.filter(Autoridad.distrito == distrito).filter(Autoridad.es_jurisdiccional == True).filter(Autoridad.es_notaria == False).filter(Autoridad.estatus == "A").order_by(Autoridad.clave).all()
    return render_template("ubicaciones_expedientes/list_autoridades.jinja2", distrito=distrito, autoridades=autoridades, estatus="A")


@ubicaciones_expedientes.route("/ubicaciones_expedientes/autoridad/<int:autoridad_id>")
def list_autoridad_ubicaciones_expedientes(autoridad_id):
    """Listado de Ubicaciones de Expedientes activasode una autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    ubicaciones_expedientes_activos = UbicacionExpediente.query.filter(UbicacionExpediente.autoridad == autoridad).filter(UbicacionExpediente.estatus == "A").order_by(UbicacionExpediente.fecha.desc()).limit(100).all()
    return render_template("ubicaciones_expedientes/list.jinja2", autoridad=autoridad, ubicaciones_expedientes=ubicaciones_expedientes_activos, estatus="A")


@ubicaciones_expedientes.route("/ubicaciones_expedientes/inactivos/autoridad/<int:autoridad_id>")
@permission_required(Permiso.ADMINISTRAR_JUSTICIABLES)
def list_autoridad_ubicaciones_expedientes_inactive(autoridad_id):
    """Listado de Ubicaciones de Expedientes inactivos de una autoridad"""
    autoridad = Autoridad.query.get_or_404(autoridad_id)
    ubicaciones_expedientes_inactivos = UbicacionExpediente.query.filter(UbicacionExpediente.autoridad == autoridad).filter(UbicacionExpediente.estatus == "B").order_by(UbicacionExpediente.creado.desc()).limit(100).all()
    return render_template("ubicaciones_expedientes/list.jinja2", autoridad=autoridad, ubicaciones_expedientes=ubicaciones_expedientes_inactivos, estatus="B")


@ubicaciones_expedientes.route("/ubicaciones_expedientes/<int:ubicacion_expediente_id>")
def detail(ubicacion_expediente_id):
    """Detalle de una Ubicacion de Expediente"""
    ubicacion_expediente = UbicacionExpediente.query.get_or_404(ubicacion_expediente_id)
    return render_template("ubicaciones_expedientes/detail.jinja2", ubicacion_expediente=ubicacion_expediente)


@ubicaciones_expedientes.route("/ubicaciones_expedientes/buscar", methods=["GET", "POST"])
def search():
    """Buscar Ubicacion de Expediente"""
    form_search = UbicacionExpedienteSearchForm()
    if form_search.validate_on_submit():
        mostrar_resultados = True
        autoridad = Autoridad.query.get(form_search.autoridad.data)
        consulta = UbicacionExpediente.query.filter(UbicacionExpediente.autoridad == autoridad)
        try:
            expediente = safe_expediente(form_search.expediente.data)
            if expediente != "":
                consulta = consulta.filter(UbicacionExpediente.expediente == expediente)
        except (IndexError, ValueError):
            flash("El expediente es incorrecto.", "warning")
            mostrar_resultados = False
        if mostrar_resultados:
            consulta = consulta.order_by(UbicacionExpediente.creado.desc()).limit(100).all()
            return render_template("ubicaciones_expedientes/list.jinja2", ubicaciones_expedientes=consulta)
    distritos = Distrito.query.filter(Distrito.es_distrito_judicial == True).filter(Distrito.estatus == "A").order_by(Distrito.nombre).all()
    autoridades = Autoridad.query.filter(Autoridad.es_jurisdiccional == True).filter(Autoridad.es_notaria == False).filter(Autoridad.estatus == "A").order_by(Autoridad.clave).all()
    return render_template("ubicaciones_expedientes/search.jinja2", form=form_search, distritos=distritos, autoridades=autoridades)


@ubicaciones_expedientes.route("/ubicaciones_expedientes/nuevo", methods=["GET", "POST"])
@permission_required(Permiso.CREAR_JUSTICIABLES)
def new():
    """Nuevo Ubicación de Expedientes"""
    form = UbicacionExpedienteNewForm()
    if form.validate_on_submit():
        ubicacion_expediente = UbicacionExpediente(
            autoridad=Autoridad.query.get_or_404(form.autoridad.data),
            expediente=form.expediente.data.strip(),
            ubicacion=form.ubicacion.data,
        )
        ubicacion_expediente.save()
        flash(f"Ubicación de Expedientes {ubicacion_expediente.expediente} guardado.", "success")
        return redirect(url_for("ubicaciones_expedientes.detail", ubicacion_expediente_id=ubicacion_expediente.id))
    distritos = Distrito.query.filter(Distrito.es_distrito_judicial == True).filter(Distrito.estatus == "A").order_by(Distrito.nombre).all()
    autoridades = Autoridad.query.filter(Autoridad.es_jurisdiccional == True).filter(Autoridad.es_notaria == False).filter(Autoridad.estatus == "A").order_by(Autoridad.clave).all()
    return render_template("ubicaciones_expedientes/new.jinja2", form=form, distritos=distritos, autoridades=autoridades)


@ubicaciones_expedientes.route("/ubicaciones_expedientes/edicion/<int:ubicacion_expediente_id>", methods=["GET", "POST"])
@permission_required(Permiso.MODIFICAR_JUSTICIABLES)
def edit(ubicacion_expediente_id):
    """Editar Ubicación de Expedientes"""
    ubicacion_expediente = UbicacionExpediente.query.get_or_404(ubicacion_expediente_id)
    form = UbicacionExpedienteEditForm()
    if form.validate_on_submit():
        ubicacion_expediente.expediente = form.expediente.data.strip()
        ubicacion_expediente.ubicacion = form.ubicacion.data
        ubicacion_expediente.save()
        flash(f"Ubicación de Expedientes {ubicacion_expediente.expediente} guardado.", "success")
        return redirect(url_for("ubicaciones_expedientes.detail", ubicacion_expediente_id=ubicacion_expediente.id))
    form.expediente.data = ubicacion_expediente.expediente
    form.ubicacion.data = ubicacion_expediente.ubicacion
    return render_template("ubicaciones_expedientes/edit.jinja2", form=form, ubicacion_expediente=ubicacion_expediente)


@ubicaciones_expedientes.route("/ubicaciones_expedientes/eliminar/<int:ubicacion_expediente_id>")
@permission_required(Permiso.MODIFICAR_JUSTICIABLES)
def delete(ubicacion_expediente_id):
    """Eliminar Ubicacion de Expedientes"""
    ubicacion_expediente = UbicacionExpediente.query.get_or_404(ubicacion_expediente_id)
    if ubicacion_expediente.estatus == "A":
        ubicacion_expediente.delete()
        flash(f"Ubicacion de Expediente {ubicacion_expediente.expediente} eliminado.", "success")
    return redirect(url_for("ubicaciones_expedientes.detail", ubicacion_expediente_id=ubicacion_expediente_id))


@ubicaciones_expedientes.route("/ubicaciones_expedientes/recuperar/<int:ubicacion_expediente_id>")
@permission_required(Permiso.MODIFICAR_JUSTICIABLES)
def recover(ubicacion_expediente_id):
    """Recuperar Lista de Acuerdos"""
    ubicacion_expediente = UbicacionExpediente.query.get_or_404(ubicacion_expediente_id)
    if ubicacion_expediente.estatus == "B":
        ubicacion_expediente.recover()
        flash(f"Ubicacion de Expediente {ubicacion_expediente.expediente} recuperado.", "success")
    return redirect(url_for("ubicaciones_expedientes.detail", ubicacion_expediente_id=ubicacion_expediente_id))
