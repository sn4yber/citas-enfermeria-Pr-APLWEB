from django.contrib.auth import get_user_model
from citas.infrastructure.adapters.django_repositories import UsuarioRepository

Usuario = get_user_model()


class RegisterUserUseCase:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

    def execute(
        self,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        rol: str,
        telefono: str = '',
        tipo_documento: str = 'CC',
        numero_documento: str = None,
        eps_id: int = None,
        regimen: str = None,
    ) -> Usuario:
        existing = self.usuario_repository.get_by_email(email)
        if existing:
            raise ValueError(f"El correo {email} ya se encuentra registrado.")

        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while Usuario.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        usuario = Usuario(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            rol=rol,
            telefono=telefono,
            tipo_documento=tipo_documento,
            numero_documento=numero_documento or None,
            eps_id=eps_id or None,
            regimen=regimen or None,
        )
        usuario.set_password(password)
        return self.usuario_repository.save(usuario)


class AuthenticateUserUseCase:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

    def execute(self, email: str, password: str) -> Usuario:
        usuario = self.usuario_repository.get_by_email(email)
        if not usuario:
            raise Exception("Usuario no encontrado")

        if not usuario.check_password(password):
            raise Exception("Contraseña incorrecta")

        return usuario


class GetUsersByRoleUseCase:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

    def execute(self, rol: str):
        return self.usuario_repository.get_by_rol(rol)


class GetAllUsersUseCase:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

    def execute(self):
        return self.usuario_repository.get_all()