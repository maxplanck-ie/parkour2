import ast
import glob
import os
from collections import namedtuple

from django.conf import settings

Import = namedtuple("Import", ["module", "name", "alias"])


def get_imports(path):
    with open(path) as fh:
        root = ast.parse(fh.read(), path)

    for node in ast.iter_child_nodes(root):
        if isinstance(node, ast.Import):
            module = []
        elif isinstance(node, ast.ImportFrom):
            module = node.module.split(".")
        else:
            continue

        for n in node.names:
            yield Import(module, n.name.split("."), n.asname)


def test_check_migrations_import_apps_instead_of_directly():
    """
    Check that Django migrations use the pattern:

    apps.get_model("appname", "ModelName")

    instead of

    from appname.models import ModelName
    """
    migrations = glob.glob(os.path.join(settings.BASE_DIR, "migrations", "*.py"))

    forbidden_imports = [{"app", "models"}]

    for migration in migrations:
        imported_libs = get_imports(migration)
        for imported_lib in imported_libs:
            assert not any(
                [
                    forbidden.issubset(set(imported_lib.module))
                    for forbidden in forbidden_imports
                ]
            )
