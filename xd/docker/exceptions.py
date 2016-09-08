class DockerException(Exception):
    """Basic exception for errors raised by XD-Docker"""


class IncompatibleRemoteAPI(DockerException):
    """Operation not supported by the Docker Remote API version"""


class PermissionDenied(DockerException):
    """Permission denied"""
