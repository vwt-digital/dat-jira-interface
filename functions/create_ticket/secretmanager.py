from google.cloud import secretmanager_v1
from google.cloud.secretmanager_v1 import AccessSecretVersionRequest


def get_secret(project_id, secret_id):
    """
    Returns a Secret Manager secret.
    """

    client = secretmanager_v1.SecretManagerServiceClient()

    secret_name = AccessSecretVersionRequest(client.secret_version_path(project_id, secret_id, 'latest'))

    response = client.access_secret_version(secret_name)
    payload = response.payload.data.decode('utf-8')

    return payload
