import re
import torch
import os
from django.shortcuts import render, redirect
from .models import AppUser
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from transformers import AlbertTokenizer, AlbertForSequenceClassification

def welcome(request):
    """
    Vista que renderiza una página de bienvenida.

    Esta función utiliza la función `render` de Django para generar una respuesta HTTP
    que muestra la plantilla 'welcome.html'.

    Parámetros:
    -----------
    request : django.http.HttpRequest
        Objeto que representa la solicitud HTTP. Contiene información como:
        - Método HTTP (GET, POST, etc.).
        - Parámetros de la URL (en `request.GET` o `request.POST`).
        - Cabeceras HTTP.
        - Cookies.
        - Archivos enviados (en `request.FILES`).
        - Sesión del usuario (en `request.session`).

    Retorna:
    --------
    django.http.HttpResponse
        Objeto que representa la respuesta HTTP. En este caso, devuelve una respuesta
        renderizada utilizando la plantilla 'welcome.html'.
        
    """
    return render(request, 'welcome.html')

def login_view(request):
    """
    Vista que gestiona el inicio de sesión de los usuarios.

    Esta función maneja la autenticación de usuarios verificando su correo y contraseña.
    Si las credenciales son correctas, genera un código de verificación y lo envía por
    correo electrónico para completar el inicio de sesión.

    Parámetros:
    -----------
    request : django.http.HttpRequest
        Objeto que representa la solicitud HTTP. Contiene datos como:
        - Método de la solicitud (GET, POST).
        - Datos del formulario de inicio de sesión (`email`, `password`).
        - Información de sesión del usuario.

    Retorna:
    --------
    django.http.HttpResponse
        - Si las credenciales son incorrectas, renderiza `login.html` con un mensaje de error.
        - Si el correo y la contraseña son correctos, guarda el email en la sesión y
          redirige a la vista de verificación de código (`verify_code`).
    """
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = AppUser.objects.get(email=email)
        except AppUser.DoesNotExist:
            return render(request, "login.html", {"error": "Correo no registrado."})

        # Verificar contraseña
        if not user.check_password(password):
            return render(request, "login.html", {"error": "Contraseña incorrecta."})

        # Generar y enviar código de verificación
        user.generate_verification_code()
        send_mail(
            "🔐 Tu código de verificación - NEX",
            f"""
            Hola {user.first_name}.

            Hemos recibido una solicitud para acceder a tu cuenta en NEX. 
            Para completar el inicio de sesión, ingresa el siguiente código de verificación:

            🔑 {user.verification_code}

            Este código es válido por 10 minutos. Si no solicitaste este acceso, puedes ignorar este mensaje.

            Si necesitas ayuda, contáctanos en cancerproyecto0@gmail.com.

            Saludos,  
            El equipo de NEX
            """,
            user.email,  
            [user.email],
            fail_silently=False,
        )

        # Guardar el email en la sesión temporalmente
        request.session["user_email"] = user.email  
        return redirect("verify_code")  

    return render(request, "login.html")

def register(request):
    """
     Vista que gestiona el registro de nuevos usuarios.

    Esta función maneja la creación de una nueva cuenta de usuario,
    validando la información ingresada y asegurando que el correo no
    esté registrado previamente.

    Parámetros:
    -----------
    request : django.http.HttpRequest
        Contiene la solicitud HTTP y los datos ingresados en el formulario:
        - `first_name`, `last_name`, `email`, `password`.

    Retorna:
    --------
    django.http.HttpResponse
        - Si hay errores en el formulario, renderiza `register.html` con mensajes de error.
        - Si el registro es exitoso, redirige a la página de inicio de sesión (`login`).
    """
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Verifica que todos los campos estén llenos
        if not first_name or not last_name or not email or not password:
            return render(request, 'register.html', {'error': 'Todos los campos son obligatorios'})

        # Verifica si el correo ya está registrado
        if AppUser.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error': 'El correo ya está en uso'})

        # Guarda el usuario con la contraseña encriptada
        user = AppUser(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=make_password(password)  # Encripta la contraseña
        )
        user.save()

        return redirect('login')  # Redirige a la página de inicio de sesión

    return render(request, 'register.html')

def verify_code(request):
    """
    Vista que verifica el código de autenticación enviado por correo.

    Esta función permite al usuario ingresar un código de verificación enviado a su correo
    tras iniciar sesión. Si el código es correcto, el usuario es autenticado y se le permite
    acceder a la aplicación.

    Parámetros:
    -----------
    request : django.http.HttpRequest
        Contiene la solicitud HTTP y los datos ingresados:
        - `request.session.get("user_email")`: Email guardado en sesión.
        - `request.POST.get("code")`: Código ingresado por el usuario.

    Retorna:
    --------
    django.http.HttpResponse
        - Si el código es correcto, redirige a la página principal (`home`).
        - Si el código es incorrecto, muestra `verify_code.html` con un mensaje de error.
        - Si no hay un email en sesión, redirige al login.
    """
    email = request.session.get("user_email")  # Verifica si el email está en la sesión

    if not email:
        return redirect("login")  # Si no ha pasado por login, redirigir

    if request.method == "POST":
        code = request.POST.get("code")

        try:
            user = AppUser.objects.get(email=email, verification_code=code)
            request.session["authenticated_user"] = user.email  # Marca al usuario como autenticado
            return redirect("home")  # Redirige a la página de inicio
        except AppUser.DoesNotExist:
            return render(request, "verify_code.html", {"error": "Código incorrecto."})

    return render(request, "verify_code.html")

def forgot_password(request):
    """
    Vista que permite solicitar un código de verificación para recuperar la contraseña.

    Esta función permite al usuario ingresar su correo electrónico para recibir un
    código de verificación. Si el correo está registrado, se genera y envía un código
    de recuperación a través del correo electrónico. Posteriormente, se guarda el correo
    en la sesión y se redirige al formulario para ingresar el código.

    Parámetros:
    -----------
    request : django.http.HttpRequest
        Contiene la solicitud HTTP y los datos ingresados:
        - `request.POST.get("email")`: Correo electrónico ingresado por el usuario.

    Retorna:
    --------
    django.http.HttpResponse
        - Si el correo está registrado, genera un código, lo envía y redirige a `verify_reset_code`.
        - Si el correo no está registrado, muestra `forgot_password.html` con un mensaje de error.
        - Si la solicitud no es POST, muestra el formulario `forgot_password.html`.
    """
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = AppUser.objects.get(email=email)
        except AppUser.DoesNotExist:
            return render(request, "forgot_password.html", {"error": "Correo no registrado."})

        # Generar y enviar código de verificación
        user.generate_verification_code()
        send_mail(
            "🔐 Recuperación de contraseña - NEX",
            f"""
            Hola {user.first_name},

            Has solicitado restablecer tu contraseña en NEX.  
            Usa el siguiente código para continuar con el proceso:

            🔑 {user.verification_code}

            Si no solicitaste esto, ignora este mensaje.

            Saludos,  
            El equipo de NEX
            """,
            user.email,
            [user.email],
            fail_silently=False,
        )

        request.session["reset_email"] = user.email  # Guardar email temporalmente
        return redirect("verify_reset_code")  # Redirigir a la verificación del código

    return render(request, "forgot_password.html")

def verify_reset_code(request):
    """
    Vista que verifica el código de recuperación ingresado por el usuario.

    Esta función permite verificar que el código de recuperación ingresado coincide con el
    enviado al correo electrónico del usuario. Si el código es correcto, se marca la sesión
    como verificada y se redirige al formulario de cambio de contraseña.

    Parámetros:
    -----------
    request : django.http.HttpRequest
        Contiene la solicitud HTTP y los datos ingresados:
        - `request.session.get("reset_email")`: Correo electrónico guardado temporalmente en sesión.
        - `request.POST.get("code")`: Código de verificación ingresado por el usuario.

    Retorna:
    --------
    django.http.HttpResponse
        - Si el código es correcto, redirige a la vista `reset_password`.
        - Si el código es incorrecto, muestra `verify_reset_code.html` con un mensaje de error.
        - Si no hay correo en la sesión, redirige a la vista `forgot_password`.
        - Si la solicitud no es POST, muestra el formulario `verify_reset_code.html`.
    """
    email = request.session.get("reset_email")

    if not email:
        return redirect("forgot_password")

    if request.method == "POST":
        code = request.POST.get("code")

        try:
            user = AppUser.objects.get(email=email, verification_code=code)
            request.session["verified_reset"] = True  # Marcar como verificado
            return redirect("reset_password")  # Redirigir al cambio de contraseña
        except AppUser.DoesNotExist:
            return render(request, "verify_reset_code.html", {"error": "Código incorrecto."})

    return render(request, "verify_reset_code.html")

def reset_password(request):
    """
    Vista que permite restablecer la contraseña después de verificar el código de recuperación.

    Esta función permite al usuario establecer una nueva contraseña, siempre y cuando se haya
    verificado previamente el código enviado a su correo. La nueva contraseña se guarda de
    forma segura y se eliminan los datos de recuperación de la sesión.

    Parámetros:
    -----------
    request : django.http.HttpRequest
        Contiene la solicitud HTTP y los datos ingresados:
        - `request.session.get("reset_email")`: Correo electrónico previamente verificado.
        - `request.session.get("verified_reset")`: Bandera que indica si el código fue validado.
        - `request.POST.get("password")`: Nueva contraseña ingresada por el usuario.

    Retorna:
    --------
    django.http.HttpResponse
        - Si la contraseña se actualiza correctamente, redirige a la vista `login`.
        - Si no hay datos de sesión válidos, redirige a `forgot_password`.
        - Si la solicitud no es POST, muestra el formulario `reset_password.html`.
    """
    email = request.session.get("reset_email")
    verified = request.session.get("verified_reset")

    if not email or not verified:
        return redirect("forgot_password")

    if request.method == "POST":
        new_password = request.POST.get("password")

        user = AppUser.objects.get(email=email)
        user.password = make_password(new_password)  # Guardar la nueva contraseña encriptada
        user.verification_code = None  # Eliminar el código usado
        user.save()

        # Limpiar sesión
        del request.session["reset_email"]
        del request.session["verified_reset"]

        return redirect("login")  # Redirigir al login con la nueva contraseña

    return render(request, "reset_password.html")

def logout_view(request):
    """
    Funcion que cierra la sesión del usuario.

    Esta función elimina la información de sesión del usuario y lo redirige
    a la página de inicio de sesión.

    Parámetros:
    -----------
    request : django.http.HttpRequest
        Contiene la solicitud HTTP del usuario.

    Retorna:
    --------
    django.http.HttpResponse
        - Redirige a la página de inicio de sesión (`login`).
    """
    request.session.flush()  # Elimina todas las variables de sesión
    return redirect("login")  # Redirige al login

def home(request):
    """
    Vista que muestra la página principal de la aplicación.

    Si el usuario no ha iniciado sesión correctamente, es redirigido a la
    página de inicio de sesión.

    Parámetros:
    -----------
    request : django.http.HttpRequest
        Contiene la sesión del usuario para verificar su autenticación.

    Retorna:
    --------
    django.http.HttpResponse
        - Si el usuario está autenticado, renderiza `home.html`.
        - Si no está autenticado, lo redirige a `login`.
    """
    if not request.session.get("authenticated_user"):
        return redirect("login")  # Redirigir al login si no está autenticado

    return render(request, "home.html")  # Mostrar página principal

def historia_clinica(request):
    """_summary_

    Args:
        request (_type_): _description_

    Returns:
        _type_: _description_
    """

    if not request.session.get("authenticated_user"):
        return redirect("login")
    return render(request,'historia clinica.html')



#esto es un comentario para ver si solo se permite un solo despliegue 
#y este es otro


# --- 1. CONFIGURACIÓN Y CARGA DEL MODELO (se ejecuta solo una vez) ---
# Define la ruta a la carpeta del modelo.
# **Asegúrate de que esta ruta sea correcta y que la carpeta del modelo esté allí.**
DIRECTORIO_MODELO = '/modelos/Modelos Entrenados/modelo_cancer_albert' # Cambiado a ALBERT por convención
MAX_LEN = 256

print("--- Cargando modelo y tokenizador para la web... ---")
# Mantener el uso de 'device' para compatibilidad con Azure
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Variable global para almacenar el modelo y tokenizador cargados.
modelo_cargado = None
tokenizer_cargado = None

try:
    if not os.path.exists(DIRECTORIO_MODELO):
        print(f"ERROR: La carpeta del modelo '{DIRECTORIO_MODELO}' no se encontró. Asegúrate de haberla descargado.")
    else:
        # 🚨 CAMBIO CLAVE: Reemplazamos BertForSequenceClassification por AlbertForSequenceClassification
        modelo_cargado = AlbertForSequenceClassification.from_pretrained(DIRECTORIO_MODELO)
        modelo_cargado.to(device)
        # 🚨 CAMBIO CLAVE: Reemplazamos BertTokenizer por AlbertTokenizer
        tokenizer_cargado = AlbertTokenizer.from_pretrained(DIRECTORIO_MODELO)
        print(f"Modelo y tokenizador cargados exitosamente para la vista web.")

except Exception as e:
    print(f"Ocurrió un error al cargar el modelo: {e}")
    modelo_cargado = None
    tokenizer_cargado = None

# ----------------------------------------------------------------------
# --- 2. FUNCIÓN DE PREDICCIÓN ---
# La lógica interna es compatible con ALBERT, por lo que se mantiene igual.
def predecir_con_modelo_entrenado(texto):
    if not modelo_cargado or not tokenizer_cargado:
        return "Error: Modelo no disponible. Revisa los logs del servidor."

    modelo_cargado.eval()
    with torch.no_grad():
        encoding = tokenizer_cargado.encode_plus(
            texto,
            add_special_tokens=True,
            max_length=MAX_LEN,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )

        input_ids = encoding['input_ids'].to(device)
        attention_mask = encoding['attention_mask'].to(device)
        outputs = modelo_cargado(input_ids=input_ids, attention_mask=attention_mask)
        _, prediction_id = torch.max(outputs.logits, dim=1)

    labels = {0: 'Control Sano (CO)', 1: 'Cáncer Colorrectal (CRC)'}
    return labels.get(prediction_id.item(), "Categoría Desconocida")

# ----------------------------------------------------------------------
# --- 3. LA VISTA DE DJANGO ---
# Esta parte se mantiene INTACTA para garantizar la conexión con tu plataforma.
def hacer_prediccion_view(request):
    """
    Maneja las peticiones GET y POST para la página de predicción.
    """
    # Asumo que 'render' está disponible en el scope (importado de django.shortcuts)
    from django.shortcuts import render 
    
    resultado_prediccion = None
    texto_ingresado = ""

    if request.method == 'POST':
        # Captura el texto del formulario
        texto_ingresado = request.POST.get('texto_clinico', '')
        if texto_ingresado:
            # Llama a la función de predicción
            resultado_prediccion = predecir_con_modelo_entrenado(texto_ingresado)

    # Prepara el contexto para la plantilla
    contexto = {
        'resultado_prediccion': resultado_prediccion,
        'texto_ingresado': texto_ingresado,
    }
    return render(request, 'hacer_prediccion.html', contexto)