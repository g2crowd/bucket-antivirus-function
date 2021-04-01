import os
import gnupg
import boto3

def initialize_gpg():
    ssm = boto3.client('ssm')
    params = ssm.get_parameter(Name = '/infra/production/s3av/gpg_private_key', WithDecryption = True)
    private_key = str(params["Parameter"]["Value"])

    gpg = gnupg.GPG(gnupghome='/tmp')
    gpg.import_keys(private_key)
    return gpg

def remove_gpg_from_path(file_path):
    """
    We expect the given path as argument to have the form: file-name.ext.gpg
    So we want to return: file-name.ext
    """
    return os.path.splitext(file_path)[0]

def decrypt_file(file_path, bucket_name, object_key):
    print(
        "Decrypting s3://%s\n"
        % (os.path.join(bucket_name, object_key))
    )
    gpg = initialize_gpg()

    with open(file_path, 'rb') as a_file:
        decrypted_file =  remove_gpg_from_path(file_path)
        status = gpg.decrypt_file(a_file, output=decrypted_file)

    if status.ok:
        s3 = boto3.client('s3')
        object_name = remove_gpg_from_path(object_key)
        s3.upload_file(decrypted_file, bucket_name, object_name)
        return status.ok, status.status
    else:
        message = "Track SFTP Decryption Failure \n>*File Name:* " + file_path + "\n>*Message:* " + status.status + "\n>*Error:* " + status.stderr
        return status.ok, message
