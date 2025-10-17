import random
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class AppUser(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Guardada encriptada
    verification_code = models.CharField(max_length=6, blank=True, null=True)

    def save(self, *args, **kwargs):
        """Hashea la contraseña antes de guardar el usuario."""
        if not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        """Verifica si la contraseña ingresada es correcta."""
        return check_password(raw_password, self.password)

    def generate_verification_code(self):
        """Genera un código de 6 dígitos y lo guarda en el modelo"""
        self.verification_code = str(random.randint(100000, 999999))
        self.save()