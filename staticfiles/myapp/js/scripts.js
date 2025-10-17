function toggleMenu() {
  document.getElementById("sidebar").classList.toggle("activo");
}


function actualizarHora() {
    const ahora = new Date();
    const opciones = { hour: '2-digit', minute: '2-digit', hour12: false };
    const horaElemento = document.getElementById('hora');
    if (horaElemento) {
      horaElemento.textContent = ahora.toLocaleTimeString('es-CO', opciones);
    }
  }
  
  document.addEventListener('DOMContentLoaded', () => {
    actualizarHora();
    setInterval(actualizarHora, 1000);
  });
  