// Validación en el navegador para dar retroalimentación inmediata.
// El servidor vuelve a validar todo: esta capa es solo para comodidad del usuario.

const formRegistro = document.getElementById('form-registro');
const errorGeneral = document.getElementById('error-general');
const botonEnviar = document.getElementById('boton-enviar');

const campoNombre = document.getElementById('nombre');
const campoEmail = document.getElementById('email');
const campoEmpresa = document.getElementById('empresa');
const campoArea = document.getElementById('area');

// Expresión regular simple para validar formato de email
const REGEX_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Limpia todos los mensajes de error (generales y por campo)
function limpiarErrores() {
  errorGeneral.textContent = '';
  errorGeneral.classList.add('oculto');

  document.querySelectorAll('.mensaje-error-campo').forEach((el) => {
    el.textContent = '';
  });

  document.querySelectorAll('.campo-invalido').forEach((el) => {
    el.classList.remove('campo-invalido');
  });
}

// Marca un campo como inválido y muestra su mensaje de error específico
function marcarError(campo, idMensaje, mensaje) {
  campo.classList.add('campo-invalido');
  document.getElementById(idMensaje).textContent = mensaje;
}

// Valida todos los campos del formulario; retorna true si todo es válido
function validarFormulario() {
  limpiarErrores();
  let esValido = true;

  const nombre = campoNombre.value.trim();
  const email = campoEmail.value.trim();
  const empresa = campoEmpresa.value.trim();
  const area = campoArea.value;

  if (nombre === '') {
    marcarError(campoNombre, 'error-nombre', 'El nombre completo es obligatorio.');
    esValido = false;
  }

  if (email === '') {
    marcarError(campoEmail, 'error-email', 'El email es obligatorio.');
    esValido = false;
  } else if (!REGEX_EMAIL.test(email)) {
    marcarError(campoEmail, 'error-email', 'El email no tiene un formato válido.');
    esValido = false;
  }

  if (empresa === '') {
    marcarError(campoEmpresa, 'error-empresa', 'La empresa u organización es obligatoria.');
    esValido = false;
  }

  if (area === '') {
    marcarError(campoArea, 'error-area', 'Selecciona un área de interés.');
    esValido = false;
  }

  if (!esValido) {
    errorGeneral.textContent = 'Por favor corrige los campos marcados antes de continuar.';
    errorGeneral.classList.remove('oculto');
  }

  return esValido;
}

// Si hay errores se detiene el envío; si no, se envía al servidor
formRegistro.addEventListener('submit', function (evento) {
  if (!validarFormulario()) {
    evento.preventDefault();
    return;
  }

  // Evita envíos duplicados por doble clic
  botonEnviar.disabled = true;
  botonEnviar.textContent = 'Registrando…';
});
