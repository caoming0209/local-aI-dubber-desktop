import sys

def check_import(module_name, attr=None):
    try:
        module = __import__(module_name)
        version = getattr(module, '__version__', 'unknown')
        if attr:
            getattr(module, attr)
            print(f'✓ {module_name}.{attr} - version: {version}')
        else:
            print(f'✓ {module_name} - version: {version}')
        return True
    except ImportError as e:
        print(f'✗ {module_name} - Error: {e}')
        return False
    except AttributeError as e:
        print(f'✗ {module_name}.{attr} - Error: {e}')
        return False

print('Checking key dependencies...')
print('=' * 50)

# Core dependencies
check_import('numpy')
check_import('torch')
check_import('torch', 'nn')
check_import('transformers')
check_import('diffusers')
check_import('fastapi')
check_import('uvicorn')
check_import('pydantic')
check_import('onnxruntime')
check_import('soundfile')
check_import('librosa')
check_import('whisper')

print('=' * 50)
print('All key dependencies checked!')
