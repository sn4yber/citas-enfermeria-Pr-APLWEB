from django.contrib.auth import get_user_model
from citas.infrastructure.adapters.django_repositories import UsuarioRepository

Usuario = get_user_model()


class RegisterUserUseCase:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

    def execute(self, first_name: str, email: str, password: str, rol: str, telefono: str = '') -> Usuario:
        existing = self.usuario_repository.get_by_email(email)
        if existing:
            raise ValueError(f"El correo {email} ya se encuentra registrado.")

        usuario = Usuario(
            username=email.split('@')[0],
            first_name=first_name,
            email=email,
            password=password,
            rol=rol,
            telefono=telefono
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