import json
import subprocess

# Fetch the service description directly via gcloud
out = subprocess.check_output(
    "gcloud run services describe ssa-alumni-dev --project=ssa-alumni --region=asia-south1 --format=json",
    shell=True
)
data = json.loads(out)

template = data['spec']['template']
container = template['spec']['containers'][0]

image = container['image']
env_vars = []
secrets = []
for e in container.get('env', []):
    name = e['name']
    if 'value' in e:
        env_vars.append(f"{name}={e['value']}")
    elif 'valueSource' in e:
        secret = e['valueSource']['secretKeyRef']['secret']
        version = e['valueSource']['secretKeyRef'].get('version', 'latest')
        secrets.append(f"{name}={secret}:{version}")

# Add superuser env vars
env_vars.append("DJANGO_SUPERUSER_USERNAME=admin")
env_vars.append("DJANGO_SUPERUSER_EMAIL=admin@ssa.com")
env_vars.append("DJANGO_SUPERUSER_PASSWORD=admin123!")

env_str = ",".join(env_vars)
sec_str = ",".join(secrets)

vpc = template['metadata']['annotations'].get('run.googleapis.com/vpc-access-connector')
sa = template['spec'].get('serviceAccountName')
cloudsql = ""
if 'volumes' in template['spec']:
    for v in template['spec']['volumes']:
        if 'cloudSqlInstance' in v:
            instances = v['cloudSqlInstance']['instances']
            cloudsql = instances[0]

cmd = [
    "gcloud.cmd", "run", "jobs", "create", "ssa-alumni-migrate-temp",
    "--project=ssa-alumni",
    "--region=asia-south1",
    f"--image={image}",
    f"--set-env-vars={env_str}",
    f"--service-account={sa}",
    f"--command=bash",
    f"--args=-c,python manage.py migrate && python manage.py createsuperuser --noinput",
]

if secrets:
    cmd.append(f"--set-secrets={sec_str}")

if vpc:
    cmd.append(f"--vpc-connector={vpc}")

if cloudsql:
    cmd.append(f"--set-cloudsql-instances={cloudsql}")

print("Creating job...")
print(" ".join(cmd))
subprocess.run(cmd, check=True)

print("Executing job...")
exec_cmd = ["gcloud.cmd", "run", "jobs", "execute", "ssa-alumni-migrate-temp", "--project=ssa-alumni", "--region=asia-south1", "--wait"]
subprocess.run(exec_cmd, check=True)
