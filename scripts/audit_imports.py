"""
Import and Dependency Audit Script for Multimax AI Hub.
Scans all Python/TS/TSX files and cross-references against requirements/package.json.
"""
import ast
import re
import json
import sys
from pathlib import Path

BASE_DIR = Path(r"c:\Multimax AI Hub")

# Known standard library modules
STDLIB = {
    'os', 'sys', 're', 'json', 'math', 'time', 'datetime', 'uuid', 'typing',
    'pathlib', 'abc', 'enum', 'dataclasses', 'collections', 'functools',
    'itertools', 'logging', 'asyncio', 'inspect', 'fractions', 'decimal',
    'io', 'base64', 'hashlib', 'hmac', 'random', 'statistics', 'copy',
    'pprint', 'textwrap', 'string', 'contextlib', 'warnings', 'traceback',
    'argparse', 'configparser', 'importlib', 'pickle', 'shelve', 'sqlite3',
    'html', 'urllib', 'http', 'webbrowser', 'ssl', 'socket', 'email',
    'numbers', 'operator', 'atexit', 'weakref', 'types', 'threading',
    'multiprocessing', 'subprocess', 'signal', 'tempfile', 'shutil',
    'fileinput', 'filecmp', 'glob', 'fnmatch', 'linecache', 'compileall',
    'dis', 'token', 'tokenize', 'keyword', 'parser', 'ast', 'py_compile',
    'symtable', 'tabnanny', 'pyclbr', 'pycodecs', 'codecs', 'unicodedata',
    'stringprep', 'struct', 'difflib', 'heapq', 'bisect', 'array', 'weakref',
    'types', 'copyreg', 'reprlib', 'enum', 'statistics', 'zoneinfo',
}

def get_python_imports(filepath):
    """Extract all third-party imports from a Python file."""
    imports = set()
    try:
        content = filepath.read_text(encoding='utf-8')
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split('.')[0]
                    if top not in STDLIB and not top.startswith('app.'):
                        imports.add(top)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split('.')[0]
                    if top not in STDLIB and not top.startswith('app.'):
                        imports.add(top)
    except Exception as e:
        print(f"  [WARN] Could not parse {filepath}: {e}")
    return imports

def get_ts_imports(filepath):
    """Extract third-party package names from TS/TSX imports."""
    imports = set()
    try:
        content = filepath.read_text(encoding='utf-8')
        # Match: import ... from 'package'  or  import ... from "package"
        pattern = r'(?:import|from)\s+[\'"]([^\.\/][^\'"]*?)[\'"]'
        for match in re.finditer(pattern, content):
            pkg = match.group(1)
            # Get the top-level package name
            if pkg.startswith('@'):
                parts = pkg.split('/')
                top = f"{parts[0]}/{parts[1]}" if len(parts) > 1 else parts[0]
            else:
                top = pkg.split('/')[0]
            imports.add(top)
    except Exception as e:
        print(f"  [WARN] Could not parse {filepath}: {e}")
    return imports

def main():
    results = {
        'backend_requirements': [],
        'backend_installed_but_unused': [],
        'backend_missing': [],
        'frontend_dependencies': [],
        'frontend_installed_but_unused': [],
        'frontend_missing': [],
        'dead_imports': [],
    }

    # --- BACKEND ---
    print("=" * 60)
    print("BACKEND IMPORT ANALYSIS")
    print("=" * 60)

    # Read requirements.txt
    req_path = BASE_DIR / 'backend' / 'requirements.txt'
    req_packages = set()
    pkg_to_req = {}
    if req_path.exists():
        current_cat = None
        for line in req_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                if line.startswith('# =='):
                    current_cat = line.strip('#= ')
                continue
            # Extract package name (handle extras, version specs)
            pkg_name = re.split(r'[>=<!~\[\]]', line)[0].strip().lower()
            pkg_name_orig = re.split(r'[>=<!~\[\]]', line)[0].strip()
            req_packages.add(pkg_name)
            pkg_to_req[pkg_name] = pkg_name_orig

    # Map pip names to import names where they differ
    name_mapping = {
        'python-dotenv': 'dotenv',
        'python-jose': 'jose',
        'passlib': 'passlib',
        'argon2-cffi': 'argon2',
        'python-multipart': 'multipart',
        'pydantic-settings': 'pydantic_settings',
        'pydantic': 'pydantic',
        'sqlalchemy': 'sqlalchemy',
        'aiosqlite': 'aiosqlite',
        'httpx': 'httpx',
        'pytest': 'pytest',
        'pytest-asyncio': 'pytest_asyncio',
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'alembic': 'alembic',
    }

    # Collect all actual imports from backend Python files
    actual_imports = set()
    files_scanned = 0
    for pyfile in sorted((BASE_DIR / 'backend' / 'app').rglob('*.py')):
        files_scanned += 1
        imports = get_python_imports(pyfile)
        actual_imports.update(imports)

    # Also check backend root files
    for pyfile in sorted((BASE_DIR / 'backend').glob('*.py')):
        if pyfile.name not in ('setup.py',):
            files_scanned += 1
            imports = get_python_imports(pyfile)
            actual_imports.update(imports)

    print(f"\nFiles scanned: {files_scanned}")
    print(f"Actual imports from backend code: {sorted(actual_imports)}")

    # Map actual imports to requirements names
    import_to_req = {v: k for k, v in name_mapping.items()}
    
    used_reqs = set()
    for imp in actual_imports:
        req_name = import_to_req.get(imp, imp)
        if req_name in req_packages:
            used_reqs.add(req_name)
        else:
            results['backend_missing'].append(imp)

    unused_reqs = req_packages - used_reqs
    results['backend_installed_but_unused'] = sorted(unused_reqs)
    results['backend_requirements'] = sorted(req_packages)

    print(f"\nInstalled packages: {sorted(req_packages)}")
    print(f"Actually used: {sorted(used_reqs)}")
    if unused_reqs:
        print(f"POTENTIALLY UNUSED: {sorted(unused_reqs)}")
    if results['backend_missing']:
        print(f"MISSING from requirements: {results['backend_missing']}")

    # --- FRONTEND ---
    print("\n" + "=" * 60)
    print("FRONTEND IMPORT ANALYSIS")
    print("=" * 60)

    pkg_path = BASE_DIR / 'frontend' / 'package.json'
    if pkg_path.exists():
        pkg_data = json.loads(pkg_path.read_text())
        deps = list(pkg_data.get('dependencies', {}).keys()) + list(pkg_data.get('devDependencies', {}).keys())
        results['frontend_dependencies'] = deps
        print(f"\npackage.json dependencies: {sorted(deps)}")

        # Collect TS imports
        actual_ts_imports = set()
        ts_files_scanned = 0
        for ext in ('*.ts', '*.tsx'):
            for f in sorted((BASE_DIR / 'frontend' / 'src').rglob(ext)):
                ts_files_scanned += 1
                imports = get_ts_imports(f)
                actual_ts_imports.update(imports)

        print(f"Files scanned: {ts_files_scanned}")
        print(f"Actual imports from frontend code: {sorted(actual_ts_imports)}")
        
        # Filter local imports
        unused_frontend = []
        for dep in deps:
            # Check if this package name appears in imports
            dep_norm = dep.replace('@', '').replace('/', '-')
            found = False
            for imp in actual_ts_imports:
                if dep == imp or dep.startswith(imp + '/') or imp.startswith(dep):
                    found = True
                    break
            if not found:
                # Special handling for vite-built packages that don't need explicit import
                # e.g., tailwindcss, postcss, autoprefixer
                build_tools = {'tailwindcss', 'postcss', 'autoprefixer', 'typescript', 
                               'vite', '@vitejs/plugin-react', 'eslint', '@typescript-eslint/eslint-plugin',
                               '@typescript-eslint/parser', 'eslint-plugin-react-hooks', 
                               'eslint-plugin-react-refresh'}
                if dep not in build_tools:
                    unused_frontend.append(dep)
        
        if unused_frontend:
            print(f"POTENTIALLY UNUSED: {sorted(unused_frontend)}")
            results['frontend_installed_but_unused'] = sorted(unused_frontend)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    print(f"\nBackend packages in requirements.txt: {len(results['backend_requirements'])}")
    print(f"Backend packages potentially unused: {results['backend_installed_but_unused']}")
    print(f"Backend imports missing from requirements: {results['backend_missing']}")
    print(f"\nFrontend packages in package.json: {len(results['frontend_dependencies'])}")
    print(f"Frontend packages potentially unused: {results['frontend_installed_but_unused']}")
    
    # Save results
    output_path = BASE_DIR / 'scripts' / 'audit_results.json'
    output_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nResults saved to {output_path}")

if __name__ == '__main__':
    main()